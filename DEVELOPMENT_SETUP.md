# CS 15 Tutor System - Development Setup

## Environment Setup

### Prerequisites
- Python 3.8+
- Node.js 16+
- Apache web server (for production authentication)
- SQLite (included with Python)

### Installation

#### 1. Backend API Server
```bash
cd responses-api-server
pip install -r requirements.txt
```

#### 2. Web Application
```bash
cd web-app
npm install
```

### Running the System

#### Backend (API Server)
```bash
cd responses-api-server
python index.py
```
The API server runs on `http://127.0.0.1:5000`

#### Frontend (Web App)
```bash
cd web-app
npm run dev
```
The web app runs on `http://localhost:3000`

## 🔧 **Development vs Production Mode**

### **Environment Variable Control**

The system uses the `DEVELOPMENT_MODE` environment variable to control authentication behavior:

#### **Development Mode (Testing/Local Development)**
```bash
# Linux/Mac
export DEVELOPMENT_MODE=true

# Windows PowerShell
$env:DEVELOPMENT_MODE = "true"

# Windows Command Prompt
set DEVELOPMENT_MODE=true

# Then start your servers
python index.py  # Backend
npm run dev      # Frontend
```

**What happens in development mode:**
- ✅ Shows development login form in VSCode auth
- ✅ Accepts any reasonable UTLN/password combination
- ✅ Bypasses Apache .htaccess authentication
- ✅ Logs indicate "Development mode" in console
- ⚠️ **Should NEVER be used in production**

#### **Production Mode (Real Authentication)**
```bash
# Linux/Mac
unset DEVELOPMENT_MODE
# Or explicitly set to false
export DEVELOPMENT_MODE=false

# Windows PowerShell
Remove-Item env:DEVELOPMENT_MODE
# Or explicitly set to false
$env:DEVELOPMENT_MODE = "false"

# Windows Command Prompt
set DEVELOPMENT_MODE=

# Then start your servers
python index.py  # Backend
npm run dev      # Frontend
```

**What happens in production mode:**
- 🔒 Requires real Apache .htaccess + LDAP authentication
- 🔒 Only shows "Authentication Required" message on auth failure
- 🔒 Checks `.htgrp` file for authorized CS 15 students
- 🔒 Validates against Tufts LDAP through Apache

### **Quick Mode Switching**

#### **Enable Development Mode**
```bash
# Linux/Mac
cd responses-api-server
DEVELOPMENT_MODE=true python index.py

# Windows PowerShell
cd responses-api-server
$env:DEVELOPMENT_MODE = "true"
python index.py

# Frontend (new terminal)
cd web-app
npm run dev
```

#### **Enable Production Mode**
```bash
# Linux/Mac
cd responses-api-server
python index.py  # (no DEVELOPMENT_MODE set)

# Windows PowerShell
cd responses-api-server
Remove-Item env:DEVELOPMENT_MODE -ErrorAction SilentlyContinue
python index.py

# Frontend (new terminal)
cd web-app
npm run dev      # (no DEVELOPMENT_MODE set)
```

### **Mode Indicators**

#### **How to tell which mode you're in:**

1. **VSCode Extension Authentication:**
   - **Development:** Shows username/password form
   - **Production:** Shows "Authentication Required" message

2. **Backend Logs:**
   - **Development:** `Development mode: allowing user username`
   - **Production:** `User username not authorized for CS 15 tutor`

3. **API Responses:**
   - Include `development_mode_available: true/false` field

### **Security Notes**

⚠️ **IMPORTANT:** 
- Development mode should **NEVER** be enabled in production
- It bypasses all authentication security
- Only use for local testing and development
- Production deployments should use Apache .htaccess authentication

## Database Configuration

The system uses SQLite by default. Database file: `responses-api-server/cs15_tutor.db`

Initialize the database:
```bash
cd responses-api-server
python database.py
```

## VSCode Extension Development

### Building the Extension
```bash
cd vscode-extension
npm install
npm run compile
```

### Testing the Extension
1. Open VSCode
2. Go to Run and Debug (Ctrl+Shift+D)
3. Select "Launch Extension"
4. Press F5 to launch a new Extension Development Host window

## Authentication Flow

### Web App Authentication
1. User accesses web app
2. Apache .htaccess redirects to LDAP login
3. REMOTE_USER environment variable set
4. Backend extracts UTLN and creates anonymous ID

### VSCode Extension Authentication
1. Extension requests login URL from backend
2. Opens browser to authentication page
3. User authenticates (production) or enters dev credentials
4. Backend creates JWT token
5. Token stored in VSCode extension
6. Token included in subsequent API requests

## Logging and Analytics

All user interactions are logged with:
- Anonymous user IDs (hashed UTLNs)
- Conversation tracking
- Platform identification (web/vscode)
- Query/response metadata
- User engagement analytics

See `LOGGING_AND_AUTH_SYSTEM.md` for detailed information.

## Troubleshooting

### Common Issues

1. **"Failed to generate login URL"**
   - Ensure backend server is running on port 5000
   - Check that `/vscode-auth` endpoint is accessible

2. **"Authentication Required" in VSCode**
   - Set `DEVELOPMENT_MODE=true` for testing
   - Ensure Apache authentication is configured for production

3. **Web app compilation hanging**
   - Kill Node.js processes: `killall node` (Linux/Mac) or Task Manager (Windows)
   - Delete cache: `rm -rf .next/ node_modules/ package-lock.json`
   - Reinstall: `npm install`

4. **Database errors**
   - Ensure write permissions to `responses-api-server/` directory
   - Initialize database: `python database.py`

### Environment Variables

| Variable | Purpose | Values | Default |
|----------|---------|--------|---------|
| `DEVELOPMENT_MODE` | Enable/disable dev authentication | `true`/`false` | `false` |
| `JWT_SECRET` | VSCode extension token signing | Any string | `your-secret-key-change-this-in-production` |
| `CS15_AUTHORIZED_USERS` | Fallback user list | Comma-separated UTLNs | None |

## Production Deployment

### Apache Configuration
See `web-app/.htaccess` for authentication setup.

### Environment Setup
```bash
# Production environment
DEVELOPMENT_MODE=false
JWT_SECRET=your-secure-random-secret-key
```

### Security Checklist
- [ ] DEVELOPMENT_MODE is false
- [ ] JWT_SECRET is changed from default
- [ ] Apache LDAP authentication configured
- [ ] .htgrp file contains authorized students
- [ ] HTTPS enabled
- [ ] Database has proper file permissions 