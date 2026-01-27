@echo off
title ProjectSeagull Launcher
echo ========================================
echo    ProjectSeagull - Starting App
echo ========================================
echo.

:: Start Backend in new window
echo Starting Backend (FastAPI)...
start "ProjectSeagull Backend" cmd /k "cd /d %~dp0backend && python run.py"

:: Wait a moment for backend to initialize
timeout /t 3 /nobreak >nul

:: Start Frontend in new window
echo Starting Frontend (React)...
start "ProjectSeagull Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

:: Wait a moment then open browser
timeout /t 5 /nobreak >nul
echo.
echo Opening browser...
start http://localhost:5173

echo.
echo ========================================
echo    Both servers are starting!
echo    Backend:  http://localhost:8000
echo    Frontend: http://localhost:5173
echo ========================================
echo.
echo You can close this window.
pause
