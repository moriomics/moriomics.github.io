@echo off
setlocal
cd /d "%~dp0"
py -3.14 tools\check_python.py
if errorlevel 1 goto fail
py -3.14 -m venv .venv314
if errorlevel 1 goto fail
".venv314\Scripts\python.exe" tools\check_python.py
if errorlevel 1 goto fail
".venv314\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto fail
".venv314\Scripts\python.exe" -m pip install --only-binary=:all: -r requirements-dev.txt
if errorlevel 1 goto fail
echo Setup complete. Place ffmpeg.exe and ffprobe.exe in vendor\ffmpeg.
echo Python 3.14 environment: .venv314. Previous .venv folders are unchanged.
pause
exit /b 0
:fail
echo Setup failed. Install standard 64-bit Python 3.14 and check the error above.
pause
exit /b 1
