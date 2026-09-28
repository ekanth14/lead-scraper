# Start everything locally with one command in PowerShell
Write-Host "Starting Lead Scraper..." -ForegroundColor Cyan

# Backend
Push-Location backend
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt -q
}
$backend = Start-Process uvicorn -ArgumentList "app.main:app --reload --port 8000" -PassThru
Pop-Location

# Frontend
Push-Location frontend
npm install -q
$frontend = Start-Process npm -ArgumentList "run dev" -PassThru
Pop-Location

Write-Host "✅ Backend: http://localhost:8000" -ForegroundColor Green
Write-Host "✅ Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "✅ API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop both servers" -ForegroundColor Yellow

try {
    Wait-Process -Id $backend.Id, $frontend.Id
} finally {
    if ($backend -and -not $backend.HasExited) { Stop-Process -Id $backend.Id -Force }
    if ($frontend -and -not $frontend.HasExited) { Stop-Process -Id $frontend.Id -Force }
}
