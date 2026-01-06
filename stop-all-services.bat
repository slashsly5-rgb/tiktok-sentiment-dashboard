@echo off
echo ========================================
echo Stopping All Dashboard Services
echo ========================================
echo.

echo Stopping Python processes...
taskkill /F /IM python.exe 2>nul
if %errorlevel% equ 0 (
    echo   - Backend API stopped
) else (
    echo   - No backend processes found
)

echo.
echo Stopping Node processes...
taskkill /F /IM node.exe 2>nul
if %errorlevel% equ 0 (
    echo   - Frontend and tunnels stopped
) else (
    echo   - No node processes found
)

echo.
echo ========================================
echo All services stopped!
echo ========================================
echo.
pause
