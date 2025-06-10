# CS15 Tutor Development Setup

This repository contains automated setup scripts to quickly get the CS15 Tutor system running on your local machine. The system consists of two main components:

1. **Web Application** (Frontend: Next.js React + Backend: Flask API)
2. **VSCode Extension** (TypeScript)

## 📋 Prerequisites

### For All Platforms:
- **Node.js** (v18.x or higher) - [Download here](https://nodejs.org/)
- **Python** (v3.8 or higher) - [Download here](https://python.org/)
- **Visual Studio Code** (for VSCode extension) - [Download here](https://code.visualstudio.com/)

### Platform-Specific Notes:

#### macOS:
- Ensure you have Xcode Command Line Tools installed: `xcode-select --install`
- Node.js and Python can also be installed via Homebrew

#### Windows:
- During Python installation, make sure to check "Add Python to PATH"
- During Node.js installation, ensure npm is included
- During VSCode installation, check "Add to PATH" option

## 🚀 Quick Setup

### Option 1: Web Application Setup

#### macOS:
```bash
# Make script executable (if needed)
chmod +x webapp-setup-mac.sh

# Run the setup script
./webapp-setup-mac.sh
```

#### Windows:
```cmd
# Right-click and "Run as Administrator" (recommended)
webapp-setup-windows.bat

# Or double-click the file in File Explorer
```

### Option 2: VSCode Extension Setup

#### macOS:
```bash
# Make script executable (if needed)
chmod +x vscode-extension-setup-mac.sh

# Run the setup script
./vscode-extension-setup-mac.sh
```

#### Windows:
```cmd
# Right-click and "Run as Administrator" (recommended)
vscode-extension-setup-windows.bat

# Or double-click the file in File Explorer
```

## 🔧 What Each Setup Script Does

### Web Application Setup (`webapp-setup-*.sh/.bat`):

1. **Verifies Prerequisites:**
   - Checks for Node.js, npm, Python, and pip
   - Validates project directory structure

2. **Frontend Setup (Next.js):**
   - Installs dependencies (`npm install`)
   - **Creates `.env.local` with `DEVELOPMENT_MODE=true`**
   - Configures for development mode (skips production build)

3. **Backend Setup (Flask API):**
   - Creates Python virtual environment
   - Installs Python dependencies from `requirements.txt`
   - **Configures Flask development mode** (`FLASK_DEBUG=True`, `FLASK_ENV=development`, `DEVELOPMENT_MODE=true`)
   - Verifies `system_prompt.txt` exists

4. **Provides Next Steps:**
   - Instructions to start both servers
   - Development workflow guidance

### VSCode Extension Setup (`vscode-extension-setup-*.sh/.bat`):

1. **Verifies Prerequisites:**
   - Checks for Node.js, npm, and VSCode
   - Validates extension directory structure

2. **Extension Development Setup:**
   - Installs TypeScript dependencies
   - Installs `vsce` (VSCode Extension Manager)
   - Compiles TypeScript to JavaScript

3. **Extension Packaging & Installation:**
   - Packages extension into `.vsix` file
   - Automatically installs extension in VSCode
   - Provides manual installation instructions as fallback

## 🎯 After Setup - Starting the Systems

### Web Application:

1. **Start Backend (Terminal 1) - Development Mode Pre-configured:**
   ```bash
   # macOS/Linux:
   cd responses-api-server
   source venv/bin/activate  # Sets FLASK_DEBUG=True, FLASK_ENV=development & DEVELOPMENT_MODE=true
   python index.py
   
   # Windows:
   cd responses-api-server
   venv\Scripts\activate.bat  # Sets FLASK_DEBUG=True, FLASK_ENV=development & DEVELOPMENT_MODE=true
   python index.py
   ```

2. **Start Frontend (Terminal 2) - Development Mode:**
   ```bash
   cd web-app
   npm run dev  # Hot reload enabled, DEVELOPMENT_MODE=true set via .env.local
   ```

3. **Access Application:**
   - Frontend: http://localhost:3000 (with hot reload)
   - Backend API: http://127.0.0.1:5000 (with debug mode)

### VSCode Extension:

1. **Open/Restart VSCode**
2. **Find CS15 Tutor Icon** in the Activity Bar (left sidebar)
3. **Click to Open** the chat panel
4. **Sign In** with Tufts credentials
5. **Start Chatting!**

## 🛠️ Development Workflow

### Web Application Development:

```bash
# Frontend development (with hot reload) - Development mode ready!
cd web-app
npm run dev

# Backend development - Development mode pre-configured!
cd responses-api-server
source venv/bin/activate  # Windows: venv\Scripts\activate.bat
# Virtual environment now automatically sets:
# - FLASK_DEBUG=True (enables auto-reload on code changes)
# - FLASK_ENV=development (development-specific settings)
# - DEVELOPMENT_MODE=true (enables your custom development features)
python index.py
```

### VSCode Extension Development:

```bash
# Watch mode for automatic TypeScript compilation
cd vscode-extension
npm run watch

# Manual compilation
npm run compile

# Repackage and reinstall after changes
vsce package
code --install-extension cs15-tutor-*.vsix
```

## ⚠️ Troubleshooting

### Common Issues:

1. **"Command not found" errors:**
   - Ensure Node.js, Python, and VSCode are in your system PATH
   - Restart your terminal/command prompt after installation

2. **Permission denied (macOS):**
   ```bash
   chmod +x *.sh
   ```

3. **npm install fails:**
   - Clear npm cache: `npm cache clean --force`
   - Delete `node_modules` and retry: `rm -rf node_modules && npm install`

4. **Python virtual environment issues:**
   - Ensure Python 3 is installed: `python3 --version`
   - Update pip: `pip install --upgrade pip`

5. **VSCode extension not appearing:**
   - Restart VSCode completely
   - Check Extensions view (Ctrl/Cmd+Shift+X) for "CS15 Tutor"
   - Try manual installation via "Install from VSIX"

### Platform-Specific Issues:

#### macOS:
- Install Xcode Command Line Tools if compilation fails
- Use `python3` and `pip3` explicitly if `python` command not found

#### Windows:
- Run scripts as Administrator if permission issues occur
- Ensure Python was installed with "Add to PATH" option
- Use PowerShell or Command Prompt, not PowerShell ISE

## 📁 Project Structure

```
CS-15-Tutor/
├── web-app/                    # Next.js frontend
├── responses-api-server/       # Flask backend
├── vscode-extension/          # VSCode extension
├── webapp-setup-mac.sh        # macOS webapp setup
├── webapp-setup-windows.bat   # Windows webapp setup
├── vscode-extension-setup-mac.sh     # macOS extension setup
├── vscode-extension-setup-windows.bat # Windows extension setup
└── SETUP-README.md           # This file
```

## 🔐 Authentication & Configuration

After running the setup scripts, you'll need to configure:

1. **Authentication System**: Set up your Tufts LDAP authentication
2. **LLM Proxy Service**: Configure the `llmproxy` service for AI responses
3. **System Prompt**: Ensure `system_prompt.txt` is properly configured
4. **Environment Variables**: Set up any required API keys or configuration

## 🎉 You're Ready!

Once setup is complete, you'll have:
- ✅ A fully functional web application
- ✅ A VSCode extension installed and ready to use
- ✅ Development environments configured with debug mode enabled
- ✅ All dependencies installed
- ✅ **Flask auto-reload** enabled (backend restarts on code changes)
- ✅ **Next.js hot reload** ready (frontend updates instantly on save)

**Happy coding with the CS15 Tutor! 🚀**

---

*For issues or questions, please refer to the main project documentation or contact the development team.* 