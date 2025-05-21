import { useState, useEffect, useRef } from "react";
import { Input } from "../components/input";
import { Button } from "../components/button";
import { LuSendHorizontal } from "react-icons/lu";
import ReactMarkdown from "react-markdown";

interface Message {
  text: string;
  sender: "user" | "bot";
  isStreaming?: boolean;
}

export default function ChatApp() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const chatRef = useRef<HTMLDivElement>(null);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = { text: input, sender: "user" };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsTyping(true);
    
    // Add an empty bot message that will be updated with streaming content
    const botMessage: Message = { text: "", sender: "bot", isStreaming: true };
    setMessages((prev) => [...prev, botMessage]);

    try {
      const response = await fetch("/api", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: input }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Check if the response body is readable
      if (!response.body) {
        throw new Error("Response body is null");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let accumulatedText = "";

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          break;
        }

        const chunk = decoder.decode(value, { stream: true });
        accumulatedText += chunk;
        
        // Force a state update for each chunk
        setMessages((prev) => {
          const newMessages = [...prev];
          const lastMessage = newMessages[newMessages.length - 1];
          if (lastMessage && lastMessage.sender === "bot") {
            lastMessage.text = accumulatedText;
          }
          return newMessages;
        });

        // Force DOM update by adding a small delay
        await new Promise(resolve => setTimeout(resolve, 10));
      }

      // Mark streaming as complete
      setMessages((prev) => {
        const newMessages = [...prev];
        const lastMessage = newMessages[newMessages.length - 1];
        if (lastMessage && lastMessage.sender === "bot") {
          lastMessage.isStreaming = false;
        }
        return newMessages;
      });

    } catch (error) {
      console.error("Error sending message:", error);
      setMessages((prev) => {
        const newMessages = [...prev];
        const lastMessage = newMessages[newMessages.length - 1];
        if (lastMessage && lastMessage.sender === "bot") {
          lastMessage.text = "Error: Could not connect to the server.";
          lastMessage.isStreaming = false;
        }
        return newMessages;
      });
    } finally {
      setIsTyping(false);
    }
  };

  // Scroll to the bottom whenever messages update
  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="flex items-center justify-center min-h-screen w-full bg-gray-50">
      <div className="flex flex-col h-[90vh] w-full max-w-6xl p-4 bg-white rounded-lg shadow-xl">
        <div ref={chatRef} className="flex-1 overflow-y-auto p-4 flex flex-col space-y-4">
          {messages.map((msg, index) => (
            <div
              key={index}
              className={`p-4 my-1 max-w-lg ${
                msg.sender === "user"
                  ? "bg-cyan-50 border-cyan-500 text-black self-end border-r-4 rounded-l-lg shadow-sm"
                  : "bg-white border-cyan-100 text-black self-start border-l-4 rounded-r-lg shadow-sm"
              }`}
            >
              {msg.sender === "bot" ? (
                <div className="prose prose-headings:text-cyan-700 prose-headings:font-extrabold prose-p:mt-2 prose-p:mb-4 max-w-none">
                  <ReactMarkdown>{msg.text}</ReactMarkdown>
                  {msg.isStreaming && (
                    <span className="ml-1 inline-block w-2 h-4 bg-cyan-600 animate-pulse"></span>
                  )}
                </div>
              ) : (
                msg.text
              )}
            </div>
          ))}
          {isTyping && messages.length > 0 && messages[messages.length - 1].sender === "user" && (
            <div className="p-4 my-1 max-w-lg text-gray-500 italic self-start bg-gray-50 rounded-lg shadow-sm">
              Thinking...
            </div>
          )}
        </div>

        <div className="mt-4 flex gap-2 p-4 bg-gray-50 rounded-lg">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            className="flex-1 bg-white"
            onKeyDown={(e) => e.key === "Enter" && sendMessage()}
            disabled={isTyping}
          />
          <Button 
            onClick={sendMessage} 
            className="bg-cyan-500 hover:bg-cyan-600 text-white transition-colors"
            disabled={isTyping}
          >
            <LuSendHorizontal size="24px" />
          </Button>
        </div>
      </div>
    </div>
  );
}

// import { useState, useEffect, useRef } from "react";
// import { Input } from "../components/input";
// import { Button } from "../components/button";
// import { LuSendHorizontal } from "react-icons/lu";
// import ReactMarkdown from "react-markdown";
// import "../styles/globals.css";

// interface Message {
//   text: string;
//   sender: "user" | "bot";
// }

// export default function ChatApp() {
//   const [messages, setMessages] = useState<Message[]>([]);
//   const [input, setInput] = useState("");
//   const [isTyping, setIsTyping] = useState(false);
//   const chatRef = useRef<HTMLDivElement>(null);

//   const sendMessage = async () => {
//     if (!input.trim()) return;

//     const userMessage: Message = { text: input, sender: "user" };
//     setMessages((prev) => [...prev, userMessage]);
//     setInput("");
//     setIsTyping(true);

//     try {
//       const response = await fetch("/api", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ message: input }),
//       });

//       const data = await response.json();
//       setIsTyping(false);

//       if (data.reply) {
//         const botMessage: Message = { text: data.reply, sender: "bot" };
//         setMessages((prev) => [...prev, botMessage]);
//       } else {
//         console.error("Invalid API response:", data);
//       }
//     } catch (error) {
//       console.error("Error sending message:", error);
//       setIsTyping(false);
//     }
//   };

