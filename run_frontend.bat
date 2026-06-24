@echo off
REM Gym Workout RAG - Windows Application Startup Script

echo ============================================
echo   Gym Workout RAG - Application Launcher
echo ============================================
echo.

REM Get the directory where the script is located
cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\" (
    echo [WARN] Virtual environment not found!
    echo [INFO] Creating virtual environment...
    echo.
    
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created
    echo.
    
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
    echo.
    
    echo [INFO] Upgrading pip...
    python -m pip install --upgrade pip
    echo.
    
    echo [INFO] Installing dependencies...
    echo [WAIT] This may take 5-10 minutes...
    echo.
    pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install dependencies!
        echo.
        echo Common Windows issues:
        echo 1. ChromaDB requires Visual C++ Build Tools
        echo    Download: https://visualstudio.microsoft.com/visual-cpp-build-tools/
        echo.
        echo 2. Alternative: Use Docker (see README.md)
        echo.
        echo 3. Or try: pip install --only-binary :all: chromadb
        echo.
        pause
        exit /b 1
    )
    echo.
    echo [OK] Dependencies installed successfully
    echo.
    
    REM Check if .env exists
    if not exist ".env" (
        echo [WARN] .env file not found!
        if exist ".env.example" (
            echo [INFO] Copying .env.example to .env...
            copy .env.example .env >nul
            echo [OK] .env file created
            echo.
            echo [ACTION REQUIRED] Please edit .env file with your settings:
            echo   - Set your LLM configuration
            echo   - Add API keys if using cloud services
            echo.
            echo Opening .env in notepad...
            start notepad .env
            echo.
            echo Press any key after editing .env to continue...
            pause >nul
        ) else (
            echo [ERROR] .env.example not found!
            pause
            exit /b 1
        )
    )
)

REM Verify venv is working by checking if Python is in venv
echo [INFO] Verifying virtual environment...
if not exist "venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment is corrupted!
    echo Please delete the venv folder and run this script again.
    pause
    exit /b 1
)

REM Install Flask dependencies if needed (using venv Python)
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
