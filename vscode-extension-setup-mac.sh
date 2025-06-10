#!/bin/bash

# CS15 Tutor VSCode Extension Setup Script for macOS
# This script compiles, packages, and installs the VSCode extension

echo "🚀 Setting up CS15 Tutor VSCode Extension for macOS..."
echo "====================================================="

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if we're in the right directory
if [ ! -d "vscode-extension" ]; then
    echo "❌ Error: vscode-extension directory not found!"
    echo "Please make sure you're running this script from the CS-15-Tutor root directory."
    exit 1
fi

echo "📁 Verified project structure..."

# Check for Node.js
echo "🔍 Checking for Node.js..."
if ! command_exists node; then
    echo "❌ Node.js is not installed!"
    echo "Please install Node.js from https://nodejs.org/"
    echo "Recommended version: 18.x or higher"
    exit 1
fi

NODE_VERSION=$(node --version)
echo "✅ Node.js found: $NODE_VERSION"

# Check for npm
if ! command_exists npm; then
    echo "❌ npm is not installed!"
    echo "npm should come with Node.js. Please reinstall Node.js."
    exit 1
fi

NPM_VERSION=$(npm --version)
echo "✅ npm found: $NPM_VERSION"

# Check for VSCode
echo "🔍 Checking for Visual Studio Code..."
if ! command_exists code; then
    echo "❌ Visual Studio Code is not installed or not in PATH!"
    echo "Please install VSCode from https://code.visualstudio.com/"
    echo "Make sure to install the 'code' command in PATH during installation."
    exit 1
fi

VSCODE_VERSION=$(code --version | head -n 1)
echo "✅ VSCode found: $VSCODE_VERSION"

echo ""
echo "🎯 Starting extension setup process..."
echo "====================================="

# Navigate to extension directory
echo ""
echo "📦 Setting up VSCode Extension..."
cd vscode-extension

echo "   Installing extension dependencies..."
if npm install; then
    echo "✅ Extension dependencies installed successfully!"
else
    echo "❌ Failed to install extension dependencies!"
    exit 1
fi

echo "   Installing vsce (VSCode Extension Manager)..."
if npm install -g @vscode/vsce; then
    echo "✅ vsce installed successfully!"
else
    echo "❌ Failed to install vsce!"
    echo "You might need to run with sudo:"
    echo "sudo npm install -g @vscode/vsce"
    exit 1
fi

echo "   Compiling TypeScript..."
if npm run compile; then
    echo "✅ TypeScript compiled successfully!"
else
    echo "❌ Failed to compile TypeScript!"
    exit 1
fi

echo "   Packaging extension..."
if vsce package; then
    echo "✅ Extension packaged successfully!"
else
    echo "❌ Failed to package extension!"
    exit 1
fi

# Find the generated .vsix file
VSIX_FILE=$(ls *.vsix 2>/dev/null | head -n 1)

if [ -z "$VSIX_FILE" ]; then
    echo "❌ Could not find generated .vsix file!"
    exit 1
fi

echo "   Found extension package: $VSIX_FILE"

echo "   Installing extension in VSCode..."
if code --install-extension "$VSIX_FILE"; then
    echo "✅ Extension installed successfully!"
else
    echo "❌ Failed to install extension!"
    echo "You can manually install it by:"
    echo "1. Opening VSCode"
    echo "2. Pressing Ctrl+Shift+P (Cmd+Shift+P on Mac)"
    echo "3. Typing 'Extensions: Install from VSIX'"
    echo "4. Selecting the file: $(pwd)/$VSIX_FILE"
    exit 1
fi

cd ..

echo ""
echo "🎉 VSCode Extension setup completed successfully!"
echo "==============================================="
echo ""
echo "🚀 The CS15 Tutor extension has been installed in VSCode!"
echo ""
echo "📋 To use the extension:"
echo "   1. Open or restart Visual Studio Code"
echo "   2. Look for the CS15 Tutor icon in the Activity Bar (left sidebar)"
echo "   3. Click on it to open the CS15 Tutor chat panel"
echo "   4. Sign in with your Tufts credentials"
echo "   5. Start asking questions!"
echo ""
echo "🔧 Development commands:"
echo "   • To recompile: cd vscode-extension && npm run compile"
echo "   • To package: cd vscode-extension && vsce package"
echo "   • To watch for changes: cd vscode-extension && npm run watch"
echo ""
echo "📚 Make sure the backend API server is running on http://127.0.0.1:5000"
echo "    (Use the webapp-setup-mac.sh script to set up the backend)"
echo ""
echo "🎯 Happy coding with your new CS15 Tutor VSCode extension!" 