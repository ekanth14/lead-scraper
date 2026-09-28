@echo off
echo Starting Lead Scraper...

start "Lead Scraper - Backend" cmd /k "cd /d %~dp0backend && pip install -r requirements.txt -q && uvicorn app.main:app --reload --port 8000"
start "Lead Scraper - Frontend" cmd /k "cd /d %~dp0frontend && npm install -q && npm run dev"

echo.
echo ========================================================
echo ✅ Backend:  http://localhost:8000
echo ✅ Frontend: http://localhost:5173
echo ✅ API Docs: http://localhost:8000/docs
echo ========================================================
echo Press any key to exit launcher (servers will remain running).
pause
