import * as vscode from 'vscode';
import * as http from 'http';

export interface AuthToken {
    token: string;
    utln: string;
    expiresAt: Date;
}

export class AuthManager {
    private static readonly TOKEN_KEY = 'cs15-tutor.authToken';
    private static readonly UTLN_KEY = 'cs15-tutor.utln';
    private static readonly EXPIRES_KEY = 'cs15-tutor.tokenExpires';
    private context: vscode.ExtensionContext;
    private apiBaseUrl: string;

    constructor(context: vscode.ExtensionContext, apiBaseUrl: string = 'http://127.0.0.1:5000') {
        this.context = context;
        this.apiBaseUrl = apiBaseUrl;
    }

    /**
     * Check if user is currently authenticated
     */
    public isAuthenticated(): boolean {
        const token = this.getStoredToken();
        if (!token) {
            return false;
        }

        // Check if token is expired
        const now = new Date();
        if (now >= token.expiresAt) {
            this.clearAuthentication();
            return false;
        }

        return true;
    }

    /**
     * Get the current authentication token
     */
    public getAuthToken(): string | null {
        const token = this.getStoredToken();
        return token ? token.token : null;
    }

    /**
     * Get the current user's UTLN
     */
    public getUtln(): string | null {
        const token = this.getStoredToken();
        return token ? token.utln : null;
    }

    /**
     * Initiate the authentication process
     */
    public async authenticate(): Promise<boolean> {
        try {
            // Show username input
            const username = await vscode.window.showInputBox({
                prompt: 'Enter your Tufts EECS username',
                placeHolder: 'e.g., your_eecs_username',
                ignoreFocusOut: true,
                validateInput: (value: string) => {
                    if (!value || value.trim().length === 0) {
                        return 'Username is required';
                    }
                    if (!/^[a-zA-Z][a-zA-Z0-9_]{2,15}$/.test(value.trim())) {
                        return 'Please enter a valid EECS username';
                    }
                    return undefined;
                }
            });

            if (!username) {
                vscode.window.showInformationMessage('Authentication cancelled');
                return false;
            }

            // Show password input
            const password = await vscode.window.showInputBox({
                prompt: 'Enter your Tufts EECS password',
                placeHolder: 'Your EECS password',
                password: true,
                ignoreFocusOut: true,
                validateInput: (value: string) => {
                    if (!value || value.trim().length === 0) {
                        return 'Password is required';
                    }
                    return undefined;
                }
            });

            if (!password) {
                vscode.window.showInformationMessage('Authentication cancelled');
                return false;
            }

            // Show progress indicator for authentication
            return await vscode.window.withProgress(
                {
                    location: vscode.ProgressLocation.Notification,
                    title: "CS 15 Tutor Authentication",
                    cancellable: false
                },
                async (progress) => {
                    progress.report({ message: "Authenticating with Tufts LDAP..." });

                    // Authenticate with backend
                    const authResult = await this.authenticateWithCredentials(username.trim(), password);
                    
                    if (authResult.success && authResult.token) {
                        // Store the token
                        const expiresAt = new Date();
                        expiresAt.setHours(expiresAt.getHours() + 24); // 24 hour expiry

                        const authToken: AuthToken = {
                            token: authResult.token,
                            utln: authResult.username,
                            expiresAt
                        };

                        this.storeToken(authToken);
                        
                        vscode.window.showInformationMessage(`Authentication successful! Welcome, ${authResult.username}`);
                        return true;
                    } else {
                        vscode.window.showErrorMessage(authResult.error || 'Authentication failed');
                        return false;
                    }
                }
            );
        } catch (error) {
            console.error('Authentication error:', error);
            vscode.window.showErrorMessage(`Authentication failed: ${error}`);
            return false;
        }
    }

    /**
     * Clear stored authentication
     */
    public clearAuthentication(): void {
        this.context.globalState.update(AuthManager.TOKEN_KEY, undefined);
        this.context.globalState.update(AuthManager.UTLN_KEY, undefined);
        this.context.globalState.update(AuthManager.EXPIRES_KEY, undefined);
    }

    /**
     * Get stored authentication token
     */
    private getStoredToken(): AuthToken | null {
        const token = this.context.globalState.get<string>(AuthManager.TOKEN_KEY);
        const utln = this.context.globalState.get<string>(AuthManager.UTLN_KEY);
        const expiresAt = this.context.globalState.get<string>(AuthManager.EXPIRES_KEY);

        if (!token || !utln || !expiresAt) {
            return null;
        }

        return {
            token,
            utln,
            expiresAt: new Date(expiresAt)
        };
    }

    /**
     * Store authentication token
     */
    private storeToken(authToken: AuthToken): void {
        this.context.globalState.update(AuthManager.TOKEN_KEY, authToken.token);
        this.context.globalState.update(AuthManager.UTLN_KEY, authToken.utln);
        this.context.globalState.update(AuthManager.EXPIRES_KEY, authToken.expiresAt.toISOString());
    }

