import ReactMarkdown from "react-markdown";
import { Message } from "../hooks/useConversation";

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.sender === "user";
  
  return (
    <div
      className={`p-4 my-1 max-w-2xl ${
        isUser
          ? "bg-white border-cs-accent text-cs-navy self-end border-r-4 rounded-l-lg shadow-sm"
          : "bg-white border-cs-mint text-cs-navy self-start border-l-4 rounded-r-lg shadow-sm"
      }`}
    >
      {isUser ? (
        message.text
      ) : (
        <div className="prose prose-headings:text-cyan-700 prose-headings:font-extrabold prose-p:mt-2 prose-p:mb-4 max-w-none">
          <ReactMarkdown>
            {message.text + (message.isStreaming ? "|" : "")}
          </ReactMarkdown>
        </div>
      )}
    </div>
  );
}; 