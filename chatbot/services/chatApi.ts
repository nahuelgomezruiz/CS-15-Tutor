interface ChatResponse {
  response?: string;
  error?: string;
  rag_context?: string;
  conversation_id?: string;
}

class ChatApiService {
  private baseUrl = "http://127.0.0.1:5000";

  async sendMessage(message: string, conversationId: string): Promise<ChatResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          message,
          conversationId 
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error("Error sending message:", error);
      throw new Error("Could not connect to the Python API server. Make sure it's running on port 5000.");
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
export type { ChatResponse }; 