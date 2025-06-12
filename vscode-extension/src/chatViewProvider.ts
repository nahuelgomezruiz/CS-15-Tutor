import * as vscode from 'vscode';
import * as http from 'http';
import { AuthManager } from './authManager';

export class ChatViewProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'cs15-tutor.chatView';
    private _view?: vscode.WebviewView;
    private authManager: AuthManager;

    constructor(
        private readonly _extensionUri: vscode.Uri,
        authManager: AuthManager
    ) {
        this.authManager = authManager;
    }

    public resolveWebviewView(
        webviewView: vscode.WebviewView,
        context: vscode.WebviewViewResolveContext,
        _token: vscode.CancellationToken,
    ) {
        this._view = webviewView;

        webviewView.webview.options = {
            enableScripts: true,
            localResourceRoots: [this._extensionUri]
        };

        webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);

        // Handle messages from the webview
        webviewView.webview.onDidReceiveMessage(async data => {
            console.log('Extension received message from webview:', data);
            switch (data.type) {
                case 'sendMessage':
                    {
                        // Check authentication first
                        if (!this.authManager.isAuthenticated()) {
                            webviewView.webview.postMessage({ 
                                type: 'authRequired',
                                message: 'Please sign in with your Tufts credentials to use the CS 15 Tutor.'
                            });
                            return;
                        }

                        try {
                            console.log('Sending message to API:', data.message);
                            const response = await this._sendMessageToAPI(data.message, data.conversationId);
                            console.log('API response received:', response);
                            webviewView.webview.postMessage({ 
                                type: 'response', 
                                ...response 
                            });
                        } catch (error) {
                            console.error('Error sending message to API:', error);
                            webviewView.webview.postMessage({ 
                                type: 'response', 
                                error: 'Error generating answer. Please try again.' 
                            });
                        }
                        break;
                    }
                case 'requestAuth':
                    {
                        // Trigger authentication flow
                        vscode.commands.executeCommand('cs15-tutor.signIn');
                        break;
                    }
                case 'getAuthStatus':
                    {
                        // Send current auth status to webview
                        webviewView.webview.postMessage({
                            type: 'authStatus',
                            isAuthenticated: this.authManager.isAuthenticated(),
                            utln: this.authManager.getUtln()
                        });
                        break;
                    }
                case 'getHealthStatus':
                    {
                        // Fetch and send health status to webview
                        if (this.authManager.isAuthenticated()) {
                            try {
                                const healthStatus = await this._fetchHealthStatus();
                                webviewView.webview.postMessage({
                                    type: 'healthStatus',
                                    ...healthStatus
                                });
                            } catch (error) {
                                console.error('Error fetching health status:', error);
                            }
                        }
                        break;
                    }
            }
        });
    }

    public refresh(): void {
        if (this._view) {
            this._view.webview.html = this._getHtmlForWebview(this._view.webview);
        }
    }

    private _sendMessageToAPI(message: string, conversationId: string): Promise<any> {
        return new Promise((resolve, reject) => {
            const postData = JSON.stringify({ message, conversationId });
            
            // Get auth token
            const authToken = this.authManager.getAuthToken();
            if (!authToken) {
                reject(new Error('Authentication required'));
                return;
            }
            
            const options = {
                hostname: '127.0.0.1',
                port: 5000,
                path: '/api/stream',
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(postData),
                    'Authorization': `Bearer ${authToken}`
                }
            };

            const req = http.request(options, (res) => {
                let buffer = '';
                
                res.on('data', (chunk) => {
                    buffer += chunk.toString();
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || '';

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const jsonStr = line.slice(6);
                            if (jsonStr.trim()) {
                                try {
                                    const event = JSON.parse(jsonStr);
                                    
                                    if (event.status === 'loading') {
                                        this._view?.webview.postMessage({ 
                                            type: 'status', 
                                            status: 'Looking at course content...' 
                                        });
                                    } else if (event.status === 'thinking') {
                                        this._view?.webview.postMessage({ 
                                            type: 'status', 
                                            status: 'Thinking...' 
                                        });
                                    } else if (event.status === 'complete') {
                                        resolve({
                                            response: event.response,
                                            rag_context: event.rag_context,
                                            conversation_id: event.conversation_id,
                                            user_info: event.user_info,
                                            health_status: event.health_status
                                        });
                                    } else if (event.status === 'error') {
                                        if (event.error.includes('Authentication required') || 
                                            event.error.includes('Access denied')) {
                                            // Authentication failed - clear local auth and prompt re-auth
                                            this.authManager.clearAuthentication();
                                            this._view?.webview.postMessage({
                                                type: 'authRequired',
                                                message: event.error
                                            });
                                            reject(new Error(event.error));
                                        } else {
                                            reject(new Error(event.error || 'Unknown error'));
                                        }
                                    }
                                } catch (e) {
                                    console.error('Error parsing SSE data:', e);
                                }
                            }
                        }
                    }
                });

                res.on('end', () => {
                    reject(new Error('Stream ended without complete status'));
                });
            });

            req.on('error', (e) => {
                console.error('Error:', e);
                resolve({ error: 'Error generating answer. Please try again.' });
            });

            req.write(postData);
            req.end();
        });
    }

    private _fetchHealthStatus(): Promise<any> {
        return new Promise((resolve, reject) => {
            const authToken = this.authManager.getAuthToken();
            if (!authToken) {
                reject(new Error('Authentication required'));
                return;
            }
            
            const options = {
                hostname: '127.0.0.1',
                port: 5000,
                path: '/health-status',
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${authToken}`
                }
            };

            const req = http.request(options, (res) => {
                let data = '';
                
                res.on('data', (chunk) => {
                    data += chunk;
                });

                res.on('end', () => {
                    try {
                        const healthStatus = JSON.parse(data);
                        resolve(healthStatus);
                    } catch (e) {
                        reject(new Error('Failed to parse health status'));
                    }
                });
            });

            req.on('error', (e) => {
                reject(e);
            });

            req.end();
        });
    }

    private _getHtmlForWebview(webview: vscode.Webview) {
        const isAuthenticated = this.authManager.isAuthenticated();
        const utln = this.authManager.getUtln();

        return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CS15 Tutor</title>
    <style>
        * {
            box-sizing: border-box;
        }
        
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            height: 100vh;
            overflow: hidden;
            background-color: var(--vscode-editor-background);
            color: var(--vscode-editor-foreground);
        }
        
        .chat-container {
            display: flex;
            flex-direction: column;
            height: 100vh;
            padding: 12px;
            overflow: hidden;
        }

        .auth-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            padding: 20px;
            text-align: center;
            gap: 12px;
        }

        .auth-container h2 {
            color: var(--vscode-foreground);
            margin: 0;
            font-size: 18px;
            font-weight: 600;
        }

        .auth-container p {
            color: var(--vscode-descriptionForeground);
            margin: 0;
            line-height: 1.4;
            max-width: 280px;
        }

        .auth-button {
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-size: 14px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-top: 12px;
        }

        .auth-button:hover {
            background-color: var(--vscode-button-hoverBackground);
        }


        
        .messages-container {
            flex: 1;
            overflow-y: auto;
            overflow-x: hidden;
            margin-bottom: 12px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            min-height: 0;
        }
        
        .message {
            display: flex;
            margin-bottom: 8px;
            flex-shrink: 0;
        }
        
        .message.user {
            justify-content: flex-end;
        }
        
        .message.bot {
            justify-content: flex-start;
        }
        
        .message-bubble {
            max-width: 80%;
            padding: 8px 12px;
            border-radius: 12px;
            font-size: 13px;
            line-height: 1.4;
            word-wrap: break-word;
        }
        
        .message.user .message-bubble {
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border-bottom-right-radius: 4px;
        }
        
        .message.bot .message-bubble {
            background-color: var(--vscode-editor-inactiveSelectionBackground);
            color: var(--vscode-editor-foreground);
            border-bottom-left-radius: 4px;
        }
        
        .message.bot .message-bubble.loading {
            font-style: italic;
            opacity: 0.8;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        /* Spinning loader animation - matches web app style */
        .spinner {
            width: 16px;
            height: 16px;
            border: 2px solid transparent;
            border-bottom: 2px solid var(--vscode-descriptionForeground);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            flex-shrink: 0;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .input-container {
            flex-shrink: 0;
            display: flex;
            gap: 8px;
            padding: 8px;
            background-color: var(--vscode-input-background);
            border-radius: 6px;
            border: 1px solid var(--vscode-input-border);
            margin-top: auto;
        }
        
        .chat-input {
            flex: 1;
            background: transparent;
            border: none;
            color: var(--vscode-input-foreground);
            font-size: 13px;
            padding: 4px;
            outline: none;
            font-family: inherit;
            resize: none;
            min-height: 20px;
            max-height: 100px;
            overflow-y: hidden;
            line-height: 1.4;
        }
        
        .send-button {
            background-color: var(--vscode-button-background);
            color: var(--vscode-button-foreground);
            border: none;
            border-radius: 4px;
            padding: 4px 12px;
            font-size: 13px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }
        
        .send-button:hover {
            background-color: var(--vscode-button-hoverBackground);
        }
        
        .send-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        /* Code block styling */
        pre {
            background-color: var(--vscode-textCodeBlock-background);
            padding: 8px;
            border-radius: 4px;
            overflow-x: auto;
            font-size: 12px;
            font-family: var(--vscode-editor-font-family);
            margin: 8px 0;
        }
        
        code {
            background-color: var(--vscode-textCodeBlock-background);
            padding: 2px 4px;
            border-radius: 3px;
            font-size: 12px;
            font-family: var(--vscode-editor-font-family);
        }
        
        /* Markdown styling */
        .message-bubble p {
            margin: 0 0 8px 0;
        }
        
        .message-bubble p:last-child {
            margin-bottom: 0;
        }
        
        .message-bubble ul, .message-bubble ol {
            margin: 8px 0;
            padding-left: 20px;
        }
        
        .message-bubble li {
            margin: 4px 0;
        }
        
        .message-bubble strong {
            font-weight: 600;
        }
        
        .message-bubble em {
            font-style: italic;
        }
        
        .message-bubble pre {
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        .message-bubble pre code {
            background: none;
            padding: 0;
            font-size: inherit;
        }
        
        /* Health bar styles */
        .health-bar-container {
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 8px;
        }
        
        .health-bar-wrapper {
            width: 100%;
            max-width: 200px;
        }
        
        .health-bar {
            width: 100%;
            height: 8px;
            background-color: var(--vscode-input-background);
            border-radius: 4px;
            overflow: hidden;
            position: relative;
        }
        
        .health-bar-fill {
            height: 100%;
            transition: width 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        
        .health-bar-fill.high {
            background-color: var(--vscode-testing-iconPassed);
        }
        
        .health-bar-fill.medium {
            background-color: var(--vscode-editorWarning-foreground);
        }
        
        .health-bar-fill.low {
            background-color: var(--vscode-testing-iconFailed);
        }
        
        .health-bar-gradient {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(to right, transparent, rgba(255, 255, 255, 0.2));
        }
        
        .health-warning {
            margin-top: 4px;
            font-size: 9px;
            color: var(--vscode-testing-iconFailed);
            text-align: center;
            opacity: 0.8;
        }
    </style>
</head>
<body>
    ${isAuthenticated ? `
    <div class="chat-container">
        <div id="healthBarContainer" class="health-bar-container" style="display: none;">
            <div class="health-bar-wrapper">
                <div class="health-bar">
                    <div class="health-bar-fill" id="healthBarFill" style="width: 100%;">
                        <div class="health-bar-gradient"></div>
                    </div>
                </div>
                <div class="health-warning" id="healthWarning" style="display: none;">
                    Out of queries. Please wait.
                </div>
            </div>
        </div>
        
        <div class="messages-container" id="messages">
            <div class="message bot">
                <div class="message-bubble">
                    Hi! This is an experimental AI tutor for CS 15. Responses are logged. Email alfredo.gomez_ruiz@tufts.edu for any errors.
                </div>
            </div>
        </div>
        
        <form class="input-container" id="chatForm" onsubmit="return false;">
            <textarea 
                class="chat-input" 
                id="chatInput" 
                placeholder="Ask a question"
                rows="1"
            ></textarea>
            <button type="button" class="send-button" id="sendButton">Send</button>
        </form>
    </div>
    ` : `
    <div class="auth-container">
        <h2>CS 15 Tutor</h2>
        <p>Please sign in with your Tufts EECS credentials to access the CS 15 AI tutor.</p>
        <button class="auth-button" onclick="requestAuth()">
            Sign In
        </button>
    </div>
    `}

    <script>
        const vscode = acquireVsCodeApi();
        let conversationId = generateUUID();
        let isLoading = false;
        const isAuthenticated = ${isAuthenticated};
        let healthStatus = null;
        let healthTimerInterval = null;

        function generateUUID() {
            return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                const r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
            });
        }

        function requestAuth() {
            vscode.postMessage({
                type: 'requestAuth'
            });
        }
        
        function updateHealthBar(status) {
            if (!status) return;
            
            healthStatus = status;
            const container = document.getElementById('healthBarContainer');
            const fillEl = document.getElementById('healthBarFill');
            const warningEl = document.getElementById('healthWarning');
            
            if (container) {
                container.style.display = 'flex';
            }
            
            if (fillEl) {
                const percentage = (status.current_points / status.max_points) * 100;
                fillEl.style.width = percentage + '%';
                
                // Update color based on percentage
                fillEl.className = 'health-bar-fill';
                if (percentage > 60) {
                    fillEl.classList.add('high');
                } else if (percentage > 30) {
                    fillEl.classList.add('medium');
                } else {
                    fillEl.classList.add('low');
                }
            }
            
            if (warningEl) {
                warningEl.style.display = status.current_points === 0 ? 'block' : 'none';
            }
            
            // Update send button state
            if (isAuthenticated) {
                const sendButton = document.getElementById('sendButton');
                if (sendButton && !isLoading) {
                    sendButton.disabled = !status.can_query;
                }
            }
        }
        
        function startHealthTimer(seconds) {
            // Timer functionality removed for cleaner interface
        }
        
        function stopHealthTimer() {
            // Timer functionality removed for cleaner interface
        }

        if (isAuthenticated) {
            const messagesContainer = document.getElementById('messages');
            const chatInput = document.getElementById('chatInput');
            const sendButton = document.getElementById('sendButton');

            function parseMarkdown(text) {
                // Same markdown parsing logic as before
                let html = text.replace(/&/g, '&amp;')
                              .replace(/</g, '&lt;')
                              .replace(/>/g, '&gt;');
                
                html = html.replace(/\\\`\\\`\\\`([\\s\\S]*?)\\\`\\\`\\\`/g, '<pre><code>$1</code></pre>');
                html = html.replace(/\\\`([^\\\`]+)\\\`/g, '<code>$1</code>');
                html = html.replace(/\\*\\*([^\\*]+)\\*\\*/g, '<strong>$1</strong>');
                html = html.replace(/__([^_]+)__/g, '<strong>$1</strong>');
                html = html.replace(/\\*([^\\*]+)\\*/g, '<em>$1</em>');
                html = html.replace(/_([^_]+)_/g, '<em>$1</em>');
                html = html.replace(/^\\* (.+)$/gm, '<li>$1</li>');
                html = html.replace(/^\\- (.+)$/gm, '<li>$1</li>');
                html = html.replace(/(<li>.*<\\/li>)/s, function(match) {
                    return '<ul>' + match + '</ul>';
                });
                html = html.replace(/^\\d+\\. (.+)$/gm, '<li>$1</li>');
                html = html.replace(/\\n\\n/g, '</p><p>');
                html = '<p>' + html + '</p>';
                html = html.replace(/\\n/g, '<br>');
                html = html.replace(/<p><\\/p>/g, '');
                html = html.replace(/<p><ul>/g, '<ul>');
                html = html.replace(/<\\/ul><\\/p>/g, '</ul>');
                html = html.replace(/<p><pre>/g, '<pre>');
                html = html.replace(/<\\/pre><\\/p>/g, '</pre>');
                
                return html;
            }

            function addMessage(text, sender, isLoading = false) {
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message ' + sender;
                
                const bubbleDiv = document.createElement('div');
                bubbleDiv.className = 'message-bubble';
                
                if (isLoading) {
                    bubbleDiv.classList.add('loading');
                    
                    // Create spinner element
                    const spinner = document.createElement('div');
                    spinner.className = 'spinner';
                    
                    // Create text element
                    const textSpan = document.createElement('span');
                    textSpan.textContent = text;
                    
                    bubbleDiv.appendChild(spinner);
                    bubbleDiv.appendChild(textSpan);
                } else if (sender === 'bot' && !text.includes('Looking at course content') && !text.includes('Thinking')) {
                    bubbleDiv.innerHTML = parseMarkdown(text);
                } else {
                    bubbleDiv.textContent = text;
                }
                
                messageDiv.appendChild(bubbleDiv);
                messagesContainer.appendChild(messageDiv);
                
                setTimeout(() => {
                    messagesContainer.scrollTop = messagesContainer.scrollHeight;
                }, 0);
                
                return bubbleDiv;
            }

            function sendMessage() {
                const message = chatInput.value.trim();
                
                if (!message || isLoading) {
                    return;
                }
                
                // Check health status
                if (healthStatus && !healthStatus.can_query) {
                    addMessage("You've run out of queries. Please wait for your health points to regenerate.", 'bot');
                    return;
                }
                
                isLoading = true;
                sendButton.disabled = true;
                
                addMessage(message, 'user');
                chatInput.value = '';
                adjustTextareaHeight();
                
                const loadingBubble = addMessage('Looking at course content...', 'bot', true);
                
                vscode.postMessage({
                    type: 'sendMessage',
                    message: message,
                    conversationId: conversationId
                });
            }

            function adjustTextareaHeight() {
                chatInput.style.height = 'auto';
                const newHeight = Math.min(chatInput.scrollHeight, 100);
                chatInput.style.height = newHeight + 'px';
                
                if (chatInput.scrollHeight > 100) {
                    chatInput.style.overflowY = 'auto';
                } else {
                    chatInput.style.overflowY = 'hidden';
                }
            }

            // Event listeners
            sendButton.addEventListener('click', sendMessage);
            
            chatInput.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });

            chatInput.addEventListener('input', adjustTextareaHeight);
        }

        // Handle messages from extension
        window.addEventListener('message', event => {
            const message = event.data;
            
            switch (message.type) {
                case 'authRequired':
                    // Reload to show auth screen
                    location.reload();
                    break;
                    
                case 'healthStatus':
                    updateHealthBar(message);
                    break;
                    
                case 'status':
                    if (isAuthenticated) {
                        const lastBotMessage = [...document.querySelectorAll('.message.bot .message-bubble')].pop();
                        if (lastBotMessage && lastBotMessage.classList.contains('loading')) {
                            // Update the text span while keeping the spinner
                            const textSpan = lastBotMessage.querySelector('span');
                            if (textSpan) {
                                textSpan.textContent = message.status;
                            } else {
                                // Fallback: recreate the loading message structure
                                lastBotMessage.innerHTML = '';
                                
                                const spinner = document.createElement('div');
                                spinner.className = 'spinner';
                                
                                const newTextSpan = document.createElement('span');
                                newTextSpan.textContent = message.status;
                                
                                lastBotMessage.appendChild(spinner);
                                lastBotMessage.appendChild(newTextSpan);
                            }
                        }
                    }
                    break;
                    
                case 'response':
                    if (isAuthenticated) {
                        const loadingMessages = document.querySelectorAll('.message.bot .loading');
                        loadingMessages.forEach(msg => {
                            if (msg.parentElement) {
                                msg.parentElement.remove();
                            }
                        });
                        
                        if (message.error) {
                            addMessage(message.error, 'bot');
                        } else if (message.response) {
                            addMessage(message.response, 'bot');
                        }
                        
                        // Update health status from response
                        if (message.health_status) {
                            updateHealthBar(message.health_status);
                        }
                        
                        isLoading = false;
                        sendButton.disabled = healthStatus && !healthStatus.can_query;
                        chatInput.focus();
                    }
                    break;
            }
        });

        // Request auth status on load
        vscode.postMessage({
            type: 'getAuthStatus'
        });
        
        // Request health status on load if authenticated
        if (isAuthenticated) {
            vscode.postMessage({
                type: 'getHealthStatus'
            });
            
            // Refresh health status every 30 seconds
            setInterval(() => {
                vscode.postMessage({
                    type: 'getHealthStatus'
                });
            }, 30000);
        }
    </script>
</body>
</html>`;
    }
} 