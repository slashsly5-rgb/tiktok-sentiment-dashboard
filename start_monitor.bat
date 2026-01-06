@echo off
echo Starting TikTok Sentiment Automated Monitor...
echo.
echo Installing dependencies...
py -m pip install schedule
echo.
cd backend
echo Launching Monitor Service...
py auto_monitor.py
pause
