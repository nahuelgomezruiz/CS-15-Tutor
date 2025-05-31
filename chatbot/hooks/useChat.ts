import { useConversation, Message } from "./useConversation";
import { chatApiService } from "../services/chatApi";

export const useChat = () => {
  const {
    messages,
    conversationId,
    isTyping,
    setIsTyping,
    addMessage,
    updateLastMessage,
  } = useConversation();

  const sendMessage = async (messageText: string) => {
    if (!messageText.trim()) return;

    const userMessage: Message = { text: messageText, sender: "user" };
    addMessage(userMessage);
    setIsTyping(true);
    
    // Add an empty bot message that will be updated with the response
    const botMessage: Message = { text: "Looking at course content...", sender: "bot", isStreaming: true };
    addMessage(botMessage);

    try {
      const data = await chatApiService.sendMessage(
        messageText, 
        conversationId,
        (status: string) => {
          // Update the bot message with the current status
          updateLastMessage(status, true);
        }
      );
      
      if (data.response) {
        updateLastMessage(data.response, false);
        console.log("RAG Context:", data.rag_context);
      } else if (data.error) {
        updateLastMessage(`Error: ${data.error}`, false);
      }

    } catch (error) {
      console.error("Error sending message:", error);
      updateLastMessage(
        error instanceof Error 
          ? `Error: ${error.message}` 
          : "Error: An unexpected error occurred",
        false
      );
    } finally {
      setIsTyping(false);
    }
  };

  return {
    messages,
    isTyping,
    sendMessage,
  };
}; 