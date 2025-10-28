#!/bin/bash
echo "--- Binance Bot Linux Build Script ---"

# Check for python3
if ! command -v python &> /dev/null
then
    echo "Python could not be found! Please install it."
    exit
fi

echo "Creating virtual environment in '.venv' folder..."
python -m venv .venv

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Updating pip and installing dependencies from req.txt..."
pip install --upgrade pip
pip install -r req.txt

if [ $? -ne 0 ]; then
    echo "Failed to install dependencies! Aborting."
    exit 1
fi

echo "Building the Linux executable (this may take a moment)..."
pyinstaller --onefile --name "BinanceBot" --copy-metadata customtkinter \
    --add-data ".venv/lib/python*/site-packages/dateparser/data:dateparser/data" \
    --add-data ".venv/lib/python*/site-packages/customtkinter:customtkinter" \
    --hidden-import customtkinter --hidden-import dateparser src/main.py

if [ $? -ne 0 ]; then
    echo "PyInstaller failed! See output above for errors."
    exit 1
fi

echo "--- Build Complete! ---"
echo "Your executable file is located in the 'dist' folder."
