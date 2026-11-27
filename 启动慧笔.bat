@echo off
cd /d "%~dp0"
if not exist "frontend\dist\index.html" (
  echo Build frontend first: cd frontend ^&^& npm ci ^&^& npm run build
  pause
  exit /b 1
)
.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
pause
