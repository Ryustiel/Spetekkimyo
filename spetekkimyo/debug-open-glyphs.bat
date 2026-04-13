@echo off
setlocal
cd /d "%~dp0"
set "PORT=8000"
set "URL=http://127.0.0.1:%PORT%/live_glyphs.html"
set "PYEXE="
where python >nul 2>nul && set "PYEXE=python"
if not defined PYEXE (
  where py >nul 2>nul && set "PYEXE=py -3"
)
if not defined PYEXE (
  echo Python is not installed or not on PATH.
  pause
  exit /b 1
)
echo Starting backend...
echo Open this in your browser:
echo %URL%
echo.
%PYEXE% glyph_server.py --host 127.0.0.1 --port %PORT%
echo.
echo Backend exited with code %errorlevel%.
pause
endlocal
