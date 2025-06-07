import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';

export default function VSCodeAuth() {
    const router = useRouter();
    const [status, setStatus] = useState('loading');
    const [sessionId, setSessionId] = useState('');
    const [userInfo, setUserInfo] = useState(null);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [showDevLogin, setShowDevLogin] = useState(false);
    const [isDevelopmentMode, setIsDevelopmentMode] = useState(false);

    useEffect(() => {
        const { session_id } = router.query;
        if (session_id) {
            setSessionId(session_id);
            // Try automatic authentication first (for production with .htaccess)
            handleAuthentication(session_id);
        }
    }, [router.query]);

    const handleAuthentication = async (sessionId, devCredentials = null) => {
        try {
            setStatus('authenticating');
            
            const headers = {
                'Content-Type': 'application/json',
            };
            
            // Add development credentials if provided
            if (devCredentials) {
                headers['X-Dev-Username'] = devCredentials.username;
                headers['X-Dev-Password'] = devCredentials.password;
            }
            
            // Send POST request to complete VSCode authentication
            const response = await fetch('/api/vscode-auth', {
                method: 'POST',
                headers,
                body: JSON.stringify({
                    session_id: sessionId
                })
            });

            if (response.ok) {
                const data = await response.json();
                setUserInfo(data);
                setStatus('success');
                
                // Auto-close after 3 seconds
                setTimeout(() => {
                    window.close();
                }, 3000);
            } else if (response.status === 401 && !devCredentials) {
                // Check if development mode is available
                const errorData = await response.json();
                if (errorData.development_mode_available) {
                    setIsDevelopmentMode(true);
                    setShowDevLogin(true);
                    setStatus('dev_login');
                } else {
                    setStatus('production_auth_required');
                }
            } else {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Authentication failed');
            }
        } catch (error) {
            console.error('Authentication error:', error);
            if (!showDevLogin && isDevelopmentMode) {
                setShowDevLogin(true);
                setStatus('dev_login');
            } else {
                setStatus('error');
            }
        }
    };

    const handleDevLogin = (e) => {
        e.preventDefault();
        if (username && password) {
            handleAuthentication(sessionId, { username, password });
        }
    };

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100vh',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            backgroundColor: '#f5f5f5',
            padding: '20px'
        }}>
            <div style={{
                backgroundColor: 'white',
                padding: '40px',
                borderRadius: '8px',
                boxShadow: '0 2px 10px rgba(0, 0, 0, 0.1)',
                textAlign: 'center',
                maxWidth: '500px',
                width: '100%'
            }}>
                <h1 style={{ 
                    color: '#333',
                    marginBottom: '20px',
                    fontSize: '24px'
                }}>
                    🔐 CS 15 Tutor Authentication
                </h1>

                {status === 'loading' && (
                    <div>
                        <p style={{ color: '#666', marginBottom: '20px' }}>
                            Initializing authentication...
                        </p>
                        <div style={{ fontSize: '24px' }}>⏳</div>
                    </div>
                )}

                {status === 'production_auth_required' && (
                    <div>
                        <div style={{ fontSize: '48px', marginBottom: '20px' }}>🔒</div>
                        <h2 style={{ color: '#dc3545', marginBottom: '15px' }}>
                            Authentication Required
                        </h2>
                        <p style={{ color: '#666', marginBottom: '20px' }}>
                            This system requires authentication through Tufts LDAP. 
                            Please ensure you're accessing this through the proper web server 
                            with Apache authentication configured.
                        </p>
                        <p style={{ color: '#666', fontSize: '14px', marginBottom: '20px' }}>
                            <strong>For administrators:</strong> To enable development mode, 
                            set the DEVELOPMENT_MODE environment variable to 'true'.
                        </p>
                        <button 
                            onClick={() => window.close()}
                            style={{
                                backgroundColor: '#6c757d',
                                color: 'white',
                                border: 'none',
                                padding: '10px 20px',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '14px'
                            }}
                        >
                            Close Window
                        </button>
                    </div>
                )}

                {status === 'dev_login' && (
                    <div>
                        <div style={{ fontSize: '48px', marginBottom: '20px' }}>🔑</div>
                        <h2 style={{ color: '#007acc', marginBottom: '15px' }}>
                            Development Login
                        </h2>
                        <p style={{ color: '#666', marginBottom: '20px' }}>
                            Enter your Tufts credentials for testing:
                        </p>
                        <form onSubmit={handleDevLogin} style={{ textAlign: 'left' }}>
                            <div style={{ marginBottom: '15px' }}>
                                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '600' }}>
                                    Username (UTLN):
                                </label>
                                <input
                                    type="text"
                                    value={username}
                                    onChange={(e) => setUsername(e.target.value)}
                                    placeholder="e.g. jsmith01"
                                    style={{
                                        width: '100%',
                                        padding: '8px 12px',
                                        border: '1px solid #ddd',
                                        borderRadius: '4px',
                                        fontSize: '14px'
                                    }}
                                    required
                                />
                            </div>
                            <div style={{ marginBottom: '20px' }}>
                                <label style={{ display: 'block', marginBottom: '5px', fontWeight: '600' }}>
                                    Password:
                                </label>
                                <input
                                    type="password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="Enter password"
                                    style={{
                                        width: '100%',
                                        padding: '8px 12px',
                                        border: '1px solid #ddd',
                                        borderRadius: '4px',
                                        fontSize: '14px'
                                    }}
                                    required
                                />
                            </div>
                            <button 
                                type="submit"
                                style={{
                                    width: '100%',
                                    backgroundColor: '#007acc',
                                    color: 'white',
                                    border: 'none',
                                    padding: '12px 20px',
                                    borderRadius: '4px',
                                    cursor: 'pointer',
                                    fontSize: '14px',
                                    fontWeight: '600'
                                }}
                            >
                                Sign In
                            </button>
                        </form>
                    </div>
                )}

                {status === 'authenticating' && (
                    <div>
                        <p style={{ color: '#666', marginBottom: '20px' }}>
                            Authenticating with your Tufts credentials...
                        </p>
                        <div style={{ fontSize: '24px' }}>🔄</div>
                    </div>
                )}

                {status === 'success' && userInfo && (
                    <div>
                        <div style={{ fontSize: '48px', marginBottom: '20px' }}>✅</div>
                        <h2 style={{ color: '#28a745', marginBottom: '15px' }}>
                            Authentication Successful!
                        </h2>
                        <p style={{ color: '#666', marginBottom: '20px' }}>
                            Welcome, <strong>{userInfo.utln}</strong>!
                        </p>
                        <p style={{ color: '#666', fontSize: '14px' }}>
                            You can now return to VS Code. This window will close automatically.
                        </p>
                        <button 
                            onClick={() => window.close()}
                            style={{
                                backgroundColor: '#007acc',
                                color: 'white',
                                border: 'none',
                                padding: '10px 20px',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '14px',
                                marginTop: '15px'
                            }}
                        >
                            Close Window
                        </button>
                    </div>
                )}

                {status === 'error' && (
                    <div>
                        <div style={{ fontSize: '48px', marginBottom: '20px' }}>❌</div>
                        <h2 style={{ color: '#dc3545', marginBottom: '15px' }}>
                            Authentication Failed
                        </h2>
                        <p style={{ color: '#666', marginBottom: '20px' }}>
                            Invalid credentials or you're not enrolled in CS 15. Please try again.
                        </p>
                        <button 
                            onClick={() => {
                                setStatus('dev_login');
                                setUsername('');
                                setPassword('');
                            }}
                            style={{
                                backgroundColor: '#007acc',
                                color: 'white',
                                border: 'none',
                                padding: '10px 20px',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '14px',
                                marginRight: '10px'
                            }}
                        >
                            Try Again
                        </button>
                        <button 
                            onClick={() => window.close()}
                            style={{
                                backgroundColor: '#6c757d',
                                color: 'white',
                                border: 'none',
                                padding: '10px 20px',
                                borderRadius: '4px',
                                cursor: 'pointer',
                                fontSize: '14px'
                            }}
                        >
                            Close Window
                        </button>
                    </div>
                )}

                <div style={{
                    marginTop: '30px',
                    padding: '15px',
                    backgroundColor: '#f8f9fa',
                    borderRadius: '4px',
                    fontSize: '12px',
                    color: '#666'
                }}>
                    <p style={{ margin: 0, marginBottom: '8px' }}>
                        <strong>Note:</strong> This authentication is for the CS 15 Tutor VS Code extension.
                    </p>
                    <p style={{ margin: 0 }}>
                        {isDevelopmentMode ? 
                            'Development mode: Enter any valid Tufts credentials for testing.' :
                            'Your credentials are verified through Tufts LDAP and your session data is anonymized for privacy.'
                        }
                    </p>
                </div>
            </div>
        </div>
    );
} 