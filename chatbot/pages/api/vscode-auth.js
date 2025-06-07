export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    try {
        const isDevelopmentMode = process.env.DEVELOPMENT_MODE?.toLowerCase() === 'true';
        
        const headers = {
            'Content-Type': 'application/json',
            // Forward authentication headers from the original request
            ...(req.headers.authorization && { 'Authorization': req.headers.authorization }),
            ...(req.headers.cookie && { 'Cookie': req.headers.cookie }),
            // Forward other relevant headers
            ...(req.headers['x-forwarded-for'] && { 'X-Forwarded-For': req.headers['x-forwarded-for'] }),
            ...(req.headers['user-agent'] && { 'User-Agent': req.headers['user-agent'] }),
            // Forward the REMOTE_USER if it exists (from Apache authentication)
            ...(req.headers['remote-user'] && { 'X-Remote-User': req.headers['remote-user'] }),
        };

        // Handle development credentials only if development mode is enabled
        if (isDevelopmentMode && req.headers['x-dev-username'] && req.headers['x-dev-password']) {
            const username = req.headers['x-dev-username'];
            const password = req.headers['x-dev-password'];
            
            // Simple validation - in a real system this would check against LDAP
            // For development, accept any reasonable username/password combination
            if (username && password && username.length > 2 && password.length > 2) {
                // Set the development user header
                headers['X-Remote-User'] = username;
                headers['X-Development-Mode'] = 'true';
            } else {
                return res.status(401).json({ 
                    error: 'Invalid credentials',
                    message: 'Username and password must be at least 3 characters',
                    development_mode_available: isDevelopmentMode
                });
            }
        }

        // Forward the request to the Python API server
        const response = await fetch('http://127.0.0.1:5000/vscode-auth', {
            method: 'POST',
            headers,
            body: JSON.stringify(req.body)
        });

        const data = await response.json();
        
        // Add development mode availability to error responses
        if (!response.ok && !data.development_mode_available) {
            data.development_mode_available = isDevelopmentMode;
        }
        
        // Forward the response status and data
        res.status(response.status).json(data);
        
    } catch (error) {
        console.error('Error proxying VSCode auth request:', error);
        res.status(500).json({ 
            error: 'Internal server error',
            message: 'Failed to process authentication request',
            development_mode_available: process.env.DEVELOPMENT_MODE?.toLowerCase() === 'true'
        });
    }
} 