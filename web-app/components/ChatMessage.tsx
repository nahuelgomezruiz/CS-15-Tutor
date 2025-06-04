import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Message } from '../hooks/useConversation';
import { LoadingSpinner } from './LoadingSpinner';

interface ChatMessageProps {
  message: Message;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.sender === "user";
  const isLoadingState = message.isStreaming && (
    message.text === "Looking at course content..." || 
    message.text === "Thinking..."
  );
  
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div
        className={`px-4 py-3 rounded-2xl max-w-[80%] shadow-sm ${
          isUser
            ? 'bg-cyan-600 text-white rounded-br-md'
            : isLoadingState
            ? 'bg-gray-100 text-gray-500 italic rounded-bl-md'
            : 'bg-gray-100 text-gray-800 rounded-bl-md'
        }`}
      >
        {isLoadingState ? (
          <div className="flex items-center space-x-2">
            <LoadingSpinner />
            <span>{message.text}</span>
          </div>
        ) : isUser ? (
          // For user messages, preserve formatting but escape markdown
          <div className="whitespace-pre-wrap break-words text-sm">
            {message.text}
          </div>
        ) : (
          // For assistant messages, render markdown
          <ReactMarkdown 
            className="prose prose-sm max-w-none prose-p:my-2 prose-headings:my-2 text-sm"
            components={{
              p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
              pre: ({ children }) => (
                <div className="overflow-x-auto my-2">
                  <pre className="bg-gray-800 text-gray-100 p-3 rounded-lg overflow-x-auto text-xs">
                    {children}
                  </pre>
                </div>
              ),
              code: ({ className, children }) => {
                const hasLanguage = className && className.includes('language-');
                return hasLanguage ? (
                  <code className="bg-gray-800 text-gray-100">
                    {children}
                  </code>
                ) : (
                  <code className="bg-gray-200 text-gray-800 px-1 py-0.5 rounded text-xs">
                    {children}
                  </code>
                );
              }
            }}
          >
            {message.text}
          </ReactMarkdown>
        )}
      </div>
    </div>
  );
}; 