# TikTok Dashboard - Ngrok Tunnel Starter (PowerShell)
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "TikTok Dashboard - Ngrok Tunnel Starter" -ForegroundColor Cyan
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

# Start Backend Tunnel with ngrok
Write-Host "[3/4] Starting Backend Tunnel (ngrok)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "./ngrok http 5000" -WindowStyle Normal
Start-Sleep -Seconds 3

# Start Frontend Tunnel with ngrok
Write-Host "[4/4] Starting Frontend Tunnel (ngrok)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "./ngrok http 3000" -WindowStyle Normal

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "All services started with Ngrok!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "IMPORTANT: Check the ngrok windows for your public URLs" -ForegroundColor Yellow
Write-Host "They will look like: https://xxxx-xx-xxx-xxx-xxx.ngrok-free.app" -ForegroundColor White
Write-Host ""
Write-Host "NO PASSWORD REQUIRED! Just visit the URLs directly." -ForegroundColor Green
Write-Host ""
Write-Host "Local URLs:" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  Backend:  http://localhost:5000" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Find the Frontend URL in the 'Frontend Tunnel' window" -ForegroundColor White
Write-Host "  2. Find the Backend URL in the 'Backend Tunnel' window" -ForegroundColor White
Write-Host "  3. Update frontend/.env with the Backend URL (if needed)" -ForegroundColor White
Write-Host "  4. Share the Frontend URL with anyone!" -ForegroundColor White
Write-Host ""
Write-Host "NOTE: You may see an ngrok warning page on first visit." -ForegroundColor Yellow
Write-Host "      Just click 'Visit Site' to continue." -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to exit this window..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
