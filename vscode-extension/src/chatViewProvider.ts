import * as vscode from 'vscode';
import * as http from 'http';

export class ChatViewProvider implements vscode.WebviewViewProvider {
    public static readonly viewType = 'cs15-tutor.chatView';
    private _view?: vscode.WebviewView;

    constructor(
        private readonly _extensionUri: vscode.Uri,
    ) { }

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
                                error: 'Error generating answer.' 
                            });
                        }
                        break;
                    }
            }
        });
    }

    private _sendMessageToAPI(message: string, conversationId: string): Promise<any> {
        return new Promise((resolve, reject) => {
            const postData = JSON.stringify({ message, conversationId });
            
            const options = {
                hostname: '127.0.0.1',
                port: 5000,
                path: '/api/stream',
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Content-Length': Buffer.byteLength(postData)
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
                                            conversation_id: event.conversation_id
                                        });
                                    } else if (event.status === 'error') {
                                        reject(new Error(event.error || 'Unknown error'));
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
                resolve({ error: 'Error generating answer.' });
            });

            req.write(postData);
            req.end();
        });
    }

    private _getHtmlForWebview(webview: vscode.Webview) {
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
    </style>
</head>
<body>
    <div class="chat-container">
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

    <script>
        const vscode = acquireVsCodeApi();
        const messagesContainer = document.getElementById('messages');
        const chatInput = document.getElementById('chatInput');
        const sendButton = document.getElementById('sendButton');
        const chatForm = document.getElementById('chatForm');
        let conversationId = generateUUID();
        let isLoading = false;

        function generateUUID() {
            return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                const r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
            });
        }

        function parseMarkdown(text) {
            // Escape HTML first
            let html = text.replace(/&/g, '&amp;')
                          .replace(/</g, '&lt;')
                          .replace(/>/g, '&gt;');
            
            // Code blocks (triple backticks)
            html = html.replace(/\\\`\\\`\\\`([\\s\\S]*?)\\\`\\\`\\\`/g, '<pre><code>$1</code></pre>');
            
            // Inline code (single backticks)
            html = html.replace(/\\\`([^\\\`]+)\\\`/g, '<code>$1</code>');
            
            // Bold (double asterisks or underscores)
            html = html.replace(/\\*\\*([^\\*]+)\\*\\*/g, '<strong>$1</strong>');
            html = html.replace(/__([^_]+)__/g, '<strong>$1</strong>');
            
            // Italic (single asterisks or underscores)
            html = html.replace(/\\*([^\\*]+)\\*/g, '<em>$1</em>');
            html = html.replace(/_([^_]+)_/g, '<em>$1</em>');
            
            // Lists (unordered)
            html = html.replace(/^\\* (.+)$/gm, '<li>$1</li>');
            html = html.replace(/^\\- (.+)$/gm, '<li>$1</li>');
            html = html.replace(/(<li>.*<\\/li>)/s, function(match) {
                return '<ul>' + match + '</ul>';
            });
            
            // Lists (ordered)
            html = html.replace(/^\\d+\\. (.+)$/gm, '<li>$1</li>');
            
            // Paragraphs (double newlines)
            html = html.replace(/\\n\\n/g, '</p><p>');
            html = '<p>' + html + '</p>';
            
            // Single line breaks
            html = html.replace(/\\n/g, '<br>');
            
            // Clean up empty paragraphs
            html = html.replace(/<p><\\/p>/g, '');
            html = html.replace(/<p><ul>/g, '<ul>');
            html = html.replace(/<\\/ul><\\/p>/g, '</ul>');
            html = html.replace(/<p><pre>/g, '<pre>');
            html = html.replace(/<\\/pre><\\/p>/g, '</pre>');
            
            return html;
        }

        function addMessage(text, sender) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + sender;
            
            const bubbleDiv = document.createElement('div');
            bubbleDiv.className = 'message-bubble';
            
            // Only parse markdown for bot messages
            if (sender === 'bot' && !text.includes('Looking at course content') && !text.includes('Thinking')) {
                bubbleDiv.innerHTML = parseMarkdown(text);
            } else {
                bubbleDiv.textContent = text;
            }
            
            messageDiv.appendChild(bubbleDiv);
            messagesContainer.appendChild(messageDiv);
            
            // Force layout recalculation and scroll to bottom
            setTimeout(() => {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
            }, 0);
            
            return bubbleDiv;
        }

        function sendMessage() {
            console.log('sendMessage called');
            const message = chatInput.value.trim();
            console.log('Message:', message, 'isLoading:', isLoading);
            
            if (!message || isLoading) {
                console.log('Returning early - no message or loading');
                return;
            }
            
            isLoading = true;
            sendButton.disabled = true;
            
            // Add user message
            addMessage(message, 'user');
            chatInput.value = '';
            chatInput.style.height = 'auto';
            chatInput.style.overflowY = 'hidden';
            adjustTextareaHeight();
            
            // Add loading message
            const loadingBubble = addMessage('Looking at course content...', 'bot');
            loadingBubble.classList.add('loading');
            
            // Send to extension
            console.log('Posting message to extension');
            vscode.postMessage({
                type: 'sendMessage',
                message: message,
                conversationId: conversationId
            });
        }

        // Handle messages from extension
        window.addEventListener('message', event => {
            const message = event.data;
            console.log('Received message from extension:', message);
            
            switch (message.type) {
                case 'status':
                    // Update loading message
                    const lastBotMessage = [...messagesContainer.querySelectorAll('.message.bot .message-bubble')].pop();
                    if (lastBotMessage && lastBotMessage.classList.contains('loading')) {
                        lastBotMessage.textContent = message.status;
                    }
                    break;
                    
                case 'response':
                    // Remove loading message and add response
                    const loadingMessages = messagesContainer.querySelectorAll('.message.bot .loading');
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
                    
                    isLoading = false;
                    sendButton.disabled = false;
                    chatInput.focus();
                    break;
            }
        });

        // Auto-resize textarea
        function adjustTextareaHeight() {
            chatInput.style.height = 'auto';
            const newHeight = Math.min(chatInput.scrollHeight, 100);
            chatInput.style.height = newHeight + 'px';
            
            // Enable scrolling if content exceeds max height
            if (chatInput.scrollHeight > 100) {
                chatInput.style.overflowY = 'auto';
            } else {
                chatInput.style.overflowY = 'hidden';
            }
        }

        // Event listeners
        chatInput.addEventListener('input', adjustTextareaHeight);
        
        // Simplify Enter key handling
        chatInput.addEventListener('keydown', (e) => {
            console.log('Key pressed:', e.key, 'Shift:', e.shiftKey);
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        sendButton.addEventListener('click', () => {
            console.log('Send button clicked');
            sendMessage();
        });
        
        // Initial setup
        chatInput.focus();
        adjustTextareaHeight();
    </script>
</body>
</html>`;
    }
} 