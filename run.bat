@echo off
echo =====================================
echo   Learning Agent Web Interface Setup
echo =====================================

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] Python is not installed or not in PATH. Please install Python and try again.
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
    echo [✓] Found Python %PYTHON_VERSION%
)

REM Check if pip is installed
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [X] pip is not installed or not in PATH. Please install pip and try again.
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('pip --version') do set PIP_VERSION=%%i
    echo [✓] Found pip version %PIP_VERSION%
)

REM Check if .env file exists
if exist .env (
    echo [✓] Found .env file
) else (
    echo [!] No .env file found. Using default environment variables.
    echo     You can create a .env file based on .env.example if needed.
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Check if JAF is installed
python -c "import jaf" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] JAF framework not found. Make sure it's installed and in your Python path.
    echo     The application may not work correctly without it.
)

echo =====================================
echo   Starting the Learning Agent Web Interface
echo =====================================
echo Open your browser and navigate to http://localhost:5000
echo Press Ctrl+C to stop the server
echo =====================================

REM Run the web interface with better error handling
python app.py
if %errorlevel% neq 0 (
    echo [X] Error starting the server. Check the error message above.
    pause
    exit /b 1
)
