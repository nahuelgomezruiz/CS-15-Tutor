# VSCode Extension Username-Only Authentication

## Overview

The VSCode extension now uses a simple username-only authentication system with a configurable list of allowed users, while the web app continues to use LDAP authentication. This gives you control over who can access the VSCode extension.

## How It Works

1. **VSCode Extension**: Only requires a username (no password needed)
2. **Web App**: Continues to use LDAP authentication (unchanged)
3. **Backend**: Checks username against allowed list and validates format
4. **Access Control**: Only usernames in `allowed_vscode_users.json` can authenticate

## Username Requirements

- Must be 3-16 characters long
- Must start with a letter
- Can contain letters, numbers, and underscores
- Must be in the allowed users list
- Examples: `testuser`, `demo_user`, `student123`

## Managing Allowed Users

### Using the Management Script

Run the management script to easily add/remove allowed users:

```bash
cd responses-api-server
python manage_allowed_users.py
```

**Available options:**
1. List allowed users
2. Add allowed user
3. Remove allowed user
4. Clear all users
5. Reset to default
6. Exit

### Manual Configuration

Edit `responses-api-server/allowed_vscode_users.json`:

```json
{
  "allowed_users": [
    "testuser",
    "demo_user", 
    "vhenao01",
    "agomez08"
  ],
  "description": "List of usernames allowed to authenticate with the VSCode extension"
}
```

### Default Allowed Users

If no configuration file exists, these users are allowed by default:
- `testuser`
- `demo_user`
- `student123`

## Using the VSCode Extension

1. Install the VSCode extension
2. Click the "Sign In" button in the status bar
3. Enter a username from the allowed list (no password required)
4. The extension will authenticate and you can start using the CS 15 Tutor

## Security Notes

- **Access Control**: Only usernames in the allowed list can authenticate
- **For Development Only**: This username-only authentication is intended for development and testing
- **No Password Required**: Anyone with an allowed username can authenticate
- **Production**: In production, you should implement proper authentication
- **Web App Unchanged**: The web app still requires proper LDAP authentication

## Backend Changes

The backend now:
1. Detects VSCode extension requests by checking for `X-Development-Mode: true` header
2. Checks username against allowed users list
3. Validates username format requirements
4. Allows username-only authentication for VSCode requests
5. Continues to require username + password for web app requests
6. Creates JWT tokens for authenticated VSCode users

## Files Modified

- `vscode-extension/src/authManager.ts` - Updated to only ask for username
- `responses-api-server/index.py` - Added allowed users checking logic
- `responses-api-server/allowed_vscode_users.json` - Configuration file for allowed users
- `responses-api-server/manage_allowed_users.py` - Management script for allowed users
- `VSCODE_USERNAME_AUTH.md` - This documentation file

## Troubleshooting

### Authentication Fails
- Check that the username is in the allowed users list
- Verify the username meets the format requirements
- Ensure the backend server is running
- Check that the `allowed_vscode_users.json` file exists and is readable

### Extension Won't Connect
- Check that the API base URL is correct in the extension
- Ensure the backend server is accessible
- Restart VSCode if needed

### Adding New Users
- Use the management script: `python manage_allowed_users.py`
- Or manually edit `allowed_vscode_users.json`
- Restart the backend server after changes

## Quick Test

To test the system:
1. Start the backend server
2. Install the VSCode extension
3. Click "Sign In" and enter `testuser` (or any user from allowed list)
4. You should be authenticated immediately

## Adding Your Own Users

1. Run the management script:
   ```bash
   cd responses-api-server
   python manage_allowed_users.py
   ```

2. Choose option 2 "Add allowed user"

3. Enter your desired username (e.g., `myusername`)

4. The user will be added to the allowed list

5. You can now authenticate with that username in the VSCode extension 