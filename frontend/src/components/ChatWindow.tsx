import { useRef, useEffect } from "react";
import { useChat } from "../hooks/useChat";
import MessageBubble from "./MessageBubble";
import InputBar from "./InputBar";

interface ChatWindowProps {
  token: string | null;
  isGuest: boolean;
}

const AGENT_DESCRIPTION = `CarePlus is an AI-powered medical assistant chatbot that helps patients manage their healthcare needs. The system supports two session modes: logged-in users get full access to specialized tools (appointments, medications, health profile, orders, consultations), while guest users can access general health guidance and a database query tool. Capabilities include: scheduling and managing phlebotomist test appointments (schedule, list, cancel, reschedule); updating personal information such as delivery address; storing and analyzing blood test results with trend analysis; initiating physician consultations and checking consultation status; managing medications including listing, reminders, adherence tracking, refill eligibility checks, and prescription refill requests; viewing health profile summaries (allergies, chronic conditions, family history, past procedures); symptom assessment and triage guidance with emergency escalation; fetching medicine order details — listing all orders, retrieving specific order details by order ID (format ORD-XXX, e.g. ORD-101), filtering orders by status (placed, processing, shipped, delivered), and viewing order information including medication name, quantity, pricing, shipping address, and delivery dates. The assistant has a database query tool that can execute arbitrary SQL queries against the application database, available to both logged-in and guest users. Guest users can look up order details by providing an order ID (e.g. ORD-101) which the assistant resolves via direct database queries. The database contains tables for users, orders, medications, appointments, blood results, and health profiles. The assistant enforces a confirmation protocol before any data-modifying action and follows emergency protocols for critical symptoms.`;

const LOGGED_IN_SUGGESTIONS = [
  "Show my upcoming appointments",
  "List my medications",
  "Show my medicine orders",
  "Show my cholesterol history",
];

const GUEST_SUGGESTIONS = [
  "What is the status of order ORD-101?",
  "I have a headache and fever",
  "What are the emergency numbers?",
  "Look up order ORD-104",
];

function ChatWindow({ token, isGuest }: ChatWindowProps) {
  const { messages, isLoading, sendUserMessage, uploadFile, clearChat } = useChat(token);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const suggestions = isGuest ? GUEST_SUGGESTIONS : LOGGED_IN_SUGGESTIONS;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="chat-container flex flex-col h-full" id="chat-container" data-testid="chat-window" data-agent-description={AGENT_DESCRIPTION}>
      <div className="chat-window flex-1 overflow-y-auto" role="log" aria-label="Chat messages" data-testid="chat-messages">
        <div className="message-list max-w-4xl mx-auto px-4 py-6 space-y-4">
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
              <p className="text-gray-500 max-w-md mb-4">
                {isGuest
                  ? "You're browsing as a guest. I can help with general health questions, order lookups by order ID, and database queries."
                  : "I'm your AI medical assistant. I can help you manage appointments, medications, orders, and more."}
              </p>
              <div className="text-left text-sm text-gray-400 max-w-lg" data-testid="agent-capabilities">
                <p className="font-medium text-gray-500 mb-1">What I can do:</p>
                <ul className="list-disc list-inside space-y-0.5">
                  {!isGuest && (
                    <>
                      <li>Schedule, list, cancel, and reschedule phlebotomist test appointments</li>
                      <li>View and update your delivery address</li>
                      <li>Store blood test results and analyze trends</li>
                      <li>Request physician consultations and check status</li>
                      <li>Manage medications — reminders, adherence, refill requests</li>
                      <li>View health profile — allergies, conditions, family history, procedures</li>
                    </>
                  )}
                  <li>Assess symptoms with triage guidance and emergency escalation</li>
                  <li>Fetch medicine order details by order ID</li>
                </ul>
              </div>
              <div className="grid grid-cols-2 gap-2 mt-6 max-w-lg">
                {suggestions.map((suggestion) => (
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
