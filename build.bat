@echo off
REM Imaland Multiplayer - Windows Build Script
REM This script builds the game as a standalone Windows executable

echo.
echo ======================================================
echo Imaland: Sands of Redemption - Multiplayer Edition
echo Windows Build Script
echo ======================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)

echo [1/5] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo ✓ Dependencies installed

echo.
echo [2/5] Cleaning old builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist ImalandMultiplayer rmdir /s /q ImalandMultiplayer
echo ✓ Build directories cleaned

echo.
echo [3/5] Building executable with PyInstaller...
pyinstaller imaland_build.spec
if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    pause
    exit /b 1
)
echo ✓ Executable built successfully

echo.
echo [4/5] Copying game assets and configuration files...
copy *.py dist\ImalandMultiplayer\ 2>nul
copy *.json dist\ImalandMultiplayer\ 2>nul
echo ✓ Assets copied

echo.
echo [5/5] Build complete!
echo.
echo ======================================================
echo Build Output Location: dist\ImalandMultiplayer\
echo Executable: dist\ImalandMultiplayer\ImalandMultiplayer.exe
echo ======================================================
echo.
echo To run the game:
echo   cd dist\ImalandMultiplayer
echo   ImalandMultiplayer.exe
echo.
echo To package for Microsoft Store, use MSIX Packaging Tool:
echo   1. Download from Microsoft Store
echo   2. Select "Package an application"
echo   3. Browse to dist\ImalandMultiplayer\ImalandMultiplayer.exe
echo   4. Follow the wizard to create .msix package
echo.
pause
