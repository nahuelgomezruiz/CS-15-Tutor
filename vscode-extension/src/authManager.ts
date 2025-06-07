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
            // Show progress indicator
            return await vscode.window.withProgress(
                {
                    location: vscode.ProgressLocation.Notification,
                    title: "CS 15 Tutor Authentication",
                    cancellable: true
                },
                async (progress, token) => {
                    progress.report({ message: "Opening authentication page..." });

                    // Generate a login URL from the server
                    const loginUrl = await this.getLoginUrl();
                    if (!loginUrl) {
                        vscode.window.showErrorMessage('Failed to generate login URL');
                        return false;
                    }

                    // Open the authentication URL in the browser
                    await vscode.env.openExternal(vscode.Uri.parse(loginUrl));

                    progress.report({ message: "Waiting for authentication..." });

                    // Extract session ID from the URL
                    const sessionId = this.extractSessionId(loginUrl);
                    if (!sessionId) {
                        vscode.window.showErrorMessage('Invalid session ID');
                        return false;
                    }

                    // Poll for authentication completion
                    const authResult = await this.pollForAuthentication(sessionId, progress, token);
                    
                    if (authResult) {
                        vscode.window.showInformationMessage(`Welcome, ${authResult.utln}! You are now authenticated.`);
                        return true;
                    } else {
                        vscode.window.showErrorMessage('Authentication failed or was cancelled');
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
            const utln = this.getUtln();
            statusBarItem.text = `$(person) CS15: ${utln}`;
            statusBarItem.tooltip = `Authenticated as ${utln}. Click to sign out.`;
            statusBarItem.command = 'cs15-tutor.signOut';
        } else {
            statusBarItem.text = `$(sign-in) CS15: Sign In`;
            statusBarItem.tooltip = 'Click to sign in to CS 15 Tutor';
            statusBarItem.command = 'cs15-tutor.signIn';
        }
        statusBarItem.show();
    }
} 