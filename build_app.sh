#!/bin/bash

# Build script for YouTube Extractor

echo "Building YouTube Extractor for macOS..."

# Create the icon if it doesn't exist
if [ ! -f "app_icon.icns" ]; then
    echo "Creating application icon..."
    python create_icon.py
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Build the application
echo "Building application with PyInstaller..."
pyinstaller youtube_app.spec

# Check if build was successful
if [ -d "dist/YouTube Extractor.app" ]; then
    echo "Build successful!"
    echo "Application is located at: $(pwd)/dist/YouTube Extractor.app"
    echo ""
    echo "To run the application, double-click on 'YouTube Extractor.app' in the Finder"
    echo "or run: open \"$(pwd)/dist/YouTube Extractor.app\""
    echo ""
    echo "To create a distributable DMG file, you can use create-dmg:"
    echo "brew install create-dmg"
    echo "create-dmg --volname \"YouTube Extractor\" --volicon \"app_icon.icns\" --window-pos 200 120 --window-size 800 400 --icon \"YouTube Extractor.app\" 200 190 --app-drop-link 600 185 \"YouTube Extractor.dmg\" \"dist/YouTube Extractor.app\""
else
    echo "Build failed. Check the output for errors."
    exit 1
fi 