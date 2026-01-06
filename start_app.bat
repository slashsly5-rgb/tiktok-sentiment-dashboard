@echo off
echo ========================================
echo Starting TikTok Scraper App
echo ========================================

echo [1/2] Starting Backend API...
start "Backend API" cmd /k "cd backend && py run_api.py"
timeout /t 5 /nobreak > nul

echo [2/2] Starting Streamlit Dashboard...
start "Streamlit Dashboard" cmd /k "cd backend && py -m streamlit run app.py"

echo.
echo App started! 
echo API: http://localhost:5000
echo Dashboard: http://localhost:8501
echo.
pause
