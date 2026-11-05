@echo off
setlocal enabledelayedexpansion

:: Set working directory to project root
cd /d "%~dp0"

echo ========================================================
echo               SenyaSabi App + Backend Launcher
echo ========================================================
echo.

:: Configure PYTHONPATH so both root and senyasabi modules resolve
set "PYTHONPATH=%CD%;%CD%\senyasabi"

:: Detect Python executable in .venv or system PATH
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
    echo [OK] Using virtual environment: .venv\Scripts\python.exe
) else (
    set "PYTHON_EXE=python"
    echo [INFO] Virtual environment not found, falling back to system python
)

:: Check if backend is already listening on port 8000
set "BACKEND_STARTED=0"
netstat -ano | findstr :8000 | findstr LISTENING >nul
if %errorlevel% equ 0 (
    echo [OK] FastAPI backend is already active on http://127.0.0.1:8000
) else (
    echo [STARTING] Launching FastAPI backend on http://127.0.0.1:8000 ...
    start "SenyaSabi Backend" "%PYTHON_EXE%" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
    set "BACKEND_STARTED=1"
    echo [WAIT] Waiting for backend to initialize...
    timeout /t 2 /nobreak >nul
)

echo [STARTING] Launching SenyaSabi Desktop App...
echo.
"%PYTHON_EXE%" senyasabi\main.py

echo.
echo ========================================================
echo SenyaSabi Desktop Application has closed.
echo ========================================================

:: Clean up the backend process if we started it
if "!BACKEND_STARTED!"=="1" (
    echo Terminating backend process...
    taskkill /FI "WINDOWTITLE eq SenyaSabi Backend*" /T /F >nul 2>&1
    echo [OK] Backend closed.
)

echo.
pause

