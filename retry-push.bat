@echo off
cd /d F:\code\code\agent-tool-website
echo Retrying git push every 30 seconds...
echo Press Ctrl+C to stop.
:loop
git push
if %errorlevel% equ 0 (
    echo PUSH SUCCESSFUL at %date% %time%
    pause
    exit /b 0
)
echo [%time%] Push failed, retrying in 30s...
timeout /t 30 /nobreak >nul
goto loop
