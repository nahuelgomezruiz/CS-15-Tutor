@echo off
setlocal enabledelayedexpansion

REM CS15 Tutor VSCode Extension Setup Script for Windows
REM This script compiles, packages, and installs the VSCode extension

echo 🚀 Setting up CS15 Tutor VSCode Extension for Windows...
echo =====================================================

REM Check if we're in the right directory
if not exist "vscode-extension" (
    echo ❌ Error: vscode-extension directory not found!
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

REM Check for VSCode
echo 🔍 Checking for Visual Studio Code...
code --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Visual Studio Code is not installed or not in PATH!
    echo Please install VSCode from https://code.visualstudio.com/
    echo Make sure to check "Add to PATH" during installation.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('code --version') do set VSCODE_VERSION=%%i
echo ✅ VSCode found: !VSCODE_VERSION!

echo.
echo 🎯 Starting extension setup process...
echo =====================================

REM Navigate to extension directory
echo.
echo 📦 Setting up VSCode Extension...
cd vscode-extension

echo    Installing extension dependencies...
call npm install
if %errorlevel% neq 0 (
    echo ❌ Failed to install extension dependencies!
    pause
    exit /b 1
)
echo ✅ Extension dependencies installed successfully!

echo    Installing vsce (VSCode Extension Manager)...
call npm install -g @vscode/vsce
if %errorlevel% neq 0 (
    echo ❌ Failed to install vsce!
    echo You might need to run this script as Administrator.
    pause
    exit /b 1
)
echo ✅ vsce installed successfully!

echo    Compiling TypeScript...
call npm run compile
if %errorlevel% neq 0 (
    echo ❌ Failed to compile TypeScript!
    pause
    exit /b 1
)
echo ✅ TypeScript compiled successfully!

echo    Packaging extension...
call vsce package
if %errorlevel% neq 0 (
    echo ❌ Failed to package extension!
    pause
    exit /b 1
)
echo ✅ Extension packaged successfully!

REM Find the generated .vsix file
for %%f in (*.vsix) do set VSIX_FILE=%%f

if "!VSIX_FILE!"=="" (
    echo ❌ Could not find generated .vsix file!
    pause
    exit /b 1
)

echo    Found extension package: !VSIX_FILE!

echo    Installing extension in VSCode...
call code --install-extension "!VSIX_FILE!"
if %errorlevel% neq 0 (
    echo ❌ Failed to install extension!
    echo You can manually install it by:
    echo 1. Opening VSCode
    echo 2. Pressing Ctrl+Shift+P
    echo 3. Typing "Extensions: Install from VSIX"
    echo 4. Selecting the file: %CD%\!VSIX_FILE!
    pause
    exit /b 1
)
echo ✅ Extension installed successfully!

cd ..

echo.
echo 🎉 VSCode Extension setup completed successfully!
echo ===============================================
echo.
echo 🚀 The CS15 Tutor extension has been installed in VSCode!
echo.
echo 📋 To use the extension:
echo    1. Open or restart Visual Studio Code
echo    2. Look for the CS15 Tutor icon in the Activity Bar (left sidebar)
echo    3. Click on it to open the CS15 Tutor chat panel
echo    4. Sign in with your Tufts credentials
echo    5. Start asking questions!
echo.
echo 🔧 Development commands:
echo    • To recompile: cd vscode-extension ^&^& npm run compile
echo    • To package: cd vscode-extension ^&^& vsce package
echo    • To watch for changes: cd vscode-extension ^&^& npm run watch
echo.
echo 📚 Make sure the backend API server is running on http://127.0.0.1:5000
echo     (Use the webapp-setup-windows.bat script to set up the backend)
echo.
echo 🎯 Happy coding with your new CS15 Tutor VSCode extension!
echo.
pause 