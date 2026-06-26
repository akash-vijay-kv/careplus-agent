import { useState, useCallback, useEffect } from "react";
import { Message } from "../types";
import { sendMessage, getNewSessionId, uploadBloodReport } from "../services/api";

function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2);
}

export function useChat(token: string | null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getNewSessionId()
      .then(setSessionId)
      .catch(() => setSessionId(generateId()));
  }, []);

  const sendUserMessage = useCallback(
    async (content: string) => {
      if (!content.trim() || isLoading) return;

      setError(null);

      const userMessage: Message = {
        id: generateId(),
        role: "user",
        content: content.trim(),
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

      try {
        const response = await sendMessage({
          message: content.trim(),
          session_id: sessionId,
          token: token,
        });

        const assistantMessage: Message = {
          id: generateId(),
          role: "assistant",
          content: response.message,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, assistantMessage]);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "An unexpected error occurred";
        setError(errorMessage);

        const errorAssistantMessage: Message = {
          id: generateId(),
          role: "assistant",
          content:
            "I'm sorry, I'm having trouble connecting right now. Please try again in a moment.",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorAssistantMessage]);
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, isLoading, token]
  );

  const uploadFile = useCallback(
    async (file: File, userText: string) => {
      if (isLoading) return;

      setError(null);

      const displayContent = userText.trim() || `Here are my blood test results`;

      const userMessage: Message = {
        id: generateId(),
        role: "user",
        content: displayContent,
        timestamp: new Date(),
        attachment: {
          name: file.name,
          type: file.type,
          size: file.size,
        },
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

      try {
        const uploadResponse = await uploadBloodReport(file, sessionId);

        if (uploadResponse.status === "error") {
          const errorMsg: Message = {
            id: generateId(),
            role: "assistant",
            content: uploadResponse.message,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, errorMsg]);
          setIsLoading(false);
          return;
        }

        const agentMessage = userText.trim()
          ? `${userText.trim()}\n\n[Attached file "${file.name}" was parsed with these results:\n${uploadResponse.message}]`
          : `I uploaded a blood report file "${file.name}". The system parsed the following results:\n${uploadResponse.message}\n\nPlease store these results and provide insights on them.`;

        const response = await sendMessage({
          message: agentMessage,
          session_id: sessionId,
          token: token,
        });

        const assistantMessage: Message = {
          id: generateId(),
          role: "assistant",
          content: response.message,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, assistantMessage]);
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : "An unexpected error occurred";
        setError(errorMessage);

        const errorAssistantMessage: Message = {
          id: generateId(),
          role: "assistant",
          content:
            "I'm sorry, I had trouble processing your file. Please try again or manually enter your blood results.",
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorAssistantMessage]);
      } finally {
        setIsLoading(false);
      }
    },
    [sessionId, isLoading, token]
  );

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
    getNewSessionId()
      .then(setSessionId)
      .catch(() => setSessionId(generateId()));
  }, []);

  return {
    messages,
    isLoading,
    error,
    sessionId,
    sendUserMessage,
    uploadFile,
    clearChat,
  };
}
