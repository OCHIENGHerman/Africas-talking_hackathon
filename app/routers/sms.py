"""
SMS router handling incoming SMS from customers.
Processes product requests and sends price comparisons.

Sandbox/simulator testing: see docs/SANDBOX_SIMULATOR.md. Use /incoming-sms for AT callback URL.
"""
import logging
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User, Order
from app.services.scraper import MockScraper
from app.services.at_service import at_service
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/incoming-sms", tags=["SMS"])


class SMSRequest(BaseModel):
    """Request body sent by Africa's Talking when a customer sends an SMS."""

    from_: str = Field(..., alias="from", description="Sender phone number")
    to: str = Field(default="", description="Shortcode or destination number")
    text: str = Field(default="", description="Message body (e.g. Sugar, Milk or ORDER)")
    date: str = Field(default="", description="SMS timestamp")
    linkId: str | None = Field(default=None, description="Link ID if present")

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "examples": [
                {"from": "+254712345678", "to": "384", "text": "Sugar, Milk", "date": "2026-01-29 12:00:00"},
                {"from": "+254712345678", "to": "384", "text": "ORDER", "date": "2026-01-29 12:00:00"},
            ]
        },
    }


class SMSSuccessResponse(BaseModel):
    """Success response after processing incoming SMS."""

    status: str = Field(..., description="success")
    message: str = Field(..., description="SMS sent successfully")


def _parse_sms_step(session_data: str | None) -> str:
    """Get current SMS step from session. Values: need_area | need_search_type | need_products | (prices:...)"""
    if not session_data:
        return "need_area"
    if session_data.startswith("prices:"):
        return "have_results"
    if session_data in ("need_area", "need_search_type", "need_products"):
        return session_data
    if session_data.startswith("sms_step:"):
        return session_data.replace("sms_step:", "")
    return "need_products"


