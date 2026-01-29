"""
FastAPI main application entry point.
Initializes the application, creates database tables, and includes routers.
"""
import json
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy import text
from app.database import Base, engine
from app.routers import ussd, sms, admin

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
        <h2>Endpoints</h2>
        <ul>
            <li><code>POST /ussd</code> — USSD callback</li>
            <li><code>POST /incoming-sms</code> — SMS callback</li>
            <li><code>GET /admin/users</code> — List users</li>
            <li><code>GET /admin/orders</code> — List orders</li>
        </ul>
    </body>
    </html>
    """


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
