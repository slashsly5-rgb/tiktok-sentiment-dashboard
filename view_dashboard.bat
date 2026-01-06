@echo off
REM Quick launcher for Project S Dashboard

echo ================================================
echo Project S - TikTok Political Sentiment Dashboard
echo ================================================
echo.

echo Select which dashboard to launch:
echo.
echo 1. HTML Dashboard (Standalone - No backend required)
echo 2. Streamlit Dashboard (Full features with database)
echo 3. Both (Open both in separate windows)
echo.

set /p choice="Enter your choice (1, 2, or 3): "

if "%choice%"=="1" (
    echo.
    echo Opening HTML Dashboard...
    start frontend/index.html
    echo HTML Dashboard opened in your default browser.
    echo.
) else if "%choice%"=="2" (
    echo.
    echo Starting Streamlit Dashboard...
    echo This will open in your browser at http://localhost:8501
    echo.
    streamlit run backend/app.py
) else if "%choice%"=="3" (
    echo.
    echo Opening HTML Dashboard...
    start frontend/index.html
    echo.
    echo Starting Streamlit Dashboard...
    streamlit run backend/app.py
) else (
    echo.
    echo Invalid choice. Please run the script again.
    echo.
)

pause
