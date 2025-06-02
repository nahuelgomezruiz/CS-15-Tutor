import { useChat } from "../hooks/useChat";
import { useAutoScroll } from "../hooks/useAutoScroll";
import { ChatMessage } from "./ChatMessage";
import { ChatInput } from "./ChatInput";

export const ChatContainer: React.FC = () => {
  const { messages, isTyping, sendMessage } = useChat();
  const { chatRef, handleScroll } = useAutoScroll([messages]);

  return (
    <div className="flex items-center justify-center min-h-screen w-full bg-cs-mint">
      <div className="flex flex-col h-[90vh] w-full max-w-4xl p-4 bg-white rounded-lg shadow-xl">
        <div className="mb-4 pb-4 border-b border-gray-200">
          <h1 className="text-xl font-sans font-medium text-black">CS 15 Tutor</h1>
        </div>
        
        <div 
          ref={chatRef} 
          onScroll={handleScroll} 
          className="flex-1 overflow-y-auto px-2 flex flex-col"
        >
          {messages.map((message, index) => (
            <ChatMessage key={index} message={message} />
          ))}
        </div>

        <ChatInput onSendMessage={sendMessage} isDisabled={isTyping} />
      </div>
    </div>
  );
}; 