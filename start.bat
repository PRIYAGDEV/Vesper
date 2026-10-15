@echo off
cd /d "%~dp0"
echo Starting Wispr Flow Clone...
start "" ".venv\Scripts\pythonw.exe" main.py
