"""
Africa's Talking USSD callback - minimal FastAPI example (reference only).
Same contract as our main app: form params in, plain text out.

Africa's Talking sends POST with:
  sessionId, serviceCode, phoneNumber, text (form fields)

Response must be plain text starting with CON (continue) or END (terminate).
"""
from fastapi import FastAPI, Form
from fastapi.responses import PlainTextResponse

app = FastAPI()


@app.post("/ussd", response_class=PlainTextResponse)
def ussd(
    sessionId: str | None = Form(None),
    serviceCode: str | None = Form(None),
    phoneNumber: str | None = Form(None),
    text: str = Form(""),
):
    # Map form names (AT sends camelCase)
    session_id = sessionId
    phone_number = phoneNumber
    user_text = text.strip() if text else ""

    if user_text == "":
        response = "CON What would you want to check \n"
        response += "1. My Account \n"
        response += "2. My phone number"
    elif user_text == "1":
        response = "CON Choose account information you want to view \n"
        response += "1. Account number"
    elif user_text == "2":
        response = "END Your phone number is " + (phone_number or "")
    elif user_text == "1*1":
        accountNumber = "ACC1001"
        response = "END Your account number is " + accountNumber
    else:
        response = "END Invalid choice"

    return response


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
