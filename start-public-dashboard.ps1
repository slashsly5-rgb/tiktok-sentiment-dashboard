# TikTok Dashboard Public Tunnel Starter (PowerShell)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TikTok Dashboard Public Tunnel Starter" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start Backend API
Write-Host "[1/4] Starting Backend API on port 5000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python run_api.py" -WindowStyle Normal
Start-Sleep -Seconds 5

# Start Frontend Dev Server
Write-Host "[2/4] Starting Frontend on port 3000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev" -WindowStyle Normal
Start-Sleep -Seconds 5

# Start Backend Tunnel
Write-Host "[3/4] Starting Backend Tunnel..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npx localtunnel --port 5000" -WindowStyle Normal
Start-Sleep -Seconds 3

# Start Frontend Tunnel
Write-Host "[4/4] Starting Frontend Tunnel..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npx localtunnel --port 3000" -WindowStyle Normal

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "All services started!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Local URLs:" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  Backend:  http://localhost:5000" -ForegroundColor White
Write-Host ""
Write-Host "Public tunnel URLs and passwords are shown" -ForegroundColor Yellow
Write-Host "in the tunnel windows. Look for:" -ForegroundColor Yellow
Write-Host "  'your url is: https://xxxxx.loca.lt'" -ForegroundColor White
Write-Host "  'your tunnel password is: xxxxx'" -ForegroundColor White
Write-Host ""
Write-Host "All services are running in separate windows." -ForegroundColor Cyan
Write-Host "Close those windows to stop the services." -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to exit this window..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
