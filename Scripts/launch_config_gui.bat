@echo off
REM Launcher script for General Configuration GUI

echo ==========================================
echo ProjectSeagull Configuration Manager
echo ==========================================
echo.

REM Check if DATABASE_URL is set
if "%DATABASE_URL%"=="" (
    if "%PGHOST%"=="" (
        echo ERROR: Database connection not configured!
        echo Please set DATABASE_URL or PGHOST environment variable.
        echo.
        pause
        exit /b 1
    )
)

echo Starting Configuration Manager...
echo.

cd /d "%~dp0.."
python Scripts\general_config_gui.py

if errorlevel 1 (
    echo.
    echo Tool exited with error.
    pause
)
