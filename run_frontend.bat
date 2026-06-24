@echo off
REM Gym Workout RAG - Windows Application Startup Script

echo ============================================
echo   Gym Workout RAG - Application Launcher
echo ============================================
echo.

REM Get the directory where the script is located
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv\" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then: venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM Install Flask dependencies if needed
echo [INFO] Checking Flask dependencies...
venv\Scripts\pip install -q Flask requests

echo.
echo [INFO] Starting application...
echo.
echo [URL] Flask Frontend: http://localhost:7500
echo [URL] FastAPI Backend: http://localhost:7501
echo.
echo [WAIT] Please wait 10-30 seconds for both servers to initialize
echo [TIP] Press Ctrl+C to stop both servers
echo.
echo ============================================
echo.

REM Run the Flask app (which will auto-start FastAPI)
venv\Scripts\python flask\app.py

REM Made with Bob

@REM Made with Bob
