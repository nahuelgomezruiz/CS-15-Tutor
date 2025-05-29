import { useState } from "react";
import { Input } from "./input";
import { Button } from "./button";
import { LuSendHorizontal } from "react-icons/lu";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  isDisabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, isDisabled = false }) => {
  const [input, setInput] = useState("");

  const handleSend = () => {
    if (!input.trim() || isDisabled) return;
    
    onSendMessage(input);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !isDisabled) {
      handleSend();
    }
  };

  return (
    <div className="mt-4 flex gap-2 p-4 bg-gray-50 rounded-lg">
      <Input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Type a message..."
        className="flex-1 bg-white"
        onKeyDown={handleKeyDown}
        disabled={isDisabled}
      />
      <Button 
        onClick={handleSend} 
        className="bg-cs-accent hover:bg-cs-navy text-white transition-colors"
        disabled={isDisabled}
      >
        <LuSendHorizontal size="24px" />
      </Button>
    </div>
  );
}; 