from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import os
import json
import re
from llmproxy import generate
from typing import Dict, List

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
        
        # Use llmproxy's generate
        # - we use lastk for context management
        response = generate(
            model='4o-mini',
            system=system_prompt,
            query=message,
            temperature=0.7,
            lastk=num_previous_pairs, 
            session_id=conversation_id,
            rag_usage=True,
            rag_threshold=0.5,
            rag_k=3
        )
        
        if isinstance(response, dict) and 'response' in response:
            assistant_response = response['response']
            rag_context = response.get('rag_context', '')
            
            print(f"📄 Generated response length: {len(assistant_response)}")
            if rag_context:
                print(f"📄 RAG context length: {len(str(rag_context))}")
                print(f"📄 RAG context: {str(rag_context)}")
                
        else:
            # Handle error response
            assistant_response = str(response)
            rag_context = ''
        
        # Add messages to conversation history
        conversation_history.append({"role": "user", "content": message})
        conversation_history.append({"role": "assistant", "content": assistant_response})
        
        # return the response 
        return jsonify({
            "response": assistant_response,
            "rag_context": rag_context,
            "conversation_id": conversation_id
        })
        
    except Exception as error:
        print(f"❌ Error processing request: {error}")
        return jsonify({"error": "Sorry, an error occurred while processing your request."}), 500


if __name__ == '__main__':
    print("🚀 Starting Python Flask API server...")
    print("📍 Available endpoints:")
    print("   POST /api - Main chat endpoint")
    print("   GET /health - Health check")
    
    # Run the Flask app
    app.run(host='127.0.0.1', port=5000, debug=True) 