@echo off
REM start-waf.bat - create venv, install requirements, and start the WAF
SETLOCAL ENABLEDELAYEDEXPANSION
SET ROOT=%~dp0
echo Using project root: %ROOT%

where python >nul 2>&1
IF ERRORLEVEL 1 (
  echo Python not found in PATH. Install Python 3 and retry.
  exit /b 1
)

python -m venv "%ROOT%\.venv"
call "%ROOT%\.venv\Scripts\activate.bat"

python -m pip install --upgrade pip
IF EXIST "%ROOT%\requirements.txt" (
  pip install -r "%ROOT%\requirements.txt"
)

echo Starting WAF (main.py) on port 8082...
python "%ROOT%\main.py" --port 8082
