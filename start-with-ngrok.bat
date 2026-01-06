@echo off
echo ========================================
echo TikTok Dashboard - Ngrok Tunnel Starter
echo ========================================
echo.

REM Start Backend API
echo [1/4] Starting Backend API on port 5000...
start "Backend API" cmd /k "cd backend && python run_api.py"
timeout /t 5 /nobreak > nul

REM Start Frontend Dev Server
echo [2/4] Starting Frontend on port 3000...
start "Frontend Dev" cmd /k "cd frontend && npm run dev"
timeout /t 5 /nobreak > nul

REM Start Backend Tunnel with ngrok
echo [3/4] Starting Backend Tunnel (ngrok)...
start "Backend Tunnel - Ngrok" cmd /k "ngrok http 5000"
timeout /t 3 /nobreak > nul

REM Start Frontend Tunnel with ngrok
echo [4/4] Starting Frontend Tunnel (ngrok)...
start "Frontend Tunnel - Ngrok" cmd /k "ngrok http 3000"

echo.
echo ========================================
echo All services started with Ngrok!
echo ========================================
echo.
echo IMPORTANT: Check the ngrok windows for your public URLs
echo They will look like: https://xxxx-xx-xxx-xxx-xxx.ngrok-free.app
echo.
echo NO PASSWORD REQUIRED! Just visit the URLs directly.
echo.
echo Local URLs:
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:5000
echo.
echo ========================================
echo.
echo Next steps:
echo 1. Find the Frontend URL in the "Frontend Tunnel" window
echo 2. Find the Backend URL in the "Backend Tunnel" window
echo 3. Update frontend/.env with the Backend URL (if needed)
echo 4. Share the Frontend URL with anyone!
echo.
echo NOTE: You may see an ngrok warning page on first visit.
echo       Just click "Visit Site" to continue.
echo.
echo ========================================
pause
