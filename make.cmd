@echo off
setlocal
if "%~1"=="" (
  echo Drag an edited video onto this file, or run make.cmd "video.mp4".
  pause
  exit /b 1
)
python -c "import numpy,PIL" >nul 2>nul
if errorlevel 1 (
  python -m pip install -r "%~dp0requirements.txt"
  if errorlevel 1 exit /b 1
)
python "%~dp0scripts\run.py" "%~1"
if errorlevel 1 (
  echo Failed. Review the error above.
  pause
  exit /b 1
)
pause
