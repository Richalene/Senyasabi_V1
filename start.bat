@echo off
echo Setting up SenyaSabi...

REM Check if Python 3.12 is installed using the Python launcher
py -3.12 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python 3.12.6 is not installed on this system.
    echo Attempting to install Python 3.12.6 automatically via winget...
    
    winget install -e --id Python.Python.3.12 --version 3.12.6 --scope machine --silent --accept-source-agreements --accept-package-agreements
    
    if %errorlevel% neq 0 (
        echo.
        echo Automatic installation failed or requires administrator privileges.
        echo Please manually download and install Python 3.12.6 from:
        echo https://www.python.org/downloads/release/python-3126/
        echo Make sure to check "Add python.exe to PATH" during installation.
        pause
        exit /b 1
    )
    echo Python 3.12.6 installed successfully.
)

REM Create virtual environment using Python 3.12 if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment with Python 3.12...
    py -3.12 -m venv venv
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment. Please check your Python installation.
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo Installing Python dependencies from requirements.txt...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install requirements. Please check your Python installation.
    pause
    exit /b 1
)

REM Copy .env.example to .env if it exists
if exist "senyasabi\.env.example" (
    echo Creating .env file from .env.example...
    copy "senyasabi\.env.example" "senyasabi\.env"
    if %errorlevel% neq 0 (
        echo Failed to create .env file.
        pause
        exit /b 1
    )
) else (
    echo Warning: senyasabi\.env.example not found. Please create senyasabi\.env manually.
)

REM Run launcher.py (or your test wrapper script)
echo Starting SenyaSabi with Backend...
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe launcher.py
) else (
    python launcher.py
)
if %errorlevel% neq 0 (
    echo Failed to start SenyaSabi.
    pause
    exit /b 1
)

pause