# Python Flask API - CS 15 Tutor

This Python Flask API provides the same functionality as `index.ts` but uses the `generate()` function from `llmproxy.py` instead of calling OpenAI directly.

## Features

- **Chat API**: Handles conversation with the CS 15 tutor
- **RAG Integration**: Automatically enables RAG for course-related queries
- **Conversation Memory**: Maintains conversation history per session
- **Streaming Support**: Offers both regular and streaming response endpoints
- **Course Keywords**: Detects course-related queries using keywords
- **Health Check**: Provides endpoint for service monitoring

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements_flask.txt
   ```

2. **Ensure Configuration**:
   - Make sure `config.json` is configured with your API credentials
   - Ensure `system_prompt.txt` contains the system prompt
   - Verify `llmproxy.py` is working correctly

3. **Start the Server**:
   ```bash
   cd chatbot/pages/api
   python index_python.py
   ```

   The server will start on `http://127.0.0.1:5000`

## API Endpoints

### POST `/api` - Main Chat Endpoint

Send a message and receive a response from the tutor.

**Request Body**:
```json
{
  "message": "How do I implement PassengerQueue?",
  "conversationId": "optional-conversation-id"
}
```

**Response**:
```json
{
  "response": "To implement PassengerQueue...",
  "rag_context": "Retrieved context from course materials",
  "conversation_id": "conversation-uuid"
}
```

### POST `/api/stream` - Streaming Chat Endpoint

Same as `/api` but streams the response in real-time.

**Request**: Same as `/api`

**Response**: Streaming text response

### GET `/health` - Health Check

Returns the health status of the API.

**Response**:
```json
{
  "status": "healthy"
}
```

### GET `/conversations/<conversation_id>` - Get Conversation History

Retrieve the conversation history for a specific conversation.

**Response**:
```json
{
  "conversation_id": "conversation-uuid",
  "messages": [
    {"role": "system", "content": "System prompt..."},
    {"role": "user", "content": "User message"},
    {"role": "assistant", "content": "Assistant response"}
  ]
}
```

### DELETE `/conversations/<conversation_id>` - Delete Conversation

Delete a conversation and its history.

**Response**:
```json
{
  "message": "Conversation conversation-uuid deleted"
}
```

## Testing

Run the test script to verify the API is working:

```bash
python test_python_api.py
```

This will test:
- Health check endpoint
- Regular chat endpoint
- Streaming chat endpoint

## Key Differences from index.ts

1. **LLMProxy Integration**: Uses `generate()` function from `llmproxy.py` instead of OpenAI directly
2. **Built-in RAG**: RAG is handled by llmproxy instead of manual context retrieval
3. **Python Flask**: Uses Flask instead of Next.js API routes
4. **Simulated Streaming**: The streaming endpoint simulates streaming by chunking the complete response

## Course Keywords

The API detects course-related queries using these keywords:
- `metrosim`
- `zap`
- `gerp`
- `calcyoulater`

When a query contains these keywords, RAG is automatically enabled to provide relevant course context.

## Configuration

The API uses the same configuration files as the original setup:

- `config.json`: Contains API credentials for llmproxy
- `system_prompt.txt`: Contains the system prompt for the tutor
- `llmproxy.py`: Handles communication with the LLM service

## Error Handling

The API includes comprehensive error handling:
- Invalid requests return appropriate HTTP status codes
- LLMProxy errors are caught and user-friendly messages are returned
- Missing conversations return 404 errors
- Server errors return 500 status codes

## CORS Support

The API includes CORS support to allow requests from web frontends running on different ports.

## Usage Example

```python
import requests

# Send a message
response = requests.post("http://127.0.0.1:5000/api", json={
    "message": "What is a binary tree?",
    "conversationId": "my-conversation"
})

data = response.json()
print(f"Response: {data['response']}")
print(f"RAG Context: {data['rag_context']}")
```

## Notes

- Conversation history is stored in memory and will be lost when the server restarts
- For production use, consider implementing persistent storage for conversations
- The streaming endpoint provides simulated streaming; true streaming would require modifications to llmproxy
- Token limits are managed by keeping only the system prompt and last 10 messages per conversation 