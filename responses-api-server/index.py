from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import os
import json
import re
from llmproxy import generate, retrieve
from typing import Dict, List
import time
import urllib.parse

# Import our new services
from auth_service import auth_service
from logging_service import logging_service

def escape_for_json(text: str) -> str:
    """
    Escape characters in text to ensure JSON compatibility for LLMProxy API calls.
    
    This function handles the escaping requirements mentioned in the LLMProxy documentation
    to prevent JSON parsing errors when text contains unescaped quotes or HTML tags.
    
    Args:
        text (str): The input text that may contain characters needing escaping
        
    Returns:
        str: The escaped text safe for JSON encoding
    """
    if not isinstance(text, str):
        return str(text)
    
    # Escape backslashes first (must be done before escaping quotes)
    escaped = text.replace('\\', '\\\\')
    
    # Escape double quotes
    escaped = escaped.replace('"', '\\"')
    
    # Escape other control characters that could break JSON
    escaped = escaped.replace('\n', '\\n')
    escaped = escaped.replace('\r', '\\r')
    escaped = escaped.replace('\t', '\\t')
    escaped = escaped.replace('\b', '\\b')
    escaped = escaped.replace('\f', '\\f')
    
    return escaped

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Store conversations in memory (key is conversationId)
conversations: Dict[str, List[Dict[str, str]]] = {}

# Store accumulated RAG context for each conversation (key is conversationId)
conversation_rag_context: Dict[str, List[Dict]] = {}

# Cache the system prompt at startup to avoid file I/O on every new conversation
CACHED_SYSTEM_PROMPT = None

def load_system_prompt() -> str:
    """Load the system prompt from cache or file if not cached, or reload if in development mode"""
    global CACHED_SYSTEM_PROMPT
    
    # Check if we're in development mode
    development_mode = os.getenv('DEVELOPMENT_MODE', '').lower() == 'true'
    
    if CACHED_SYSTEM_PROMPT is None or development_mode:
        prompt_path = os.path.join(os.path.dirname(__file__), "system_prompt.txt")
        with open(prompt_path, "r") as f:
            CACHED_SYSTEM_PROMPT = f.read().strip()
        
        if development_mode:
            print("🔄 System prompt reloaded from file (development mode)")
        else:
            print("📄 System prompt loaded and cached")
    
    return CACHED_SYSTEM_PROMPT

# Preload system prompt at startup
load_system_prompt()

"""
name:        health_check
description: endpoint to check if the server is running
parameters:  none
returns:     a json object with a status key and a value of "healthy"
"""
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

"""
name:        vscode_auth_endpoint
description: endpoint for VSCode extension authentication
parameters:  none (uses query parameters)
returns:     authentication status or redirect
"""
@app.route('/vscode-auth', methods=['GET', 'POST'])
def vscode_auth_endpoint():
    """Handle VSCode extension authentication"""
    try:
        if request.method == 'GET':
            session_id = request.args.get('session_id')
            
            if not session_id:
                # VSCode extension requesting a new session ID
                login_url = auth_service.generate_vscode_login_url('http://127.0.0.1:3000')
                # Extract session_id from the URL
                parsed_url = urllib.parse.urlparse(login_url)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                session_id = query_params.get('session_id', [None])[0]
                
                if session_id:
                    return jsonify({
                        "session_id": session_id,
                        "login_url": login_url
                    })
                else:
                    return jsonify({"error": "Failed to generate session"}), 500
            else:
                # Web browser accessing the authentication page
                return jsonify({
                    "message": "VSCode authentication pending",
                    "session_id": session_id,
                    "instructions": "Please authenticate via the web interface"
                })
        
        elif request.method == 'POST':
            # Handle authentication callback
            data = request.get_json()
            session_id = data.get('session_id')
            
            # Get UTLN from web authentication
            utln, platform = auth_service.authenticate_request(request)
            if not utln:
                return jsonify({"error": "Authentication required"}), 401
            
            # Create VSCode token
            token = auth_service.handle_vscode_login_callback(session_id, utln)
            if token:
                return jsonify({"token": token, "utln": utln})
            else:
                return jsonify({"error": "Authentication failed"}), 401
                
    except Exception as e:
        print(f"❌ Error in VSCode auth: {e}")
        return jsonify({"error": "Authentication error"}), 500

