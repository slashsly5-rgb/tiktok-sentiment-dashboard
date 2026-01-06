@echo off
echo ========================================
echo TikTok Dashboard Public Tunnel Starter
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

REM Start Backend Tunnel
echo [3/4] Starting Backend Tunnel...
start "Backend Tunnel" cmd /k "npx localtunnel --port 5000"
timeout /t 3 /nobreak > nul

REM Start Frontend Tunnel
echo [4/4] Starting Frontend Tunnel...
start "Frontend Tunnel" cmd /k "npx localtunnel --port 3000"

echo.
echo ========================================
echo All services started!
echo ========================================
echo.
echo Check the tunnel windows for:
echo - Frontend URL (port 3000)
echo - Backend URL (port 5000)
echo - Tunnel passwords (if required)
echo.
echo Press any key to view service URLs...
pause > nul

REM Wait a bit for tunnels to initialize
timeout /t 5 /nobreak > nul

echo.
echo ========================================
echo Local URLs:
echo ========================================
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:5000
echo.
echo Public tunnel URLs and passwords are shown
echo in the tunnel windows. Look for:
echo   "your url is: https://xxxxx.loca.lt"
echo   "your tunnel password is: xxxxx"
echo.
echo ========================================
echo.
echo All services are running in separate windows.
echo Close those windows to stop the services.
echo.
pause
