# PriceChekRider - USSD/SMS Retail System

A FastAPI-based USSD/SMS retail price comparison system for the Kenyan market, built for the Africa's Talking Hackathon.

## Features

- **USSD Interface**: Interactive menu system for customers to compare prices
- **SMS Integration**: Receive product requests via SMS and send price comparisons
- **Mock Price Scraper**: Fast mock price data for Kenyan retailers (Naivas, Quickmart, Tuskys, Carrefour)
- **Order Management**: Track customer orders and locations
- **Admin Endpoints**: View users and orders via REST API

## Project Structure

```
price_chek_rider/
├── requirements.txt
├── .env.example
├── app/
│   ├── __init__.py
│   ├── main.py            # FastAPI Entry Point
│   ├── config.py          # Pydantic Settings (Africa's Talking creds)
│   ├── database.py        # SQLAlchemy SQLite setup
│   ├── models.py          # User, Order Tables
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── ussd.py        # USSD State Machine logic
│   │   ├── sms.py         # SMS Callback logic
│   │   └── admin.py       # Basic endpoints to view data
│   └── services/
│       ├── __init__.py
│       ├── at_service.py  # Africa's Talking SDK Wrapper
│       └── scraper.py     # Mock Price Logic (Hackathon specific)
```

## Setup Instructions

### 1. Create Virtual Environment

```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

Copy `.env.example` to `.env` and fill in your Africa's Talking credentials:

```bash
# Windows PowerShell
Copy-Item .env.example .env

# Linux/Mac
cp .env.example .env
```

Edit `.env`:
```env
AT_USERNAME=your_username_here
AT_API_KEY=your_api_key_here
AT_ENV=sandbox
# Optional: SMS sender configuration
# Option 1: Numeric shortcode (for two-way SMS, users can reply)
#   Example: AT_SHORTCODE=384
# Option 2: Alphanumeric sender ID (for one-way branded SMS)
#   Example: AT_SENDER_ID=PriceChekRider
# If neither set, will use shortcode from incoming SMS or default from dashboard
AT_SHORTCODE=384
# AT_SENDER_ID=PriceChekRider  # Uncomment to use alphanumeric sender ID instead
```

### 4. Run the Application

**Option A: Using the startup script (recommended):**
```powershell
.\start_server.ps1
```

**Option B: Manual command:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Important:** Use `app.main:app` (not `main:app`) because `main.py` is inside the `app/` folder.

The API will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc

## API Endpoints

### USSD Endpoints
- **POST** `/ussd` - USSD callback with **JSON** body (for Swagger / testing)
- **POST** `/ussd/at` - USSD callback for **Africa's Talking** (form data in, plain text out). **Set this URL in the Africa's Talking dashboard** as your USSD callback. AT sends `sessionId`, `serviceCode`, `phoneNumber`, `text` as form fields; response must be plain text starting with CON or END (see `docs/africastalking_ussd_flask_example.py` for a minimal FastAPI reference).

### SMS Endpoint
- **POST** `/incoming-sms` - Handle incoming SMS from customers

### Admin Endpoints
- **GET** `/admin/users` - List all users
- **GET** `/admin/users/{user_id}` - Get specific user
- **GET** `/admin/orders` - List all orders
- **GET** `/admin/orders/{order_id}` - Get specific order

### Health Check
- **GET** `/` - API status check

## USSD Flow

1. **Level 0** (Initial): Main menu
   ```
   CON Karibu PriceChek!
   1. Compare Prices
   2. My Orders
   ```

2. **Level 1** (Option 1 selected): Location prompt
   ```
   CON Enter your specific location (e.g. Westlands):
   ```

3. **Level 2** (Location entered): Confirmation and SMS trigger
   ```
   END We have noted your location. We are sending you an SMS. 
   Please reply to the SMS with the products you want.
   ```

## SMS Flow

1. Customer receives SMS after setting location
2. Customer replies with products: `Sugar, Milk, Bread`
3. System responds with price comparison:
   ```
   Found best prices!
   Sugar: Naivas - KES 230/= (5 min)
   Milk: Carrefour - KES 118/= (12 min)
   Bread: Naivas - KES 55/= (5 min)
   
   Reply ORDER to buy lowest prices.
   ```

## Mock Products Available

The mock scraper includes prices for:
- Sugar
- Milk
- Bread
- Rice
- Cooking Oil
- Tea

## Database

The application uses SQLite (`pricechekrider.db`) which is created automatically on first run.

## Development

### Running Tests

```bash
# Install test dependencies (if needed)
pip install pytest pytest-asyncio

# Run tests
pytest
```

### Code Quality

```bash
# Format code
black app/

# Lint code
flake8 app/
```

## Testing (Sandbox & Simulator)

Test USSD and SMS **without a real phone** using Africa's Talking **sandbox** and **simulator**:

1. **Sandbox:** Sign up at https://account.africastalking.com/apps/sandbox (free).
2. **Simulator:** All testing happens at https://simulator.africastalking.com:1517/ — no handset needed.
3. **ngrok:** Expose your app so AT can call your callbacks; set USSD callback to `/ussd/at` and SMS callback to `/incoming-sms`.

**User flow (presentation):** [docs/USER_FLOW_PRESENTATION.md](docs/USER_FLOW_PRESENTATION.md) — end-to-end user journey, screens, and demo talking points.  
**Step-by-step:** [docs/SANDBOX_SIMULATOR.md](docs/SANDBOX_SIMULATOR.md) — sandbox setup, simulator usage, callback URLs.  
**ngrok only:** [docs/NGROK.md](docs/NGROK.md).

## Deployment

For production deployment:

1. Set `AT_ENV=production` in `.env`
2. Use a production WSGI server (e.g., Gunicorn with Uvicorn workers)
3. Set up proper database (PostgreSQL recommended for production)
4. Configure reverse proxy (Nginx)
5. Set up SSL/TLS certificates
6. Configure Africa's Talking webhook URLs to point to your server

## License

Built for Africa's Talking Hackathon 2026
