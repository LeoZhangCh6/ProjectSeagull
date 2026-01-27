@echo off
title ProjectSeagull - Stop Servers
echo Stopping ProjectSeagull servers...

:: Kill Python (backend)
taskkill /F /IM python.exe /T 2>nul
if %errorlevel%==0 (
    echo Backend stopped.
) else (
    echo No backend process found.
)

:: Kill Node (frontend)
taskkill /F /IM node.exe /T 2>nul
if %errorlevel%==0 (
    echo Frontend stopped.
) else (
    echo No frontend process found.
)

echo.
echo Done!
pause
