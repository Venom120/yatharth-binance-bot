@echo off
ECHO "--- Binance Bot Windows Build Script ---"

REM Check for python
python --version >NUL 2>&1
IF %ERRORLEVEL% NEQ 0 (
    ECHO "Python not found! Please install Python and add it to your PATH."
    pause
    GOTO :EOF
)

ECHO "Creating virtual environment in '.venv' folder..."
python -m venv .venv

ECHO "Activating virtual environment..."
CALL .venv\Scripts\activate.bat

ECHO "Updating pip and installing dependencies from req.txt..."
pip install --upgrade pip
pip install -r req.txt

IF %ERRORLEVEL% NEQ 0 (
    ECHO "Failed to install dependencies! Aborting."
    pause
    GOTO :EOF
)

ECHO "Building the .exe file (this may take a moment)..."
pyinstaller --onefile --windowed --name "BinanceBot" main.py

IF %ERRORLEVEL% NEQ 0 (
    ECHO "PyInstaller failed! See output above for errors."
    pause
    GOTO :EOF
)

ECHO "--- Build Complete! ---"
ECHO "Your .exe file is located in the 'dist' folder."
pause