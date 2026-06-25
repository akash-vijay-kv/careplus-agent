import { useRef, useEffect } from "react";
import { useChat } from "../hooks/useChat";
import MessageBubble from "./MessageBubble";
import InputBar from "./InputBar";

function ChatWindow() {
  const { messages, isLoading, sendUserMessage, uploadFile, clearChat } = useChat();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <div className="w-20 h-20 bg-careplus/10 rounded-full flex items-center justify-center mb-4">
              <svg
                className="w-10 h-10 text-careplus"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                />
              </svg>
            </div>
            <h2 className="text-2xl font-semibold text-gray-700 mb-2">
              Welcome to CarePlus
            </h2>
            <p className="text-gray-500 max-w-md">
              I'm your AI medical assistant. I can help you manage appointments,
              medications, blood results, and more. How can I assist you today?
            </p>
            <div className="grid grid-cols-2 gap-2 mt-6 max-w-lg">
              {[
                "Show my upcoming appointments",
                "List my medications",
                "Show my cholesterol history",
                "I need to update my address",
              ].map((suggestion) => (
                <button
                  key={suggestion}
                  onClick={() => sendUserMessage(suggestion)}
                  className="text-sm px-3 py-2 bg-white rounded-lg border border-blue-200 text-gray-600 hover:bg-blue-50 hover:border-blue-300 transition-colors text-left"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {isLoading && (
          <div className="flex items-start gap-3">
            <div className="w-8 h-8 bg-careplus rounded-full flex items-center justify-center flex-shrink-0">
              <svg
                className="w-4 h-4 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                />
              </svg>
            </div>
            <div className="bg-white rounded-2xl rounded-tl-md px-4 py-3 shadow-sm">
              <div className="flex gap-1.5">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.2s]" />
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce [animation-delay:0.4s]" />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="border-t border-blue-100 bg-white/80 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex items-center gap-2 mb-2">
            <button
              onClick={clearChat}
              className="text-xs text-gray-400 hover:text-gray-600 transition-colors"
            >
              New conversation
            </button>
          </div>
          <InputBar onSend={sendUserMessage} onFileUpload={uploadFile} disabled={isLoading} />
        </div>
      </div>
    </div>
  );
}

export default ChatWindow;
