@echo off
cd /d "%~dp0"
"C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe" "%~dp0main.py"
if errorlevel 1 pause