    /**
     * Authenticate user with credentials against backend
     */
    private async authenticateWithCredentials(username: string, password: string): Promise<any> {
        return new Promise((resolve) => {
            const data = JSON.stringify({
                username: username,
                password: password
            });

            const options = {
                hostname: '127.0.0.1',
                port: 5000,
                path: '/vscode-direct-auth',
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(data)
                }
            };

            const req = http.request(options, (res) => {
                let responseData = '';
                res.on('data', (chunk) => {
                    responseData += chunk;
                });
                res.on('end', () => {
                    try {
                        const response = JSON.parse(responseData);
                        resolve(response);
                    } catch (error) {
                        resolve({ 
                            success: false, 
                            error: 'Invalid response from server' 
                        });
                    }
                });
            });

            req.on('error', (error) => {
                console.error('Error authenticating with credentials:', error);
                resolve({ 
                    success: false, 
                    error: `Connection error: ${error.message}` 
                });
            });

            req.write(data);
            req.end();
        });
    }

    /**
     * Get login URL from the server
     */
    private async getLoginUrl(): Promise<string | null> {
        return new Promise((resolve) => {
            const options = {
                hostname: '127.0.0.1',
                port: 5000,
                path: '/vscode-auth',
                method: 'GET'
            };

            const req = http.request(options, (res) => {
                let data = '';
                res.on('data', (chunk) => {
                    data += chunk;
                });
                res.on('end', () => {
                    try {
                        const response = JSON.parse(data);
                        if (response.login_url) {
                            // Server provides the complete login URL
                            resolve(response.login_url);
                        } else if (response.session_id) {
                            // Fallback: construct URL from session_id
                            resolve(`${this.apiBaseUrl}/vscode-auth?session_id=${response.session_id}`);
                        } else {
                            console.error('No session_id or login_url in response:', response);
                            resolve(null);
                        }
                    } catch (error) {
                        console.error('Error parsing login URL response:', error);
                        resolve(null);
                    }
                });
            });

            req.on('error', (error) => {
                console.error('Error getting login URL:', error);
                resolve(null);
            });

            req.end();
        });
    }

    /**
     * Extract session ID from login URL
     */
    private extractSessionId(url: string): string | null {
        try {
            const urlObj = new URL(url);
            return urlObj.searchParams.get('session_id');
        } catch (error) {
            return null;
        }
    }

    /**
     * Poll for authentication completion
     */
    private async pollForAuthentication(
        sessionId: string, 
        progress: vscode.Progress<{ message?: string; increment?: number }>,
        cancellationToken: vscode.CancellationToken
    ): Promise<AuthToken | null> {
        const maxAttempts = 60; // 5 minutes (5 second intervals)
        let attempts = 0;

        while (attempts < maxAttempts && !cancellationToken.isCancellationRequested) {
            try {
                const status = await this.checkAuthStatus(sessionId);
                
                if (status.status === 'completed' && status.token && status.utln) {
                    // Authentication successful
                    const expiresAt = new Date();
                    expiresAt.setHours(expiresAt.getHours() + 24); // 24 hour expiry

                    const authToken: AuthToken = {
                        token: status.token,
                        utln: status.utln,
                        expiresAt
                    };

                    this.storeToken(authToken);
                    return authToken;
                }

                if (status.status === 'error') {
                    throw new Error('Authentication failed on server');
                }

                // Update progress
                progress.report({ 
                    message: `Waiting for authentication... (${Math.ceil((maxAttempts - attempts) * 5 / 60)} min remaining)` 
                });

                // Wait 5 seconds before next poll
                await new Promise(resolve => setTimeout(resolve, 5000));
                attempts++;

            } catch (error) {
                console.error('Error polling for authentication:', error);
                throw error;
            }
        }

        if (cancellationToken.isCancellationRequested) {
            throw new Error('Authentication cancelled by user');
        }

        throw new Error('Authentication timeout');
    }

    /**
     * Check authentication status on server
     */
    private async checkAuthStatus(sessionId: string): Promise<any> {
        return new Promise((resolve, reject) => {
            const options = {
                hostname: '127.0.0.1',
                port: 5000,
                path: `/vscode-auth-status?session_id=${encodeURIComponent(sessionId)}`,
                method: 'GET'
            };

            const req = http.request(options, (res) => {
                let data = '';
                res.on('data', (chunk) => {
                    data += chunk;
                });
                res.on('end', () => {
                    try {
                        const response = JSON.parse(data);
                        resolve(response);
                    } catch (error) {
                        reject(new Error('Invalid response from server'));
                    }
                });
            });

            req.on('error', (error) => {
                reject(error);
            });

            req.end();
        });
    }

    /**
     * Show authentication status in status bar
     */
    public updateStatusBar(statusBarItem: vscode.StatusBarItem): void {
        if (this.isAuthenticated()) {
            statusBarItem.text = `CS 15 $(ellipsis)`;
            statusBarItem.tooltip = `CS 15 Tutor - Click to see user options`;
            statusBarItem.command = 'cs15-tutor.showUserMenu';
        } else {
            statusBarItem.text = `$(sign-in) CS15: Sign In`;
            statusBarItem.tooltip = 'Click to sign in to CS 15 Tutor';
            statusBarItem.command = 'cs15-tutor.signIn';
        }
        statusBarItem.show();
    }

    /**
     * Show user menu with username and sign out option
     */
    public async showUserMenu(): Promise<void> {
        if (!this.isAuthenticated()) {
            return;
        }

        const utln = this.getUtln();
        const items = [
            {
                label: `$(person) Signed in as: ${utln}`,
                description: 'Your current authentication status'
            },
            {
                label: `$(sign-out) Sign Out`,
                description: 'Sign out of CS 15 Tutor'
            }
        ];

        const selection = await vscode.window.showQuickPick(items, {
            placeHolder: 'CS 15 Tutor User Options',
            canPickMany: false
        });

        if (selection && selection.label.includes('Sign Out')) {
            const result = await vscode.window.showInformationMessage(
                'Are you sure you want to sign out of CS 15 Tutor?',
                'Sign Out',
                'Cancel'
            );
            
            if (result === 'Sign Out') {
                await this.signOut();
            }
        }
    }

    /**
     * Sign out the current user
     */
    public async signOut(): Promise<void> {
        try {
            this.clearAuthentication();
            vscode.window.showInformationMessage('Successfully signed out of CS 15 Tutor');
        } catch (error) {
            console.error('Error during sign out:', error);
            vscode.window.showErrorMessage('Error signing out');
        }
    }
} 