"""
name:        vscode_direct_auth
description: endpoint for direct VSCode authentication with username/password
parameters:  username and password in JSON body
returns:     JWT token if successful
"""
@app.route('/vscode-direct-auth', methods=['POST'])
def vscode_direct_auth():
    """Handle direct VSCode authentication with credentials"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "JSON data required"}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400
        
        # Authenticate user with LDAP
        token = auth_service.authenticate_vscode_user(username, password)
        
        if token:
            return jsonify({
                "success": True,
                "token": token,
                "username": username.lower(),
                "message": "Authentication successful"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Invalid credentials or user not authorized for CS 15"
            }), 401
            
    except Exception as e:
        print(f"❌ Error in direct VSCode auth: {e}")
        return jsonify({"error": "Authentication error"}), 500

"""
name:        vscode_auth_status
description: endpoint to check VSCode authentication status
parameters:  session_id as query parameter
returns:     authentication status
"""
@app.route('/vscode-auth-status', methods=['GET'])
def vscode_auth_status():
    """Check VSCode authentication status"""
    try:
        session_id = request.args.get('session_id')
        if not session_id:
            return jsonify({"error": "Missing session_id"}), 400
        
        status = auth_service.get_vscode_session_status(session_id)
        return jsonify(status)
        
    except Exception as e:
        print(f"❌ Error checking auth status: {e}")
        return jsonify({"error": "Status check failed"}), 500

"""
name:        analytics_endpoint
description: endpoint to get system analytics (admin only)
parameters:  none
returns:     system analytics data
"""
@app.route('/analytics', methods=['GET'])
def analytics_endpoint():
    """Get system analytics (admin endpoint)"""
    try:
        # Authenticate request
        utln, platform = auth_service.authenticate_request(request)
        if not utln:
            return jsonify({"error": "Authentication required"}), 401
        
        # For now, allow any authenticated user to view analytics
        # In production, you might want to restrict this to admins
        analytics = logging_service.get_system_analytics()
        engagement = logging_service.analyze_user_engagement()
        
        return jsonify({
            "system_analytics": analytics,
            "engagement_analytics": engagement
        })
        
    except Exception as e:
        print(f"❌ Error getting analytics: {e}")
        return jsonify({"error": "Analytics error"}), 500

"""
name:        chat_handler
description: endpoint to handle the chat request and return a message-response
parameters:  a json object with a message key and a conversationId key
returns:     a json object with a response key and a rag_context key
"""
@app.route('/api', methods=['POST'])
def chat_handler():
    request_start_time = time.time()
    
    try:
        # Authenticate request first
        utln, platform = auth_service.authenticate_request(request)
        if not utln:
            return jsonify({"error": "Authentication required. Please log in with your Tufts credentials."}), 401
        
        # Check authorization
        if not auth_service.is_authorized_cs15_student(utln):
            return jsonify({"error": "Access denied. You must be enrolled in CS 15."}), 403
        
        data = request.get_json()
        message = data.get('message', '')
        conversation_id = data.get('conversationId', 'default')
        
        print(f"📝 Processing message from {utln} ({platform}): {message}")
        print(f"💬 Conversation ID: {conversation_id}")
        
        if not message.strip():
            return jsonify({"error": "Message is required"}), 400
        
        # Log the user query
        query_log_result = logging_service.log_user_query(
            utln=utln,
            conversation_id=conversation_id,
            query=message,
            platform=platform
        )
        
        # Initialize conversation if it doesn't exist
        base_system_prompt = load_system_prompt()
        if conversation_id not in conversations:
            conversations[conversation_id] = [
                {"role": "system", "content": base_system_prompt}
            ]
            conversation_rag_context[conversation_id] = []
            print(f"🆕 Initialized new conversation: {conversation_id}")
        
        # In development mode, always update the base system prompt
        development_mode = os.getenv('DEVELOPMENT_MODE', '').lower() == 'true'
        if development_mode:
            update_conversation_system_prompt(conversation_id, base_system_prompt)
        
        # Calculate the number of previous user-assistant pairs for lastk
        conversation_history = conversations[conversation_id]
        num_previous_pairs = (len(conversation_history) - 1) // 2
        
        # Use retrieve() to get RAG context from GenericSession
        rag_context_formatted = ''
        new_rag_context_added = False
        try:
            print(f"🔍 Attempting RAG retrieval for query: '{message}'")
            # Escape the message for JSON compatibility
            escaped_message = escape_for_json(message)
            rag_context = retrieve(
                query=escaped_message,
                session_id='GenericSession',
                rag_threshold=0.4,
                rag_k=5
            )
            
            print(f"🔍 RAG API response type: {type(rag_context)}")
            print(f"🔍 RAG API response: {rag_context}")
            
            # Add new RAG context to accumulated context if any is retrieved
            if rag_context and isinstance(rag_context, list) and len(rag_context) > 0:
                # Add to accumulated context for this conversation
                conversation_rag_context[conversation_id].extend(rag_context)
                new_rag_context_added = True
                
                # Update the system prompt in conversation history with all accumulated context
                update_conversation_system_prompt(conversation_id, base_system_prompt)
                
                # Format the new RAG context for logging
                rag_context_formatted = rag_context_string_simple(rag_context)
                print(f"📄 Retrieved and added RAG context from GenericSession")
                print(f"📄 New RAG context length: {len(rag_context_formatted)}")
                print(f"📄 Total accumulated contexts: {len(conversation_rag_context[conversation_id])}")
            else:
                print(f"📭 No new RAG context found. Response was: {rag_context}")
                
        except Exception as e:
            print(f"⚠️ Error retrieving RAG context: {e}")
            import traceback
            print(f"⚠️ Full traceback: {traceback.format_exc()}")
        
        # Get the current system prompt (which now includes all accumulated context)
        enhanced_system_prompt = conversations[conversation_id][0]["content"]
        
        # Escape parameters for JSON compatibility
        escaped_system_prompt = escape_for_json(enhanced_system_prompt)
        escaped_message = escape_for_json(message)
        
        # Use llmproxy's generate
        response = generate(
            model='4o-mini',
            system=escaped_system_prompt,
            query=escaped_message,
            temperature=0.7,
            lastk=num_previous_pairs, 
            session_id=conversation_id,
            rag_usage=False, 
        )
        
        if isinstance(response, dict) and 'response' in response:
            assistant_response = response['response']
        else:
            assistant_response = str(response)
        
        # Add messages to conversation history
        conversation_history.append({"role": "user", "content": message})
        conversation_history.append({"role": "assistant", "content": assistant_response})
        
        # Calculate response time
        response_time_ms = int((time.time() - request_start_time) * 1000)
        
        # Get accumulated RAG context for logging
        accumulated_rag_context = ''
        if conversation_id in conversation_rag_context and conversation_rag_context[conversation_id]:
            accumulated_rag_context = rag_context_string_simple(conversation_rag_context[conversation_id])
        
        # Log the assistant response
        logging_service.log_assistant_response(
            conversation_id=conversation_id,
            response=assistant_response,
            rag_context=accumulated_rag_context,
            model_used='4o-mini',
            temperature=0.7,
            response_time_ms=response_time_ms
        )
        
        print(f"📄 Generated response length: {len(assistant_response)}")
        print(f"⏱️ Total request time: {response_time_ms}ms")
        print(f"👤 User analytics: {query_log_result}")
        
        # return the response 
        return jsonify({
            "response": assistant_response,
            "rag_context": accumulated_rag_context,
            "conversation_id": conversation_id,
            "user_info": {
                "anonymous_id": query_log_result.get('anonymous_id'),
                "platform": platform,
                "is_new_conversation": query_log_result.get('is_new_conversation', False)
            }
        })
        
    except Exception as error:
        print(f"❌ Error processing request: {error}")
        return jsonify({"error": "Sorry, an error occurred while processing your request."}), 500

"""
name:        chat_handler_stream
description: endpoint to handle chat requests with streaming status updates
parameters:  a json object with a message key and a conversationId key
returns:     Server-Sent Events stream with status updates and final response
"""
@app.route('/api/stream', methods=['POST'])
def chat_handler_stream():
    request_start_time = time.time()
    
    # Authenticate request first
    utln, platform = auth_service.authenticate_request(request)
    if not utln:
        def error_stream():
            yield f'data: {json.dumps({"status": "error", "error": "Authentication required. Please log in with your Tufts credentials."})}\n\n'
        return Response(stream_with_context(error_stream()), mimetype='text/event-stream')
    
    # Check authorization
    if not auth_service.is_authorized_cs15_student(utln):
        def error_stream():
            yield f'data: {json.dumps({"status": "error", "error": "Access denied. You must be enrolled in CS 15."})}\n\n'
        return Response(stream_with_context(error_stream()), mimetype='text/event-stream')
    
    data = request.get_json()
    message = data.get('message', '')
    conversation_id = data.get('conversationId', 'default')
    
    def generate_events():
        try:
            print(f"📝 Processing message from {utln} ({platform}): {message}")
            print(f"💬 Conversation ID: {conversation_id}")
            
            if not message.strip():
                yield f'data: {json.dumps({"error": "Message is required"})}\n\n'
                return
            
            # Log the user query
            query_log_result = logging_service.log_user_query(
                utln=utln,
                conversation_id=conversation_id,
                query=message,
                platform=platform
            )
            
            # Initialize conversation if it doesn't exist
            base_system_prompt = load_system_prompt()
            if conversation_id not in conversations:
                conversations[conversation_id] = [
                    {"role": "system", "content": base_system_prompt}
                ]
                conversation_rag_context[conversation_id] = []
                print(f"🆕 Initialized new conversation: {conversation_id}")
            
            # In development mode, always update the base system prompt
            development_mode = os.getenv('DEVELOPMENT_MODE', '').lower() == 'true'
            if development_mode:
                update_conversation_system_prompt(conversation_id, base_system_prompt)
            
            # Send status: loading (RAG retrieval)
            yield f'data: {json.dumps({"status": "loading", "message": "Looking at course content..."})}\n\n'
            
            # Calculate the number of previous user-assistant pairs for lastk
            conversation_history = conversations[conversation_id]
            num_previous_pairs = (len(conversation_history) - 1) // 2
            
            # Use retrieve() to get RAG context from GenericSession
            rag_context_formatted = ''
            new_rag_context_added = False
            try:
                print(f"🔍 Attempting RAG retrieval for query: '{message}'")
                # Escape the message for JSON compatibility
                escaped_message = escape_for_json(message)
                rag_context = retrieve(
                    query=escaped_message,
                    session_id='GenericSession',
                    rag_threshold=0.4,
                    rag_k=5
                )
                
                print(f"🔍 RAG API response type: {type(rag_context)}")
                print(f"🔍 RAG API response: {rag_context}")
                
                # Add new RAG context to accumulated context if any is retrieved
                if rag_context and isinstance(rag_context, list) and len(rag_context) > 0:
                    # Add to accumulated context for this conversation
                    conversation_rag_context[conversation_id].extend(rag_context)
                    new_rag_context_added = True
                    
                    # Update the system prompt in conversation history with all accumulated context
                    update_conversation_system_prompt(conversation_id, base_system_prompt)
                    
                    # Format the new RAG context for logging
                    rag_context_formatted = rag_context_string_simple(rag_context)
                    print(f"📄 Retrieved and added RAG context from GenericSession")
                    print(f"📄 New RAG context length: {len(rag_context_formatted)}")
                    print(f"📄 Total accumulated contexts: {len(conversation_rag_context[conversation_id])}")
                else:
                    print(f"📭 No new RAG context found. Response was: {rag_context}")
                    
            except Exception as e:
                print(f"⚠️ Error retrieving RAG context: {e}")
                import traceback
                print(f"⚠️ Full traceback: {traceback.format_exc()}")
            
            # Get the current system prompt (which now includes all accumulated context)
            enhanced_system_prompt = conversations[conversation_id][0]["content"]
            
            # Send status: thinking (response generation)
            yield f'data: {json.dumps({"status": "thinking", "message": "Thinking..."})}\n\n'
            
            # Escape parameters for JSON compatibility
            escaped_system_prompt = escape_for_json(enhanced_system_prompt)
            escaped_message = escape_for_json(message)
            
            # Use llmproxy's generate
            response = generate(
                model='4o-mini',
                system=escaped_system_prompt,
                query=escaped_message,
                temperature=0.7,
                lastk=num_previous_pairs, 
                session_id=conversation_id,
                rag_usage=False, 
            )
            
            if isinstance(response, dict) and 'response' in response:
                assistant_response = response['response']
            else:
                assistant_response = str(response)
            
            # Add messages to conversation history
            conversation_history.append({"role": "user", "content": message})
            conversation_history.append({"role": "assistant", "content": assistant_response})
            
            # Calculate response time
            response_time_ms = int((time.time() - request_start_time) * 1000)
            
            # Get accumulated RAG context for logging
            accumulated_rag_context = ''
            if conversation_id in conversation_rag_context and conversation_rag_context[conversation_id]:
                accumulated_rag_context = rag_context_string_simple(conversation_rag_context[conversation_id])
            
            # Log the assistant response
            logging_service.log_assistant_response(
                conversation_id=conversation_id,
                response=assistant_response,
                rag_context=accumulated_rag_context,
                model_used='4o-mini',
                temperature=0.7,
                response_time_ms=response_time_ms
            )
            
            print(f"📄 Generated response length: {len(assistant_response)}")
            print(f"⏱️ Total request time: {response_time_ms}ms")
            print(f"👤 User analytics: {query_log_result}")
            
            # Send final response
            response_data = {
                "status": "complete", 
                "response": assistant_response, 
                "rag_context": accumulated_rag_context, 
                "conversation_id": conversation_id,
                "user_info": {
                    "anonymous_id": query_log_result.get('anonymous_id'),
                    "platform": platform,
                    "is_new_conversation": query_log_result.get('is_new_conversation', False)
                }
            }
            yield f'data: {json.dumps(response_data)}\n\n'
            
        except Exception as error:
            print(f"❌ Error processing request: {error}")
            yield f'data: {json.dumps({"status": "error", "error": "Sorry, an error occurred while processing your request."})}\n\n'
    
    return Response(
        stream_with_context(generate_events()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

"""
name:        rag_context_string_simple
description: create a context string from retrieve's return value
parameters:  rag_context - the return value from retrieve()
returns:     str - formatted context string
"""
def rag_context_string_simple(rag_context):
    context_string = ""
    
    i = 1
    for collection in rag_context:
        if not context_string:
            context_string = """The following is additional context that may be
                             helpful in answering the query. Use them only
                             if it is relevant to the user's query."""
        
        context_string += """
        #{} {}
        """.format(i, collection['doc_summary'])
        j = 1
        for chunk in collection['chunks']:
            context_string += """
            #{}.{} {}
            """.format(i, j, chunk)
            j += 1
        i += 1 
    return context_string

