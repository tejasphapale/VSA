@echo off
REM Shop Billing Software Startup Script for Windows

echo.
echo ==================================
echo Shop Billing Software
echo ==================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.7 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo [OK] Python found
echo.

REM Navigate to script directory
cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo [INFO] Installing dependencies...
pip install -q -r requirements.txt

REM Create data directory if it doesn't exist
if not exist "data" mkdir data

echo.
echo [OK] Setup complete!
echo.
echo [INFO] Starting application...
echo [INFO] Open your browser and go to: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run the application
python run.py

pause
