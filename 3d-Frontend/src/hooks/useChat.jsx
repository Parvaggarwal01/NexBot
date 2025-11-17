import { createContext, useContext, useEffect, useState } from "react";

const backendUrl = import.meta.env.VITE_API_URL || "http://localhost:5001";

const ChatContext = createContext();

export const ChatProvider = ({ children }) => {
  const chat = async (message) => {
    setLoading(true);
    try {
      const response = await fetch(`${backendUrl}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ message }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Handle different response formats
      let newMessages = [];
      if (data.messages) {
        // Original format
        newMessages = data.messages;
      } else if (data.message) {
        // New backend format
        const messageData = {
          text: data.message,
          audio: data.audio ? `${backendUrl}${data.audio}` : null,
          lipsync: data.lipsync || null,
          facialExpression: "default",
          animation: "Talking",
        };

        // Validate audio file if provided
        if (messageData.audio) {
          try {
            const audioResponse = await fetch(messageData.audio, {
              method: "HEAD",
            });
            if (!audioResponse.ok) {
              console.warn(
                "Audio file not accessible, proceeding without audio"
              );
              messageData.audio = null;
            }
          } catch (audioError) {
            console.warn(
              "Audio validation failed, proceeding without audio:",
              audioError
            );
            messageData.audio = null;
          }
        }

        newMessages = [messageData];
      } else {
        // Fallback
        newMessages = [
          {
            text: "Sorry, I couldn't process your request.",
            audio: null,
            lipsync: null,
            facialExpression: "default",
            animation: "Idle",
          },
        ];
      }

      setMessages((messages) => [...messages, ...newMessages]);
    } catch (error) {
      console.error("Chat error:", error);
      // Add error message
      setMessages((messages) => [
        ...messages,
        {
          text: "Sorry, there was an error processing your request. Please try again.",
          audio: null,
          lipsync: null,
          facialExpression: "sad",
          animation: "Idle",
        },
      ]);
    }
    setLoading(false);
  };
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState();
  const [loading, setLoading] = useState(false);
  const [cameraZoomed, setCameraZoomed] = useState(true);
  const onMessagePlayed = () => {
    setMessages((messages) => messages.slice(1));
  };

  useEffect(() => {
    if (messages.length > 0) {
      setMessage(messages[0]);
    } else {
      setMessage(null);
    }
  }, [messages]);

  return (
    <ChatContext.Provider
      value={{
        chat,
        message,
        onMessagePlayed,
        loading,
        cameraZoomed,
        setCameraZoomed,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
};
