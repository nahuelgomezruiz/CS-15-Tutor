@echo off
setlocal enabledelayedexpansion

REM CS15 Tutor Web App Setup Script for Windows
REM This script sets up both the frontend (Next.js) and backend (Flask API)

echo 🚀 Setting up CS15 Tutor Web App for Windows...
echo ================================================

REM Check if we're in the right directory
if not exist "web-app" (
    echo ❌ Error: web-app directory not found!
    echo Please make sure you're running this script from the CS-15-Tutor root directory.
    pause
    exit /b 1
)

if not exist "responses-api-server" (
    echo ❌ Error: responses-api-server directory not found!
    echo Please make sure you're running this script from the CS-15-Tutor root directory.
    pause
    exit /b 1
)

echo 📁 Verified project structure...

REM Check for Node.js
echo 🔍 Checking for Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed!
    echo Please install Node.js from https://nodejs.org/
    echo Recommended version: 18.x or higher
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('node --version') do set NODE_VERSION=%%i
echo ✅ Node.js found: !NODE_VERSION!

REM Check for npm
npm --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ npm is not installed!
    echo npm should come with Node.js. Please reinstall Node.js.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('npm --version') do set NPM_VERSION=%%i
echo ✅ npm found: !NPM_VERSION!

REM Check for Python
echo 🔍 Checking for Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed!
    echo Please install Python from https://python.org/
    echo Recommended version: 3.8 or higher
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ Python found: !PYTHON_VERSION!

REM Check for pip
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip is not installed!
    echo pip should come with Python. Please reinstall Python.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('pip --version') do set PIP_VERSION=%%i
echo ✅ pip found: !PIP_VERSION!

echo.
echo 🎯 Starting setup process...
echo ==============================

REM Setup Frontend (Next.js Web App)
echo.
echo 📦 Setting up Frontend (Next.js)...
cd web-app

echo    Installing frontend dependencies...
call npm install
if %errorlevel% neq 0 (
    echo ❌ Failed to install frontend dependencies!
    pause
    exit /b 1
)
echo ✅ Frontend dependencies installed successfully!

echo    Setting up frontend for development mode...
echo    Creating .env.local file for development environment...
echo DEVELOPMENT_MODE=true > .env.local
echo    (Skipping production build - will use 'npm run dev' for development)
echo ✅ Frontend configured for development mode!

cd ..

REM Setup Backend (Flask API)
echo.
echo 🐍 Setting up Backend (Flask API)...
cd responses-api-server

echo    Creating Python virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ❌ Failed to create virtual environment!
    pause
    exit /b 1
)
echo ✅ Virtual environment created!

echo    Activating virtual environment...
call venv\Scripts\activate.bat

echo    Installing backend dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ Failed to install backend dependencies!
    call venv\Scripts\deactivate.bat
    pause
    exit /b 1
)
echo ✅ Backend dependencies installed successfully!

echo    Configuring Flask for development mode...
echo set FLASK_ENV=development >> venv\Scripts\activate.bat
echo set FLASK_DEBUG=True >> venv\Scripts\activate.bat
echo set DEVELOPMENT_MODE=true >> venv\Scripts\activate.bat
echo set PYTHONPATH=%%PYTHONPATH%%;%%CD%% >> venv\Scripts\activate.bat
echo ✅ Flask development environment configured!

REM Check if system_prompt.txt exists
if not exist "system_prompt.txt" (
    echo ⚠️  Warning: system_prompt.txt not found!
    echo    The API server requires this file to run properly.
    echo    Please make sure system_prompt.txt exists in the responses-api-server directory.
)

call venv\Scripts\deactivate.bat
cd ..

echo.
echo 🎉 Setup completed successfully!
echo ================================
echo.
echo 🚀 To start the development servers:
echo.
echo 1. Start the Backend (Flask API) in DEVELOPMENT MODE:
echo    cd responses-api-server
echo    venv\Scripts\activate.bat  # Sets FLASK_DEBUG=True, FLASK_ENV=development ^& DEVELOPMENT_MODE=true
echo    python index.py
echo    (Server will run on http://127.0.0.1:5000 with debug mode enabled)
echo.
echo 2. In a new terminal, start the Frontend (Next.js) in DEVELOPMENT MODE:
echo    cd web-app
echo    npm run dev  # Hot reload enabled for development
echo    (Server will run on http://localhost:3000 with hot reload)
echo.
echo 📚 Make sure to:
echo    - Configure your authentication system
echo    - Set up the llmproxy service
echo    - Ensure system_prompt.txt is properly configured
echo.
echo 🎯 Happy coding! The CS15 Tutor is ready for development!
echo.
pause 