//   // Scroll to the bottom whenever messages update
//   useEffect(() => {
//     if (chatRef.current) {
//       chatRef.current.scrollTop = chatRef.current.scrollHeight;
//     }
//   }, [messages, isTyping]);

//   return (
//     <div className="flex items-center justify-center h-screen w-full bg-white">
//       <div className="flex flex-col h-[90vh] w-full max-w-6xl p-4 bg-white rounded-lg shadow-lg">
//         <div ref={chatRef} className="flex-1 overflow-y-auto p-4 flex flex-col">
//           {messages.map((msg, index) => (
//             <div
//               key={index}
//               className={`p-2 my-1 max-w-lg ${
//                 msg.sender === "user"
//                   ? "bg-cyan-50 border-cyan-500 text-black self-end border-r-4 rounded-l"
//                   : "border-cyan-50 text-black self-start border-l-4 rounded-r shadow"
//               }`}
//             >
//               {msg.sender === "bot" ? (
//                 <div className="prose prose-headings:text-cyan-700 prose-headings:font-extrabold prose-p:mt-2 prose-p:mb-4">
//                   <ReactMarkdown>{msg.text}</ReactMarkdown>
//                 </div>
//               ) : (
//                 msg.text
//               )}
//             </div>
//           ))}
//           {isTyping && (
//             <div className="p-2 my-1 max-w-lg text-gray-500 italic self-start">
//               Typing...
//             </div>
//           )}
//         </div>

//         <div className="mt-4 flex gap-2">
//           <Input
//             value={input}
//             onChange={(e) => setInput(e.target.value)}
//             placeholder="Type a message..."
//             className="flex-1"
//             onKeyDown={(e) => e.key === "Enter" && sendMessage()}
//           />
//           <Button onClick={sendMessage} className="bg-cyan-300 text-white">
//             <LuSendHorizontal size="30px" />
//           </Button>
//         </div>
//       </div>
//     </div>
//   );
// }


// import { useState, useEffect, useRef } from "react";
// import { Input } from "../components/input";
// import { Button } from "../components/button";
// import { LuSendHorizontal } from "react-icons/lu";
// import ReactMarkdown from "react-markdown";
// import "../styles/globals.css";

// interface Message {
//   text: string;
//   sender: "user" | "bot";
// }

// export default function ChatApp() {
//   const [messages, setMessages] = useState<Message[]>([]);
//   const [input, setInput] = useState("");
//   const [isTyping, setIsTyping] = useState(false);
//   const chatRef = useRef<HTMLDivElement>(null);

//   const sendMessage = async () => {
//     if (!input.trim()) return;

//     const userMessage: Message = { text: input, sender: "user" };
//     setMessages((prev) => [...prev, userMessage]);
//     setInput("");
//     setIsTyping(true);

//     try {
//       const response = await fetch("/api", {
//         method: "POST",
//         headers: { "Content-Type": "application/json" },
//         body: JSON.stringify({ message: input }),
//       });

//       const data = await response.json();
//       setIsTyping(false);

//       if (data.reply) {
//         const botMessage: Message = { text: data.reply, sender: "bot" };
//         setMessages((prev) => [...prev, botMessage]);
//       } else {
//         console.error("Invalid API response:", data);
//       }
//     } catch (error) {
//       console.error("Error sending message:", error);
//       setIsTyping(false);
//     }
//   };

//   // Scroll to the bottom whenever messages update
//   useEffect(() => {
//     if (chatRef.current) {
//       chatRef.current.scrollTop = chatRef.current.scrollHeight;
//     }
//   }, [messages, isTyping]);

//   return (
//     <div className="flex items-center justify-center h-screen w-full bg-white">
//       <div className="flex flex-col h-[90vh] w-full max-w-6xl p-4 bg-white rounded-lg shadow-lg">
//         <div ref={chatRef} className="flex-1 overflow-y-auto p-4 flex flex-col">
//           {messages.map((msg, index) => (
//             <div
//               key={index}
//               className={`p-2 my-1 max-w-lg ${
//                 msg.sender === "user"
//                   ? "bg-cyan-50 border-cyan-500 text-black self-end border-r-4 rounded-l"
//                   : "border-cyan-50 text-black self-start border-l-4 rounded-r shadow"
//               }`}
//             >
//               {msg.sender === "bot" ? (
//                 <div className="prose prose-headings:text-cyan-700 prose-headings:font-extrabold prose-p:mt-2 prose-p:mb-4">
//                   <ReactMarkdown>{msg.text}</ReactMarkdown>
//                 </div>
//               ) : (
//                 msg.text
//               )}
//             </div>
//           ))}
//           {isTyping && (
//             <div className="p-2 my-1 max-w-lg text-gray-500 italic self-start">
//               Typing...
//             </div>
//           )}
//         </div>

//         <div className="mt-4 flex gap-2">
//           <Input
//             value={input}
//             onChange={(e) => setInput(e.target.value)}
//             placeholder="Type a message..."
//             className="flex-1"
//             onKeyDown={(e) => e.key === "Enter" && sendMessage()}
//           />
//           <Button onClick={sendMessage} className="bg-cyan-300 text-white">
//             <LuSendHorizontal size="30px" />
//           </Button>
//         </div>
//       </div>
//     </div>
//   );
// }
