import { useChat } from "../hooks/useChat";
import { useAutoScroll } from "../hooks/useAutoScroll";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";

export const ChatContainer: React.FC = () => {
  const { messages, isTyping, sendMessage } = useChat();
  const { chatRef, handleScroll } = useAutoScroll([messages]);

  return (
    <div className="flex items-center justify-center min-h-screen w-full bg-cs-mint">
      <div className="flex flex-col h-[90vh] w-full max-w-6xl p-4 bg-white rounded-lg shadow-xl">
        <div className="mb-4">
          <h1 className="text-xl font-bold text-cyan-700">CS 15 Tutor (Python API)</h1>
          <p className="text-sm text-gray-600">Connected to Python Flask API on port 5000</p>
        </div>
        
        <div 
          ref={chatRef} 
          onScroll={handleScroll} 
          className="flex-1 overflow-y-auto p-4 flex flex-col space-y-4"
        >
          {messages.map((message, index) => (
            <ChatMessage key={index} message={message} />
          ))}
          
          {isTyping && messages.length > 0 && messages[messages.length - 1].sender === "user" && (
            <div className="p-4 my-1 max-w-lg text-gray-500 italic self-start bg-gray-50 rounded-lg shadow-sm">
              Thinking...
            </div>
          )}
        </div>

        <ChatInput onSendMessage={sendMessage} isDisabled={isTyping} />
      </div>
    </div>
  );
}; 