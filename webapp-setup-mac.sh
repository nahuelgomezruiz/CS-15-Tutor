#!/bin/bash

# CS15 Tutor Web App Setup Script for macOS
# This script sets up both the frontend (Next.js) and backend (Flask API)

echo "🚀 Setting up CS15 Tutor Web App for macOS..."
echo "================================================"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if directory exists
check_directory() {
    if [ ! -d "$1" ]; then
        echo "❌ Error: Directory $1 not found!"
        echo "Please make sure you're running this script from the CS-15-Tutor root directory."
        exit 1
    fi
}

# Check if we're in the right directory
check_directory "web-app"
check_directory "responses-api-server"

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

# Check for Python
echo "🔍 Checking for Python..."
if ! command_exists python3; then
    echo "❌ Python 3 is not installed!"
    echo "Please install Python 3 from https://python.org/"
    echo "Recommended version: 3.8 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✅ Python found: $PYTHON_VERSION"

# Check for pip
if ! command_exists pip3; then
    echo "❌ pip3 is not installed!"
    echo "pip3 should come with Python 3. Please reinstall Python."
    exit 1
fi

PIP_VERSION=$(pip3 --version)
echo "✅ pip3 found: $PIP_VERSION"

echo ""
echo "🎯 Starting setup process..."
echo "=============================="

# Setup Frontend (Next.js Web App)
echo ""
echo "📦 Setting up Frontend (Next.js)..."
cd web-app

echo "   Installing frontend dependencies..."
if npm install; then
    echo "✅ Frontend dependencies installed successfully!"
else
    echo "❌ Failed to install frontend dependencies!"
    exit 1
fi

echo "   Setting up frontend for development mode..."
echo "   Creating .env.local file for development environment..."
echo "DEVELOPMENT_MODE=true" > .env.local
echo "   (Skipping production build - will use 'npm run dev' for development)"
echo "✅ Frontend configured for development mode!"

cd ..

# Setup Backend (Flask API)
echo ""
echo "🐍 Setting up Backend (Flask API)..."
cd responses-api-server

echo "   Creating Python virtual environment..."
if python3 -m venv venv; then
    echo "✅ Virtual environment created!"
else
    echo "❌ Failed to create virtual environment!"
    exit 1
fi

echo "   Activating virtual environment..."
source venv/bin/activate

echo "   Installing backend dependencies..."
if pip install -r requirements.txt; then
    echo "✅ Backend dependencies installed successfully!"
else
    echo "❌ Failed to install backend dependencies!"
    deactivate
    exit 1
fi

echo "   Configuring Flask for development mode..."
echo "export FLASK_ENV=development" >> venv/bin/activate
echo "export FLASK_DEBUG=True" >> venv/bin/activate
echo "export DEVELOPMENT_MODE=true" >> venv/bin/activate
echo "export PYTHONPATH=\$PYTHONPATH:\$(pwd)" >> venv/bin/activate
echo "✅ Flask development environment configured!"

# Check if system_prompt.txt exists
if [ ! -f "system_prompt.txt" ]; then
    echo "⚠️  Warning: system_prompt.txt not found!"
    echo "   The API server requires this file to run properly."
    echo "   Please make sure system_prompt.txt exists in the responses-api-server directory."
fi

deactivate
cd ..

echo ""
echo "🎉 Setup completed successfully!"
echo "================================"
echo ""
echo "🚀 To start the development servers:"
echo ""
echo "1. Start the Backend (Flask API) in DEVELOPMENT MODE:"
echo "   cd responses-api-server"
echo "   source venv/bin/activate  # Sets FLASK_DEBUG=True, FLASK_ENV=development & DEVELOPMENT_MODE=true"
echo "   python index.py"
echo "   (Server will run on http://127.0.0.1:5000 with debug mode enabled)"
echo ""
echo "2. In a new terminal, start the Frontend (Next.js) in DEVELOPMENT MODE:"
echo "   cd web-app"
echo "   npm run dev  # Hot reload enabled for development"
echo "   (Server will run on http://localhost:3000 with hot reload)"
echo ""
echo "📚 Make sure to:"
echo "   - Configure your authentication system"
echo "   - Set up the llmproxy service"
echo "   - Ensure system_prompt.txt is properly configured"
echo ""
echo "🎯 Happy coding! The CS15 Tutor is ready for development!" 