#!/bin/bash
# F1 ELO Web Application Launcher for Linux/Mac
# Run this file to start the app: ./start_app.sh

echo ""
echo "========================================"
echo "  F1 ELO Rankings Web Application"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from python.org"
    exit 1
fi

echo "Python found!"
echo ""

# Check if dependencies are installed
echo "Checking dependencies..."
python3 -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo ""
    echo "Flask not found. Installing dependencies..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install dependencies"
        exit 1
    fi
fi

echo "Dependencies OK!"
echo ""

# Check if database exists
if [ ! -f "DB/f1_database.db" ]; then
    echo "WARNING: Database not found at DB/f1_database.db"
    echo "Please ensure the database is set up properly."
    read -p "Press enter to continue..."
fi

# Start the application
echo "Starting F1 ELO Web Application..."
echo ""
echo "The app will be available at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 app.py
