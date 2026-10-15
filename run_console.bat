@echo off
cd /d "%~dp0"
echo Starting Wispr Flow Clone with console logs...
".venv\Scripts\python.exe" main.py
pause
