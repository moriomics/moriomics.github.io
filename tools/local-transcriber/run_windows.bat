@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv314\Scripts\python.exe" (
 echo Run setup_windows.bat first.
 pause
 exit /b 1
)
".venv314\Scripts\python.exe" tools\check_python.py
if errorlevel 1 (
 pause
 exit /b 1
)
".venv314\Scripts\python.exe" run.py
if errorlevel 1 pause
