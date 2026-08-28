@echo off
setlocal
python -m PyInstaller --noconfirm --clean --windowed --name MobilDesk --distpath package --workpath build_kiosko --add-data "assets;assets" --add-data "database\migrations;database\migrations" --icon "assets\kiosko_logo.ico" main.py
if errorlevel 1 exit /b 1
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\MobilDesk.iss

