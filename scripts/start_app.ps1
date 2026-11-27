$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path "frontend/dist/index.html")) {
    throw "Build the frontend first: cd frontend; npm ci; npm run build"
}
& ".venv/Scripts/python.exe" -m uvicorn app:app --host 127.0.0.1 --port 8000