"""
name:        update_conversation_system_prompt
description: update the system prompt in conversation history with accumulated RAG context
parameters:  conversation_id - the conversation ID
             base_system_prompt - the original system prompt
returns:     none
"""
def update_conversation_system_prompt(conversation_id, base_system_prompt):
    if conversation_id not in conversation_rag_context or not conversation_rag_context[conversation_id]:
        # No RAG context accumulated yet, keep original system prompt
        conversations[conversation_id][0]["content"] = base_system_prompt
        return
    
    # Format all accumulated RAG context
    accumulated_context = rag_context_string_simple(conversation_rag_context[conversation_id])
    
    # Update the system prompt with accumulated context
    enhanced_system_prompt = f"{base_system_prompt}\n\n{accumulated_context}"
    conversations[conversation_id][0]["content"] = enhanced_system_prompt

if __name__ == '__main__':
    print("🚀 Starting Python Flask API server with authentication and logging...")
    print("📍 Available endpoints:")
    print("   POST /api - Main chat endpoint (requires authentication)")
    print("   POST /api/stream - Streaming chat endpoint (requires authentication)")
    print("   GET /health - Health check")
    print("   GET/POST /vscode-auth - VSCode extension authentication (browser-based)")
    print("   POST /vscode-direct-auth - VSCode extension authentication (form-based)")
    print("   GET /vscode-auth-status - Check VSCode auth status")
    print("   GET /analytics - System analytics (authenticated users)")
    print("🔐 Authentication: Web app uses .htaccess, VSCode uses JWT tokens with LDAP")
    print("📊 Logging: All interactions are logged with user anonymization")
    
    # Run the Flask app
    app.run(host='127.0.0.1', port=5000, debug=True) 