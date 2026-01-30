"""
USSD router handling Africa's Talking USSD callbacks.
Implements a state machine for USSD menu navigation.

Africa's Talking sends POST with form fields: sessionId, serviceCode, phoneNumber, text
and expects a plain text response starting with CON or END.

Sandbox/simulator testing: see docs/SANDBOX_SIMULATOR.md. Use /ussd/at for AT callback URL.
"""
import logging

from fastapi import APIRouter, Depends, Form
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.services.at_service import at_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ussd", tags=["USSD"])


class USSDRequest(BaseModel):
    """Request body sent by Africa's Talking on each USSD session step (JSON for Swagger)."""

    phoneNumber: str = Field(..., description="Customer phone number (e.g. +254712345678)")
    sessionId: str = Field(..., description="Unique session ID for this USSD session")
    serviceCode: str = Field(..., description="Shortcode (e.g. *384*12345#)")
    text: str = Field(
        default="",
        description="User input so far. Empty on first screen; then e.g. `1`, `1*NAI`",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"phoneNumber": "+254712345678", "sessionId": "abc-123", "serviceCode": "*384*12345#", "text": ""},
                {"phoneNumber": "+254712345678", "sessionId": "abc-123", "serviceCode": "*384*12345#", "text": "1*NAI"},
            ]
        }
    }


class USSDResponse(BaseModel):
    """Response body for JSON API. Africa's Talking expects plain text (CON/END) not JSON."""

    response: str = Field(..., description="CON <menu> or END <message>")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"response": "CON Welcome to PriceChekRider!\n1. Compare Prices\n2. Order Delivery\n3. Help\n4. Exit"},
                {"response": "END We have noted your city. We are sending you an SMS."},
            ]
        }
    }


def _ussd_logic(phone_number: str, text: str, db: Session) -> str:
    """Shared USSD state machine. Returns plain text response (CON or END)."""
    text = (text or "").strip()
    parts = text.split("*") if text else []
    level = len(parts)
    logger.info(f"USSD from {phone_number}, text: '{text}'")
    try:
        if level == 0:
            return (
                "CON Welcome to PriceChekRider!\n"
                "1. Compare Prices\n"
                "2. Order Delivery\n"
                "3. Help\n"
                "4. Exit"
            )
        if level == 1 and parts[0] == "1":
            return "CON Enter your city code (e.g., NAI for Nairobi):"
        if level == 2 and parts[0] == "1":
            city_code = parts[1].strip().upper()
            user = db.query(User).filter(User.phone_number == phone_number).first()
            if not user:
                user = User(phone_number=phone_number, city_code=city_code, location=city_code)
                db.add(user)
            else:
                user.city_code = city_code
                user.location = city_code
            user.current_session_data = "sms_step:need_area"
            db.commit()
            sms_message = (
                "Welcome to PriceChekRider! Reply with:\n"
                "LOCATION-FORMAT: CityCode-Area\n"
                "Example: NAI-Kileleshwa or NAI-Kasarani"
            )
            try:
                # Pass shortcode so SMS is from your shortcode (required for two-way)
                from app.config import settings
                sender = settings.sms_sender
                at_service.send_sms(phone_number, sms_message, sender_id=sender)
                logger.info(f"SMS sent to {phone_number} after city code (from {sender})")
            except Exception as e:
                logger.error(f"Failed to send SMS to {phone_number}: {e}", exc_info=True)
            return (
                "END We have noted your city. "
                "We are sending you an SMS. Please reply with your location (e.g. NAI-Kileleshwa)."
            )
        if level == 1 and parts[0] == "4":
            return "END Thank you for using PriceChekRider. Goodbye!"
        if level == 1 and parts[0] == "3":
            return (
                "END PriceChekRider helps you find the cheapest prices nearby and get delivery. "
                "Choose 1 to compare prices or 2 for delivery. Dial again to start."
            )
        if level == 1 and parts[0] == "2":
            user = db.query(User).filter(User.phone_number == phone_number).first()
            if not user:
                return "END You have no orders yet. Use option 1 to compare prices first."
            from app.models import Order
            orders = db.query(Order).filter(Order.user_id == user.id).limit(5).all()
            if not orders:
                return "END You have no orders yet."
            order_list = "\n".join([
                f"Order #{o.id}: {o.items[:30]}... - KES {o.total_price:.2f} ({o.status})"
                for o in orders
            ])
            return f"END Your recent orders:\n{order_list}"
        return "END Invalid option. Please try again."
    except Exception as e:
        logger.error(f"Error handling USSD request: {e}", exc_info=True)
        return "END An error occurred. Please try again later."


# --- JSON (Swagger / testing) ---

@router.post(
    "",
    response_model=USSDResponse,
    summary="USSD callback (JSON)",
    description="Same logic as `/ussd/at`. Use this with JSON body for Swagger. **Africa's Talking** should use `/ussd/at` (form → plain text).",
)
async def handle_ussd_json(request: USSDRequest, db: Session = Depends(get_db)):
    """JSON body: for Swagger and API tests."""
    response_text = _ussd_logic(request.phoneNumber, request.text or "", db)
    return USSDResponse(response=response_text)


# --- Africa's Talking: form data in, plain text out (see docs/africastalking_ussd_flask_example.py) ---

@router.post(
    "/at",
    summary="USSD callback (Africa's Talking form)",
    description=(
        "**Set this URL in Africa's Talking dashboard** as your USSD callback. "
        "AT sends POST with form fields: `sessionId`, `serviceCode`, `phoneNumber`, `text`. "
        "Response is plain text starting with CON or END (not JSON)."
    ),
    response_class=PlainTextResponse,
)
async def handle_ussd_at(
    db: Session = Depends(get_db),
    sessionId: str = Form(...),
    serviceCode: str = Form(...),
    phoneNumber: str = Form(...),
    text: str = Form(""),
    input: str = Form(""),  # Africa's Talking may send user input as 'input' field
):
    """
    Form body: sessionId, serviceCode, phoneNumber, text/input.
    Africa's Talking may send user input in either 'text' or 'input' field.
    """
    # Use 'input' if present and non-empty, otherwise fall back to 'text'
    user_input = (input or text or "").strip()
    logger.info(
        f"POST /ussd/at: phone={phoneNumber[:10]}..., "
        f"session={sessionId[:20]}..., serviceCode={serviceCode}, "
        f"user_input='{user_input}' (from input='{input}', text='{text}')"
    )
    response_text = _ussd_logic(phoneNumber, user_input, db)
    return PlainTextResponse(content=response_text)
