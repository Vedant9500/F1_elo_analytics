@echo off
REM F1 ELO Web Application Launcher
REM Double-click this file to start the app

echo.
echo ========================================
echo   F1 ELO Rankings Web Application
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

echo Python found!
echo.

REM Check if dependencies are installed
echo Checking dependencies...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo.
    echo Flask not found. Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo Dependencies OK!
echo.

REM Check if database exists
if not exist "DB\f1_database.db" (
    echo WARNING: Database not found at DB\f1_database.db
    echo Please ensure the database is set up properly.
    pause
)

REM Start the application
echo Starting F1 ELO Web Application...
echo.
echo The app will be available at: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.

python app.py

pause