@router.post(
    "",
    response_model=SMSSuccessResponse,
    summary="Incoming SMS callback",
    description="**Africa's Talking** calls this when a customer sends an SMS. If **text** is product names (e.g. `Sugar, Milk`), we reply with best prices via SMS. If **text** is `ORDER`, we confirm the order and send SMS.",
    response_description="Confirmation that the reply SMS was sent",
    responses={500: {"description": "Failed to send SMS or process request"}},
)
async def handle_incoming_sms(request: SMSRequest, db: Session = Depends(get_db)):
    try:
        phone_number = request.from_
        message_text = request.text.strip()
        msg_upper = message_text.upper()
        
        logger.info(f"Incoming SMS from {phone_number}: {message_text}")
        
        user = db.query(User).filter(User.phone_number == phone_number).first()
        if not user:
            user = User(phone_number=phone_number)
            db.add(user)
            db.commit()
        
        step = _parse_sms_step(user.current_session_data)
        
        # --- ORDER (spec: Order confirmed! Estimated delivery: 45 mins. Rider John (072X). Track at [URL]. Reply CANCEL within 5 mins)
        if msg_upper == "ORDER":
            last_prices = None
            if user.current_session_data and user.current_session_data.startswith("prices:"):
                try:
                    last_prices = json.loads(user.current_session_data.replace("prices:", ""))
                except Exception:
                    pass
            
            if last_prices:
                items_list = []
                total = 0.0
                for product, prices in last_prices.items():
                    sorted_prices = sorted(prices, key=lambda x: x["price"])
                    best = sorted_prices[0]
                    items_list.append({
                        "product": product,
                        "shop": best.get("shop"),
                        "store_location": best.get("store_location", best.get("shop", "")),
                        "price": best["price"],
                        "rider_time": best.get("rider_time", ""),
                    })
                    total += best["price"]
                
                delivery_fee = getattr(MockScraper, "DELIVERY_FEE_KES", 150)
                order = Order(
                    user_id=user.id,
                    items=json.dumps(items_list),
                    total_price=total + delivery_fee,
                    status="PENDING",
                )
                db.add(order)
                db.commit()
                # Spec delivery phase: rider name, track URL, CANCEL within 5 mins
                response_message = (
                    f"Order confirmed! Estimated delivery: 45 mins.\n"
                    f"Rider John (0722 XXX XXX) will contact you.\n"
                    f"Track at: https://pricechekrider.co.ke/track/{order.id}\n\n"
                    f"Reply CANCEL within 5 mins to cancel."
                )
                user.current_session_data = "need_products"  # Allow new search
                db.commit()
            else:
                response_message = (
                    "No recent price comparison found. "
                    "Send product names (e.g. Sugar 2kg, Milk) then reply ORDER."
                )
        
        # --- CANCEL (spec: Reply CANCEL within 5 mins to cancel)
        elif msg_upper == "CANCEL":
            # Optional: cancel latest PENDING order; for hackathon we just acknowledge
            user.current_session_data = "need_products"
            db.commit()
            response_message = "Order cancelled. Reply with products to search again or dial *123# to start over."
        
        # --- NEW (spec: search again)
        elif msg_upper == "NEW":
            user.current_session_data = "need_products"
            db.commit()
            response_message = (
                "List products (comma separated):\n"
                "Example: Sugar 2kg, Rice 1kg, Cooking Oil"
            )
        
        # --- Step: need_area — expect location e.g. NAI-Kileleshwa (spec)
        elif step == "need_area":
            if re.match(r"^[A-Z]{2,5}-[A-Za-z]+$", message_text.strip(), re.IGNORECASE):
                user.location = message_text.strip()
                user.current_session_data = "need_search_type"
                db.commit()
                response_message = (
                    "Search for:\n"
                    "1. Single product\n"
                    "2. Multiple products (batch)\n"
                    "Reply 1 or 2"
                )
            else:
                response_message = (
                    "Reply with location in format: CityCode-Area\n"
                    "Example: NAI-Kileleshwa or NAI-Kasarani"
                )
        
        # --- Step: need_search_type — expect 1 or 2 (spec)
        elif step == "need_search_type":
            if message_text.strip() in ("1", "2"):
                user.current_session_data = "need_products"
                db.commit()
                response_message = (
                    "List products (comma separated):\n"
                    "Example: Sugar 2kg, Rice 1kg, Cooking Oil"
                )
            else:
                response_message = "Reply 1 for single product or 2 for multiple products."
        
        # --- Step: need_products or have_results but not ORDER/NEW — treat as product list
        else:
            products = [p.strip() for p in re.split(r"[,;\n]+", message_text) if p.strip()]
            if not products:
                response_message = (
                    "List products (comma separated):\n"
                    "Example: Sugar 2kg, Rice 1kg, Milk 500ml"
                )
            else:
                all_prices = {}
                for product in products:
                    prices = MockScraper.get_prices(product, user.location)
                    if prices:
                        all_prices[product] = prices
                if not all_prices:
                    response_message = "Sorry, we couldn't find prices for those products. Try different names or reply NEW."
                else:
                    # Spec results format: PriceChekRider Results, *Product*: Cheapest: KES X @ Store Area, Average: KES Y. Total Cheapest, Delivery KES 150, Reply ORDER or NEW
                    delivery_fee = getattr(MockScraper, "DELIVERY_FEE_KES", 150)
                    total_cheapest = 0.0
                    lines = ["PriceChekRider Results:"]
                    for product, prices in all_prices.items():
                        sorted_prices = sorted(prices, key=lambda x: x["price"])
                        best = sorted_prices[0]
                        avg = sum(p["price"] for p in prices) / len(prices)
                        store_loc = best.get("store_location", best["shop"])
                        total_cheapest += best["price"]
                        lines.append(f"*{product.title()}*:")
                        lines.append(f"- Cheapest: KES {best['price']} @ {store_loc}")
                        lines.append(f"- Average: KES {int(avg)}")
                        lines.append("")
                    lines.append(f"Total Cheapest: KES {int(total_cheapest)}")
                    lines.append(f"Delivery available for KES {delivery_fee}")
                    lines.append("")
                    lines.append("Reply ORDER to confirm delivery or NEW to search again")
                    response_message = "\n".join(lines)
                    user.current_session_data = f"prices:{json.dumps(all_prices)}"
                    db.commit()
        
        # Send response SMS (return 200 even if send fails so AT does not retry; log failure)
        try:
            at_service.send_sms(phone_number, response_message)
            logger.info(f"Response SMS sent to {phone_number}")
            return SMSSuccessResponse(status="success", message="SMS sent successfully")
        except Exception as e:
            logger.error(f"Failed to send response SMS: {e}")
            # Still return 200 so Africa's Talking does not retry; include note in response
            return SMSSuccessResponse(
                status="success",
                message="Request processed; SMS could not be sent (check AT credentials).",
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling incoming SMS: {e}", exc_info=True)
        detail = str(e) or type(e).__name__
        raise HTTPException(status_code=500, detail=f"Error processing SMS: {detail}")
