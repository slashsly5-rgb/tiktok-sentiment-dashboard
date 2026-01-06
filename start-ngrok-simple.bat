@echo off
echo ========================================
echo TikTok Dashboard - Ngrok (Simple Setup)
echo ========================================
echo.
echo This script uses ONE ngrok tunnel for the frontend.
echo The frontend proxies API requests to the backend.
echo NO PASSWORDS REQUIRED!
echo.

REM Start Backend API
echo [1/3] Starting Backend API on port 5000...
start "Backend API" cmd /k "cd backend && python run_api.py"
timeout /t 5 /nobreak > nul

REM Start Frontend Dev Server with Proxy
echo [2/3] Starting Frontend with API Proxy on port 3000...
start "Frontend Dev" cmd /k "cd frontend && npm run dev"
timeout /t 7 /nobreak > nul

REM Start Ngrok Tunnel (Frontend Only)
echo [3/3] Starting Ngrok Tunnel...
start "Ngrok Tunnel" cmd /k "ngrok http 3000"

echo.
echo ========================================
echo All services started!
echo ========================================
echo.
echo Check the "Ngrok Tunnel" window for your public URL.
echo It will look like: https://xxxx-xxxx-xxxx.ngrok-free.dev
echo.
echo The frontend will automatically proxy API calls to the backend.
echo NO separate backend tunnel needed!
echo.
echo Local URLs:
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:5000
echo.
echo ========================================
echo.
echo Press any key when ready to view ngrok URL...
pause > nul

timeout /t 5 /nobreak > nul

REM Try to get ngrok URL
echo.
echo Fetching ngrok URL...
curl -s http://localhost:4040/api/tunnels > nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo Your public URL is displayed in the "Ngrok Tunnel" window.
    echo Look for the line that says: "Forwarding https://..."
) else (
    echo.
    echo Check the "Ngrok Tunnel" window for your public URL.
)

echo.
echo NOTE: First-time visitors may see an ngrok warning page.
echo       Just click "Visit Site" to continue.
echo.
pause
