@echo off
setlocal enabledelayedexpansion
title SenyaSabi Launcher (App + FastAPI Backend)

echo ===================================================
echo             SenyaSabi Desktop & Backend
echo ===================================================
echo.

REM Determine the Python executable to use
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
) else if exist "venv\Scripts\python.exe" (
    set "PYTHON_EXE=venv\Scripts\python.exe"
) else (
    py -3.12 --version >nul 2>&1
    if !errorlevel! equ 0 (
        set "PYTHON_EXE=py -3.12"
    ) else (
        python --version >nul 2>&1
        if !errorlevel! equ 0 (
            set "PYTHON_EXE=python"
        ) else (
            echo [ERROR] No Python environment found.
            echo Please install Python 3.12 or create a virtual environment in .venv.
            pause
            exit /b 1
        )
    )
)

echo Using Python: %PYTHON_EXE%

REM Set PYTHONPATH so both project root and senyasabi are discoverable
set "PYTHONPATH=%CD%;%CD%\senyasabi;%PYTHONPATH%"

REM Copy .env.example to senyasabi\.env if not already present
if not exist "senyasabi\.env" (
    if exist "senyasabi\.env.example" (
        echo [INFO] Creating senyasabi\.env from .env.example...
        copy "senyasabi\.env.example" "senyasabi\.env" >nul
    )
)

echo.
echo [1/2] Starting FastAPI backend server on 127.0.0.1:8000...
start "SenyaSabi FastAPI Backend" /min cmd /c "%PYTHON_EXE% -m uvicorn senyasabi.backend.main:app --host 127.0.0.1 --port 8000"

echo [2/2] Launching SenyaSabi GUI application...
echo.
%PYTHON_EXE% senyasabi\main.py

echo.
echo SenyaSabi application closed.
REM Cleanup: Close the background FastAPI uvicorn window when GUI exits
taskkill /FI "WINDOWTITLE eq SenyaSabi FastAPI Backend*" /F >nul 2>&1

exit /b 0
