"""
FastAPI main application entry point.
Initializes the application, creates database tables, and includes routers.
"""
import json
import logging
from urllib.parse import parse_qs, unquote_plus

from fastapi import FastAPI, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from sqlalchemy import text
from app.database import Base, engine, SessionLocal
from app.routers import ussd, sms, admin
from app.routers.ussd import _ussd_logic
from app.routers.sms import handle_incoming_sms
from app.routers.sms import SMSRequest as SMSRequestModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# OpenAPI tags for Swagger UI grouping and descriptions
openapi_tags = [
    {
        "name": "USSD",
        "description": "Africa's Talking USSD callbacks. Menu: 1=Compare Prices, 2=My Orders. Use **text** for session state (e.g. `1*Westlands`).",
    },
    {
        "name": "SMS",
        "description": "Incoming SMS from customers. Send product names (e.g. Sugar, Milk) or **ORDER** to place order. Response is sent back via SMS.",
    },
    {
        "name": "Admin",
        "description": "View users and orders. For demo and debugging.",
    },
    {
        "name": "Health",
        "description": "API status and health check.",
    },
]

# Create FastAPI app with Swagger as primary docs
app = FastAPI(
    title="PriceChekRider API",
    description="USSD/SMS retail system for the Kenyan market. Use **Swagger UI** below to try all endpoints.",
    version="1.0.0",
    openapi_tags=openapi_tags,
    docs_url="/docs",           # Swagger UI (primary)
    openapi_url="/openapi.json",
    redoc_url=None,             # Custom /redoc with embedded schema
)

# Add CORS middleware for testing from browser/frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Create database tables and run migrations on application startup."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        # Add city_code to users if missing (migration for existing DBs)
        with engine.connect() as conn:
            r = conn.execute(text("PRAGMA table_info(users)"))
            cols = [row[1] for row in r]
            if "city_code" not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN city_code VARCHAR(10)"))
                conn.commit()
                logger.info("Added city_code column to users")
    except Exception as e:
        logger.error(f"Failed to create database tables: {e}")
        raise


@app.get(
    "/",
    response_class=HTMLResponse,
    include_in_schema=True,
    summary="Welcome page",
    description="HTML welcome page with links to **Swagger UI** (/docs), ReDoc, and health check.",
    tags=["Health"],
)
async def root():
    """Root endpoint - shows welcome page in browser, or use /health for JSON."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>PriceChekRider API</title>
        <style>
            body { font-family: system-ui, sans-serif; max-width: 600px; margin: 3rem auto; padding: 0 1rem; }
            h1 { color: #2563eb; }
            a { color: #2563eb; }
            ul { line-height: 1.8; }
            code { background: #f1f5f9; padding: 2px 6px; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>PriceChekRider API</h1>
        <p>USSD/SMS retail system for the Kenyan market.</p>
        <p><strong>Status:</strong> API is live.</p>
        <h2>Quick links</h2>
        <ul>
            <li><a href="/docs">Interactive API docs (Swagger)</a></li>
            <li><a href="/redoc">ReDoc API documentation</a></li>
            <li><a href="/health">Health check (JSON)</a></li>
        </ul>
        <h2>Africa's Talking Callback Endpoints</h2>
        <ul>
            <li><code>POST /ussd/at</code> — <strong>USSD callback</strong> (set in AT dashboard)</li>
            <li><code>POST /incoming-sms</code> — <strong>SMS callback</strong> (set in AT dashboard)</li>
        </ul>
        <h2>Admin Endpoints</h2>
        <ul>
            <li><code>GET /admin/users</code> — List users</li>
            <li><code>GET /admin/orders</code> — List orders</li>
        </ul>
    </body>
    </html>
    """


@app.post(
    "/",
    include_in_schema=False,
)
async def root_post(
    request: Request,
    sessionId: str | None = Form(None),
    serviceCode: str | None = Form(None),
    phoneNumber: str | None = Form(None),
    text: str = Form(""),
    input: str = Form(""),  # Africa's Talking USSD: user input as 'input' field
    from_number: str | None = Form(None, alias="from"),  # Africa's Talking SMS: sender
    to_dest: str | None = Form(None, alias="to"),        # Africa's Talking SMS: shortcode
    date: str = Form(""),  # Africa's Talking SMS: timestamp
    linkId: str | None = Form(None),
):
    """
    POST to / : handle both USSD and SMS callbacks when Africa's Talking points at root.
    USSD: form has phoneNumber, sessionId, serviceCode, text/input.
    SMS: form has from, to, text, date (no phoneNumber/sessionId).
    """
    content_type = request.headers.get("content-type", "")

    if "application/x-www-form-urlencoded" not in content_type:
        logger.warning(f"POST to / from {request.client.host if request.client else 'unknown'}, Content-Type: {content_type}")
        return PlainTextResponse(content="ERROR: Use /ussd/at for USSD and /incoming-sms for SMS.", status_code=400)

    # 1) USSD: Africa's Talking sends phoneNumber, sessionId, serviceCode, text/input
    if phoneNumber and sessionId:
        user_input = (input or text or "").strip()
        logger.info(
            f"POST / USSD: phone={phoneNumber[:10]}..., "
            f"session={sessionId[:20]}..., serviceCode={serviceCode}, "
            f"user_input='{user_input}' (from input='{input}', text='{text}')"
        )
        db = SessionLocal()
        try:
            response_text = _ussd_logic(phoneNumber, user_input, db)
            return PlainTextResponse(content=response_text)
        finally:
            db.close()

    # 2) SMS: Africa's Talking sends from, to, text, date (no phoneNumber/sessionId)
    if from_number:
        logger.info(
            f"POST / SMS callback: from={from_number[:10]}..., to={to_dest}, text='{text[:50] if text else ''}'"
        )
        sms_request = SMSRequestModel(
            from_=from_number,
            to=to_dest or "",
            text=text or "",
            date=date or "",
            linkId=linkId,
        )
        db = SessionLocal()
        try:
            result = await handle_incoming_sms(sms_request, db)
            return JSONResponse(content=result.model_dump(), status_code=200)
        finally:
            db.close()

    # 3) Unknown form (e.g. health check or wrong format)
    logger.warning(
        f"POST to / from {request.client.host if request.client else 'unknown'}, "
        f"phoneNumber={phoneNumber}, sessionId={sessionId}, from_number={from_number}, "
        f"not recognized as USSD or SMS"
    )
    return PlainTextResponse(
        content="ERROR: Use /ussd/at for USSD and /incoming-sms for SMS.",
        status_code=400,
    )


@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="Returns API status. Use for monitoring or load balancers.",
    response_description="API status message",
)
async def health():
    """JSON health check for monitoring."""
    return {"status": "PriceChekRider API is live"}


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """ReDoc page with OpenAPI schema embedded inline (no fetch = no empty page)."""
    schema = app.openapi()
    schema_json = json.dumps(schema)
    # Escape for safe embedding in HTML script tag
    schema_escaped = schema_json.replace("</", "<\\/")
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <title>{app.title} - ReDoc</title>
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet"/>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.css"/>
</head>
<body>
    <div id="redoc-container"></div>
    <script src="https://cdn.jsdelivr.net/npm/redoc@2.1.3/bundles/redoc.standalone.js"></script>
    <script>
        var spec = {schema_escaped};
        Redoc.init(spec, {{}}, document.getElementById("redoc-container"));
    </script>
</body>
</html>"""
    return HTMLResponse(content=html)


# Include routers
app.include_router(ussd.router)
app.include_router(sms.router)
app.include_router(admin.router)
