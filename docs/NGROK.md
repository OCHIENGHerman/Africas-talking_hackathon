# Using ngrok with PriceChekRider

ngrok exposes your local server so **Africa's Talking** can reach your USSD and SMS callback URLs. Use it together with the **sandbox and simulator** for testing without a real handset.

**Full flow (sandbox + simulator + callbacks):** see **[SANDBOX_SIMULATOR.md](SANDBOX_SIMULATOR.md)**.

---

## 1. Install ngrok

- **Windows (winget):** `winget install ngrok.ngrok`
- **Windows (choco):** `choco install ngrok`
- **Download:** https://ngrok.com/download  
- **Sign up** at https://ngrok.com (free tier is enough) and get your auth token from the dashboard.

```powershell
# After install, authenticate (one-time)
ngrok config add-authtoken YOUR_AUTH_TOKEN
```

## 2. Start your app and ngrok

**Terminal 1 – run the API:**
```powershell
cd c:\Users\USER\Desktop\PROJECTS\Africas-talking_hackathon
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 – run ngrok:**
```powershell
ngrok http 8000
```

You’ll see something like:
```
Forwarding   https://abc123def456.ngrok-free.app -> http://localhost:8000
```

Copy the **HTTPS** URL (e.g. `https://abc123def456.ngrok-free.app`). You’ll use it as the base for your callbacks.

## 3. Set Africa's Talking callback URLs

In the **Africa's Talking** dashboard:

1. Go to **USSD** → **Callback URL** (or your USSD product settings).
2. Set:
   ```
   https://YOUR-NGROK-URL/ussd/at
   ```
   Example: `https://abc123def456.ngrok-free.app/ussd/at`

3. Go to **SMS** → **Callback URL** (Incoming Messages).
4. Set:
   ```
   https://YOUR-NGROK-URL/incoming-sms
   ```
   Example: `https://abc123def456.ngrok-free.app/incoming-sms`

Use your **actual** ngrok HTTPS host each time you start ngrok (it changes on the free tier unless you use a reserved domain).

## 4. Test

- **Sandbox:** Use the **simulator** at https://simulator.africastalking.com:1517/ (not a real phone). See [SANDBOX_SIMULATOR.md](SANDBOX_SIMULATOR.md).
- **USSD:** In the simulator, run your USSD code; AT POSTs to `/ussd/at`.
- **SMS:** In the simulator, send SMS to your shortcode; AT POSTs to `/incoming-sms`.

Check the ngrok terminal for incoming requests and your uvicorn terminal for logs.

## 5. Quick reference

| What              | URL (replace `YOUR-NGROK-URL` with your ngrok host) |
|-------------------|------------------------------------------------------|
| USSD callback     | `https://YOUR-NGROK-URL/ussd/at`                    |
| SMS callback      | `https://YOUR-NGROK-URL/incoming-sms`               |
| API docs (browser)| `https://YOUR-NGROK-URL/docs`                       |
| Health check      | `https://YOUR-NGROK-URL/health`                     |

## Notes

- **Free ngrok:** The forwarding URL changes each time you run `ngrok http 8000`. Update the callback URLs in the AT dashboard when it changes.
- **Paid ngrok:** You can use a fixed subdomain so you don’t have to update AT every time.
- **Firewall:** Allow port 8000 for uvicorn; ngrok handles HTTPS and tunnels to localhost.
- Keep both the **uvicorn** and **ngrok** terminals running while testing.
