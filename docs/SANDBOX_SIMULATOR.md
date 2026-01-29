# Africa's Talking Sandbox & Simulator – PriceChekRider

This guide follows **Africa's Talking** official sandbox and simulator setup and maps it to our codebase so you can test USSD and SMS **without a real handset**.

**Official references:**
- [How do I get started on the Africa's Talking Sandbox?](https://help.africastalking.com/en/articles/1170660-how-do-i-get-started-on-the-africa-s-talking-sandbox)
- [What are the sandbox and the live environments?](https://help.africastalking.com/en/articles/2189460-what-are-the-sandbox-and-the-live-environments)
- Sandbox dashboard: **https://account.africastalking.com/apps/sandbox**
- Simulator (where you test): **https://simulator.africastalking.com:1517/**

---

## 1. Sandbox vs live

| | Sandbox | Live |
|---|--------|------|
| **Cost** | Free | Charged per transaction |
| **Where messages go** | **Simulator only** (browser) | Real handsets |
| **Dashboard** | Orange / sandbox | Green / live |
| **Use case** | Development and testing | Production |

**Important:** In sandbox, all USSD and SMS interactions happen in the **simulator** at https://simulator.africastalking.com:1517/ — **not** on your physical phone. You “register” numbers in the simulator and use them to trigger callbacks to your app.

---

## 2. One-time setup

### 2.1 Africa's Talking sandbox account

1. Sign up (free): **https://account.africastalking.com/apps/sandbox**
2. Log in and stay in the **sandbox** app (not live).

### 2.2 Create resources and set callbacks

Our app expects **two** callback URLs. You need a **public URL** (e.g. ngrok) before saving these.

| Resource | Where to create / configure | Callback URL to set (our codebase) |
|----------|-----------------------------|-------------------------------------|
| **USSD channel** | Sandbox → USSD → create channel → **Callback URL** | `https://YOUR-NGROK-HOST/ussd/at` |
| **SMS shortcode** | Sandbox → SMS → Inbox → **Callback URL** | `https://YOUR-NGROK-HOST/incoming-sms` |

**Dashboard links (sandbox):**
- Create USSD channel: https://account.africastalking.com/apps/sandbox/ussd/channel/create  
- SMS Inbox / callback: https://account.africastalking.com/apps/sandbox/sms/inbox/callback  

**Our endpoints:**

| Purpose | Method | Path | Request format | Response |
|--------|--------|------|-----------------|----------|
| USSD (Africa's Talking) | POST | `/ussd/at` | Form: `sessionId`, `serviceCode`, `phoneNumber`, `text` | Plain text starting with `CON` or `END` |
| USSD (Swagger / JSON) | POST | `/ussd` | JSON: `phoneNumber`, `sessionId`, `serviceCode`, `text` | JSON `{ "response": "CON/END ..." }` |
| Incoming SMS | POST | `/incoming-sms` | JSON/form: `from`, `to`, `text`, `date` | JSON `{ "status": "success", ... }` |

Use **`/ussd/at`** and **`/incoming-sms`** for the sandbox callback URLs. See [NGROK.md](NGROK.md) to get `YOUR-NGROK-HOST`.

---

## 3. Expose your app (ngrok)

Africa's Talking servers must reach your local app. Use ngrok to expose it:

1. **Terminal 1 – run the app**
   ```powershell
   cd c:\Users\USER\Desktop\PROJECTS\Africas-talking_hackathon
   .\venv\Scripts\Activate.ps1
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Terminal 2 – run ngrok**
   ```powershell
   ngrok http 8000
   ```
   Copy the **HTTPS** URL (e.g. `https://abc123.ngrok-free.app`).

3. In the **sandbox** dashboard, set:
   - **USSD callback:** `https://YOUR-NGROK-HOST/ussd/at`
   - **SMS (Incoming) callback:** `https://YOUR-NGROK-HOST/incoming-sms`

Details: [NGROK.md](NGROK.md).

---

## 4. Testing in the simulator

### 4.1 Open the simulator

- Go to: **https://simulator.africastalking.com:1517/**
- Use the same browser session (or multiple sessions if you want multiple “numbers”).

### 4.2 Test USSD

1. In the simulator, choose **USSD**.
2. Enter your **USSD service code** (e.g. the shortcode you created in sandbox, like `*384*12345#`).
3. Click to start the session.  
   Africa's Talking will **POST** to your USSD callback (`/ussd/at`) with form fields: `sessionId`, `serviceCode`, `phoneNumber`, `text`.
4. Our app responds with plain text (`CON ...` or `END ...`). The simulator shows the same menu as a real phone would:
   - First screen: `Welcome to PriceChekRider! 1. Compare Prices 2. Order Delivery 3. Help 4. Exit`
   - Then follow the flow (e.g. `1` → city code → `1*NAI` → END + SMS).

5. Watch:
   - **Simulator:** USSD screens.
   - **Uvicorn terminal:** Logs for each request.
   - **ngrok terminal:** Incoming POSTs to `/ussd/at`.

### 4.3 Test SMS

1. In the simulator, register / use a number for **SMS** (simulator acts as the “phone”).
2. Send an SMS **to** your sandbox shortcode (e.g. “NAI-Kileleshwa” or “Sugar, Milk”).  
   Africa's Talking will **POST** to your SMS callback (`/incoming-sms`) with `from`, `to`, `text`, `date`.
3. Our app processes the message and (if AT credentials are valid) sends a reply via the Africa's Talking API; the simulator shows incoming SMS.
4. Check:
   - **Dashboard:** Sandbox SMS Inbox / session logs.
   - **Uvicorn logs:** Incoming request and our reply.
   - **ngrok:** POSTs to `/incoming-sms`.

### 4.4 Multiple “users”

- Open **https://simulator.africastalking.com:1517/** in different browsers (or incognito) and register different numbers.
- Each number can run USSD and SMS flows independently against the same callback URLs.

---

## 5. How our codebase matches the sandbox

| Africa's Talking (sandbox) | Our code |
|----------------------------|----------|
| USSD: POST form `sessionId`, `serviceCode`, `phoneNumber`, `text` | `app/routers/ussd.py` → `POST /ussd/at` (Form), `_ussd_logic()` returns plain text `CON`/`END` |
| USSD response: plain text starting with CON or END | `PlainTextResponse(content=response_text)` in `handle_ussd_at()` |
| SMS: POST body with `from`, `to`, `text`, `date` | `app/routers/sms.py` → `POST /incoming-sms`, `SMSRequest` (alias `from_` for `from`) |
| Simulator only (no handset) in sandbox | Use simulator.africastalking.com:1517 for all tests; no real phone needed |
| Callback must be publicly reachable | ngrok (or similar) exposing `/ussd/at` and `/incoming-sms` |

---

## 6. Checklist

- [ ] Sandbox account created at https://account.africastalking.com/apps/sandbox  
- [ ] USSD channel created; callback URL set to `https://YOUR-NGROK-HOST/ussd/at`  
- [ ] SMS shortcode / Inbox callback set to `https://YOUR-NGROK-HOST/incoming-sms`  
- [ ] App running (`uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`)  
- [ ] ngrok running (`ngrok http 8000`) and URLs updated in dashboard  
- [ ] `.env` has valid sandbox `AT_USERNAME` and `AT_API_KEY` (for SMS send)  
- [ ] Simulator opened at https://simulator.africastalking.com:1517/  
- [ ] USSD tested in simulator (menu → city code → END + SMS)  
- [ ] SMS tested in simulator (send message → receive reply in simulator / inbox)  

---

## 7. Troubleshooting

| Issue | What to check |
|-------|----------------|
| Simulator shows no response / timeout | Callback URL must be **HTTPS** and reachable (ngrok running, URL correct in dashboard). |
| USSD returns error | Response must be **plain text** starting with `CON` or `END`; we use `/ussd/at` (not `/ussd` JSON) for AT. |
| SMS not received in simulator | Verify sandbox credentials in `.env`; check dashboard Inbox and callback logs. |
| “Invalid request” | For USSD, AT sends **form** data; our `/ussd/at` expects Form, not JSON. |

---

## 8. References

- [Get started on the Sandbox](https://help.africastalking.com/en/articles/1170660-how-do-i-get-started-on-the-africa-s-talking-sandbox)  
- [Sandbox vs live](https://help.africastalking.com/en/articles/2189460-what-are-the-sandbox-and-the-live-environments)  
- [Configure callback URL](https://help.africastalking.com/en/articles/2206161-how-do-i-configure-my-callback-url)  
- Simulator: **https://simulator.africastalking.com:1517/**  
- Sandbox dashboard: **https://account.africastalking.com/apps/sandbox**  
- Project ngrok steps: [NGROK.md](NGROK.md)  
- Flask-style USSD example: [africastalking_ussd_flask_example.py](africastalking_ussd_flask_example.py)  
