@echo off
REM Move to the directory of this script (saving current directory to return later)
pushd "%~dp0"

REM Check if 'uv' is installed
where uv >nul 2>nul
if errorlevel 1 (
    pip install uv
)

REM Recreate venv only if needed
if not exist ".venv" (
    echo Creating virtual environment...
    uv venv .venv
) else (
    echo Using existing virtual environment...
)

REM Activate the virtual environment
call .venv\Scripts\activate.bat

where node >nul 2>nul
if errorlevel 1 (
    echo Node.js is not installed. Please install Node.js from https://nodejs.org/ and re-run this script.
    exit /b 1
)

REM Install the required packages
uv pip install .
cd src/utils/blockchain/lib
call npm install typescript
call npm run build
popd

REM Set the PYTHONPATH environment variable
set PYTHONPATH=%PYTHONPATH%;%CD%\src\