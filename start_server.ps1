# Start PriceChekRider FastAPI server
# Usage: .\start_server.ps1

Write-Host "Starting PriceChekRider server..." -ForegroundColor Green

# Activate virtual environment
& ".\venv\Scripts\Activate.ps1"

# Start uvicorn with correct module path: app.main:app
Write-Host "Running: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Yellow
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
