# Testing Guide for PriceChekRider

## Prerequisites

1. **Virtual environment activated**
   ```bash
   .\venv\Scripts\Activate.ps1  # Windows PowerShell
   ```

2. **Environment variables configured**
   - Check `.env` file has valid Africa's Talking credentials:
     ```
     AT_USERNAME=your_username
     AT_API_KEY=your_api_key
     AT_ENV=sandbox
     ```

3. **Dependencies installed**
   ```bash
   pip install -r requirements.txt
   ```

## Starting the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **Swagger UI**: http://localhost:8000/docs
- **API Root**: http://localhost:8000/
- **Health Check**: http://localhost:8000/health

## Testing Endpoints

### 1. Health Check
```bash
curl http://localhost:8000/health
```
Expected: `{"status": "PriceChekRider API is live"}`

### 2. USSD Endpoint

**Test Level 0 (Initial Menu):**
```bash
curl -X POST http://localhost:8000/ussd \
  -H "Content-Type: application/json" \
  -d '{
    "phoneNumber": "+254712345678",
    "sessionId": "test-session-123",
    "serviceCode": "*384*12345#",
    "text": ""
  }'
```
Expected: `{"response": "CON Karibu PriceChek!\n1. Compare Prices\n2. My Orders"}`

**Test Level 1 (Select Compare Prices):**
```bash
curl -X POST http://localhost:8000/ussd \
  -H "Content-Type: application/json" \
  -d '{
    "phoneNumber": "+254712345678",
    "sessionId": "test-session-123",
    "serviceCode": "*384*12345#",
    "text": "1"
  }'
```
Expected: `{"response": "CON Enter your specific location (e.g. Westlands):"}`

**Test Level 2 (Enter Location):**
```bash
curl -X POST http://localhost:8000/ussd \
  -H "Content-Type: application/json" \
  -d '{
    "phoneNumber": "+254712345678",
    "sessionId": "test-session-123",
    "serviceCode": "*384*12345#",
    "text": "1*Westlands"
  }'
```
Expected: `{"response": "END We have noted your location. We are sending you an SMS..."}`

**Note**: This will trigger an SMS (if AT credentials are valid) or log a warning if not.

### 3. SMS Endpoint

**Test Product Price Comparison:**
```bash
curl -X POST http://localhost:8000/incoming-sms \
  -H "Content-Type: application/json" \
  -d '{
    "from": "+254712345678",
    "to": "384",
    "text": "Sugar, Milk",
    "date": "2026-01-29 12:00:00"
  }'
```
Expected: `{"status": "success", "message": "SMS sent successfully"}`

**Test ORDER Command:**
```bash
curl -X POST http://localhost:8000/incoming-sms \
  -H "Content-Type: application/json" \
  -d '{
    "from": "+254712345678",
    "to": "384",
    "text": "ORDER",
    "date": "2026-01-29 12:00:00"
  }'
```
Expected: Order created in database and confirmation SMS sent.

### 4. Admin Endpoints

**List Users:**
```bash
curl http://localhost:8000/admin/users
```

**List Orders:**
```bash
curl http://localhost:8000/admin/orders
```

**Get Specific User:**
```bash
curl http://localhost:8000/admin/users/1
```

**Get Specific Order:**
```bash
curl http://localhost:8000/admin/orders/1
```

## Testing with Swagger UI

1. Open http://localhost:8000/docs
2. Click on any endpoint to expand it
3. Click "Try it out"
4. Fill in the request body (examples are provided)
5. Click "Execute"
6. View the response

## Common Issues

### 1. AT Service Not Initialized
**Symptom**: Warnings in logs about AT Service initialization
**Solution**: Check `.env` file has correct credentials. The app will continue with mock SMS (logged only).

### 2. Database Errors
**Symptom**: SQLite errors
**Solution**: Delete `pricechekrider.db` and restart server (tables will be recreated).

### 3. Port Already in Use
**Symptom**: `Address already in use`
**Solution**: Change port: `uvicorn app.main:app --reload --port 8001`

### 4. Import Errors
**Symptom**: `ModuleNotFoundError`
**Solution**: Ensure virtual environment is activated and dependencies installed.

## Testing Flow

1. **USSD Flow**:
   - Call USSD with `text=""` → Get menu
   - Call with `text="1"` → Get location prompt
   - Call with `text="1*Westlands"` → Location saved, SMS sent

2. **SMS Flow**:
   - Send SMS with products: `Sugar, Milk`
   - Receive price comparison via SMS
   - Send SMS: `ORDER`
   - Order created, confirmation SMS sent

3. **Admin Flow**:
   - View users via `/admin/users`
   - View orders via `/admin/orders`
   - Check order details match SMS interactions

## Notes

- **Mock SMS**: If AT credentials are invalid, SMS calls are logged but not sent (app continues working).
- **Database**: SQLite file (`pricechekrider.db`) is created automatically on first run.
- **CORS**: Enabled for all origins (for testing). Restrict in production.
