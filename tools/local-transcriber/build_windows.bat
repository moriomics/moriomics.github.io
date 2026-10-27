@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv314\Scripts\python.exe" goto missing
if not exist "vendor\ffmpeg\ffmpeg.exe" goto missing
if not exist "vendor\ffmpeg\ffprobe.exe" goto missing
".venv314\Scripts\python.exe" tools\check_python.py
if errorlevel 1 goto fail
".venv314\Scripts\python.exe" -m pytest -q
if errorlevel 1 goto fail
".venv314\Scripts\python.exe" -m PyInstaller --noconfirm --clean LocalTranscriber.spec
if errorlevel 1 goto fail
".venv314\Scripts\python.exe" -m pip freeze > dist\LocalTranscriber\build-environment.txt
echo Built dist\LocalTranscriber\LocalTranscriber.exe
echo Distribute the complete dist\LocalTranscriber folder, not only the exe.
echo Complete docs\ACCEPTANCE_TESTS.md on a clean Windows PC before release.
pause
exit /b 0
:missing
echo Run setup_windows.bat and place ffmpeg.exe and ffprobe.exe in vendor\ffmpeg.
:fail
echo Build failed. See the error above.
pause
exit /b 1
