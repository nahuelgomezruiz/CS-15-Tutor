interface ChatResponse {
  response?: string;
  error?: string;
  rag_context?: string;
  conversation_id?: string;
}

interface StreamEvent {
  status: 'loading' | 'thinking' | 'complete' | 'error';
  message?: string;
  response?: string;
  error?: string;
  rag_context?: string;
  conversation_id?: string;
}

class ChatApiService {
  private baseUrl = "http://127.0.0.1:5000";

  async sendMessage(
    message: string, 
    conversationId: string,
    onStatusUpdate?: (status: string) => void
  ): Promise<ChatResponse> {
    try {
      // Check if we're in development mode
      const isDevelopmentMode = process.env.NODE_ENV === 'development' || 
                               process.env.DEVELOPMENT_MODE === 'true';
      
      const headers: Record<string, string> = {
        "Content-Type": "application/json"
      };
      
      // Add development headers if in development mode
      if (isDevelopmentMode) {
        headers["X-Development-Mode"] = "true";
        headers["X-Remote-User"] = "testuser"; // Default test user for development
      }
      
      const response = await fetch(`${this.baseUrl}/api/stream`, {
        method: "POST",
        headers,
        body: JSON.stringify({ 
          message,
          conversationId 
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      if (!reader) {
        throw new Error("No response body");
      }

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const jsonStr = line.slice(6);
            if (jsonStr.trim()) {
              try {
                const event: StreamEvent = JSON.parse(jsonStr);
                
                // Handle status updates
                if (event.status === 'loading' && onStatusUpdate) {
                  onStatusUpdate('Looking at course content...');
                } else if (event.status === 'thinking' && onStatusUpdate) {
                  onStatusUpdate('Thinking...');
                } else if (event.status === 'complete') {
                  return {
                    response: event.response,
                    rag_context: event.rag_context,
                    conversation_id: event.conversation_id
                  };
                } else if (event.status === 'error') {
                  throw new Error(event.error || 'Unknown error');
                }
              } catch (e) {
                console.error('Error parsing SSE data:', e);
              }
            }
          }
        }
      }

      throw new Error("Stream ended without complete status");
    } catch (error) {
      console.error("Error sending message:", error);
      throw new Error("Error generating answer.");
    }
  }

  async checkHealth(): Promise<{ status: string }> {
    try {
      const response = await fetch(`${this.baseUrl}/health`);
      return await response.json();
    } catch (error) {
      console.error("Health check failed:", error);
      throw error;
    }
  }
}

export const chatApiService = new ChatApiService();
export type { ChatResponse, StreamEvent }; 