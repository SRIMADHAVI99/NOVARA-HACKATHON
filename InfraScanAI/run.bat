@echo off
echo ==========================================
echo Starting Infra Scan AI - Road Damage System
echo ==========================================
echo.
echo Activating Virtual Environment...
call .\venv\Scripts\activate.bat
echo Starting Flask Server...
python app.py
pause
