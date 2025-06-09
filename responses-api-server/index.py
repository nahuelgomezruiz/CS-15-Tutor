from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import os
import json
import re
from llmproxy import generate, retrieve, model_info
from typing import Dict, List
import time
import csv

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Store conversations in memory (key is conversationId)
conversations: Dict[str, List[Dict[str, str]]] = {}

"""
name:        load_system_prompt
description: load the system prompt from the text in system_prompt.txt
parameters:  none
returns:     str - the system prompt
note:        system_prompt.txt is required in the same directory as this file
"""
def load_system_prompt() -> str:
    prompt_path = os.path.join(os.path.dirname(__file__), "system_prompt.txt")
    with open(prompt_path, "r") as f:
        return f.read().strip()

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
name:        chat_handler
description: endpoint to handle the chat request and return a message-response
parameters:  a json object with a message key and a conversationId key
returns:     a json object with a response key and a rag_context key
"""
@app.route('/api', methods=['POST'])
def chat_handler():
    try:
        data = request.get_json()
        message = data.get('message', '')
        conversation_id = data.get('conversationId', 'default')
        
        print(f"📝 Processing message: {message}")
        print(f"💬 Conversation ID: {conversation_id}")
        
        if not message.strip():
            return jsonify({"error": "Message is required"}), 400
        
        # Initialize conversation if it doesn't exist
        # we do this by adding a new element to the conversations dictionary
        # - the key is the conversationId and the value is a list of messages
        # - the first element is the system prompt
        if conversation_id not in conversations:
            system_prompt = load_system_prompt()
            conversations[conversation_id] = [
                {"role": "system", "content": system_prompt}
            ]
            print(f"🆕 Initialized new conversation: {conversation_id}")
        
        # Calculate the number of previous user-assistant pairs for lastk
        # (we exclude the system prompt (index 0) and count pairs)
        conversation_history = conversations[conversation_id]
        num_previous_pairs = (len(conversation_history) - 1) // 2
        
        # Get the system prompt (always the first message)
        system_prompt = conversation_history[0]["content"]
        
        # Use retrieve() to get RAG context from GenericSession
        try:
            rag_context = retrieve(
                query=message,
                session_id='GenericSession',
                rag_threshold=0.3,
                rag_k=3
            )
            
            # Format the RAG context and add it to the system prompt
            if rag_context:
                rag_context_formatted = rag_context_string_simple(rag_context)
                enhanced_system_prompt = f"{system_prompt}\n\n{rag_context_formatted}"
                print(f"📄 Retrieved RAG context from GenericSession")
                print(f"📄 RAG context length: {len(rag_context_formatted)}")
            else:
                enhanced_system_prompt = system_prompt
                rag_context_formatted = ''
                print(f"📭 No RAG context found")
                
        except Exception as e:
            print(f"⚠️ Error retrieving RAG context: {e}")
            enhanced_system_prompt = system_prompt
            rag_context_formatted = ''
        
        # Use llmproxy's generate
        # - we use lastk for context management
        # - rag_usage=False since we manually provide RAG context in system prompt
        response = generate(
            model='4o-mini',
            system=enhanced_system_prompt,
            query=message,
            temperature=0.7,
            lastk=num_previous_pairs, 
            session_id=conversation_id,
            rag_usage=False, 
        )
        
        if isinstance(response, dict) and 'response' in response:
            assistant_response = response['response']
            
            print(f"📄 Generated response length: {len(assistant_response)}")
            if 'rag_context_formatted' in locals() and rag_context_formatted:
                print(f"📄 RAG context length: {len(str(rag_context_formatted))}")
                
        else:
            # Handle string response (when rag_usage=False)
            assistant_response = str(response)
        
        # Add messages to conversation history
        conversation_history.append({"role": "user", "content": message})
        conversation_history.append({"role": "assistant", "content": assistant_response})
        
        print(f"📄 Generated response length: {len(assistant_response)}")
        
        # return the response 
        return jsonify({
            "response": assistant_response,
            "rag_context": rag_context_formatted if 'rag_context_formatted' in locals() else '',
            "conversation_id": conversation_id
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
    data = request.get_json()
    message = data.get('message', '')
    conversation_id = data.get('conversationId', 'default')
    
    def generate_events():
        try:
            print(f"📝 Processing message: {message}")
            print(f"💬 Conversation ID: {conversation_id}")
            
            if not message.strip():
                yield f'data: {json.dumps({"error": "Message is required"})}\n\n'
                return
            
            # Initialize conversation if it doesn't exist
            if conversation_id not in conversations:
                system_prompt = load_system_prompt()
                conversations[conversation_id] = [
                    {"role": "system", "content": system_prompt}
                ]
                print(f"🆕 Initialized new conversation: {conversation_id}")
            
            # Send status: loading (RAG retrieval)
            yield f'data: {json.dumps({"status": "loading", "message": "Looking at course content..."})}\n\n'
            
            # Calculate the number of previous user-assistant pairs for lastk
            conversation_history = conversations[conversation_id]
            num_previous_pairs = (len(conversation_history) - 1) // 2
            
            # Get the system prompt (always the first message)
            system_prompt = conversation_history[0]["content"]

            threshold = 0.4  # RAG threshold
            k = 7  # Number of RAG documents to retrieve
            session = 'MetrosimTestSession'  # Session ID for RAG retrieval
            print(f"🔍 Using RAG threshold: {threshold}, k: {k}")

            # Use retrieve() to get RAG context from GenericSession
            rag_context_formatted = ''
            try:
                rag_context = retrieve(
                    query=message,
                    session_id=session,
                    rag_threshold=threshold,
                    rag_k=k
                )
                
                # Format the RAG context and add it to the system prompt
                if rag_context:
                    rag_context_formatted = rag_context_string_simple(rag_context)
                    enhanced_system_prompt = f"{system_prompt}\n\n{rag_context_formatted}"
                    print(f"📄 Retrieved RAG context from GenericSession")
                    print(f"📄 RAG context length: {len(rag_context_formatted)}")
                else:
                    enhanced_system_prompt = system_prompt
                    print(f"📭 No RAG context found")
                    
            except Exception as e:
                print(f"⚠️ Error retrieving RAG context: {e}")
                enhanced_system_prompt = system_prompt
            
            # Send status: thinking (response generation)
            yield f'data: {json.dumps({"status": "thinking", "message": "Thinking..."})}\n\n'
            
            # Use llmproxy's generate
            response = generate(
                model='4o-mini',
                system=enhanced_system_prompt,
                query=message,
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
            
            print(f"📄 Generated response length: {len(assistant_response)}")
            csv_path = os.path.abspath("query_rag_responses.csv")
            print(f"📁 Writing to: {csv_path}")

            with open('responses-api-server/query_rag_responses.csv', 'a', newline='') as csvfile:
                csv_writer = csv.writer(csvfile)
                csv_writer.writerow([message, rag_context_formatted, assistant_response, threshold, k, session])

            
            # Send final response
            yield f'data: {json.dumps({"status": "complete", "response": assistant_response, "rag_context": rag_context_formatted, "conversation_id": conversation_id})}\n\n'
            
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
            context_string = """The following is additional context that may be helpful in answering the user's query."""
        
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

if __name__ == '__main__':
    print("🚀 Starting Python Flask API server...")
    print("📍 Available endpoints:")
    print("   POST /api - Main chat endpoint")
    print("   POST /api/stream - Streaming chat endpoint with status updates")
    print("   GET /health - Health check")
    
    # Run the Flask app
    app.run(host='127.0.0.1', port=5000, debug=True) 