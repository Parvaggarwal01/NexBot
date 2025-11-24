import { useRef, useState, useEffect } from "react";
import { useChat } from "../hooks/useChat";

export const UI = ({ hidden, chatMode = "human", onModeChange, ...props }) => {
  const input = useRef();
  const {
    chat,
    loading,
    cameraZoomed,
    setCameraZoomed,
    message,
    setIsTyping: setGlobalIsTyping,
  } = useChat();
  const [textChatMode, setTextChatMode] = useState(chatMode === "text"); // internal text chat toggle
  const [chatHistory, setChatHistory] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  // Sync internal textChatMode with external chatMode pro
  useEffect(() => {
    setTextChatMode(chatMode === "text");
  }, [chatMode]);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory, isTyping]);

  const sendMessage = async () => {
    const text = input.current.value;
    if (!loading && !message && text.trim()) {
      if (chatMode === "text") {
        setChatHistory((prev) => [
          ...prev,
          { type: "user", content: text, timestamp: Date.now() },
        ]);
        setIsTyping(true);
        input.current.value = ""; // Clear input immediately

        try {
          const response = await fetch("http://localhost:5001/chat-text", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text }),
          });

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const data = await response.json();

          setChatHistory((prev) => [
            ...prev,
            {
              type: "assistant",
              content:
                data.response ||
                data.message ||
                "Sorry, I could not process your request.",
              timestamp: Date.now(),
            },
          ]);
        } catch (error) {
          console.error("Error in text chat:", error);
          setChatHistory((prev) => [
            ...prev,
            {
              type: "assistant",
              content:
                "Sorry, there was an error processing your request. Please try again.",
              timestamp: Date.now(),
            },
          ]);
        } finally {
          setIsTyping(false);
        }
      } else {
        // 3D mode
        setGlobalIsTyping(false); // Clear typing state when sending
        chat(text);
        input.current.value = "";
      }
    }
  };

  // Enhanced Markdown Formatter
  const formatMarkdown = (text) => {
    return text
      .replace(/\*\*(.*?)\*\*/g, "<strong class='text-indigo-900'>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em class='text-gray-600'>$1</em>")
      .replace(
        /`(.*?)`/g,
        '<code class="bg-gray-100 text-red-500 px-1.5 py-0.5 rounded text-sm font-mono border border-gray-200">$1</code>'
      )
      .replace(
        /### (.*?)(\n|$)/g,
        '<h3 class="text-lg font-bold text-gray-800 mt-4 mb-2 border-b pb-1">$1</h3>'
      )
      .replace(
        /## (.*?)(\n|$)/g,
        '<h2 class="text-xl font-bold text-gray-900 mt-6 mb-3 border-b pb-2">$1</h2>'
      )
      .replace(
        /# (.*?)(\n|$)/g,
        '<h1 class="text-2xl font-extrabold text-gray-900 mt-6 mb-4">$1</h1>'
      )
      .replace(/\n- /g, "<br/>• ")
      .replace(/\n\d+\. /g, "<br/>• ")
      .replace(/\n/g, "<br/>");
  };

  if (hidden) {
    return null;
  }

  return (
    <>
      {/* ================= TEXT CHAT MODE ================= */}
      {(chatMode === "text" || textChatMode) && (
        <div className="fixed inset-0 z-20 bg-gray-50 flex flex-col font-sans text-gray-800">
          {/* Professional Header */}
          <header className="bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center sticky top-0 z-10">
            <div className="flex items-center gap-3">
              <div>
                <h1 className="text-lg font-bold text-gray-900 leading-tight">
                  Policy Assistant
                </h1>
                <div className="flex items-center gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                  <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">
                    Online
                  </p>
                </div>
              </div>
            </div>

            <button
              onClick={() => setTextChatMode(false)}
              className="group flex items-center gap-2 px-4 py-2 rounded-lg bg-white border border-gray-200 hover:bg-gray-50 hover:border-gray-300 transition-all text-sm font-medium text-gray-700 shadow-sm"
            >
              <span>Switch to Avatar</span>
              <svg
                className="w-4 h-4 text-indigo-500 group-hover:scale-110 transition-transform"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                />
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
            </button>
          </header>

          {/* Chat Area - Centered Container */}
          <div className="flex-1 overflow-y-auto scroll-smooth">
            <div className="max-w-4xl mx-auto px-4 py-8 flex flex-col gap-6 min-h-full">
              {/* Empty State / Welcome Screen */}
              {chatHistory.length === 0 ? (
                <div className="flex flex-col items-center justify-center flex-1 mt-10 text-center">
                  <div className="w-20 h-20 bg-indigo-100 rounded-full flex items-center justify-center mb-6 shadow-inner">
                    <span className="text-4xl">🎓</span>
                  </div>
                  <h2 className="text-3xl font-bold text-gray-900 mb-3">
                    How can I help you today?
                  </h2>
                  <p className="text-gray-500 max-w-md mb-10 text-lg">
                    I'm trained on all educational guidelines. Ask me anything
                    about policies, procedures, or student care.
                  </p>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-2xl">
                    {[
                      {
                        icon: "📋",
                        title: "Attendance Policy",
                        desc: "What is the waiver policy?",
                      },
                      {
                        icon: "🌟",
                        title: "CARE Guidelines",
                        desc: "Explain student care protocols",
                      },
                      {
                        icon: "🗓️",
                        title: "Exam Procedures",
                        desc: "What are the rules for finals?",
                      },
                      {
                        icon: "⚖️",
                        title: "Code of Conduct",
                        desc: "Student disciplinary actions",
                      },
                    ].map((item, idx) => (
                      <button
                        key={idx}
                        onClick={() => {
                          input.current.value = item.desc;
                          sendMessage();
                        }}
                        className="flex items-start gap-4 p-4 rounded-xl border border-gray-200 bg-white hover:border-indigo-300 hover:shadow-md hover:-translate-y-0.5 transition-all text-left group"
                      >
                        <span className="text-2xl group-hover:scale-110 transition-transform duration-300">
                          {item.icon}
                        </span>
                        <div>
                          <div className="font-semibold text-gray-800 group-hover:text-indigo-600 transition-colors">
                            {item.title}
                          </div>
                          <div className="text-sm text-gray-500 mt-1">
                            {item.desc}
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                /* Message History */
                chatHistory.map((msg, index) => (
                  <div
                    key={index}
                    className={`flex gap-4 ${
                      msg.type === "user" ? "flex-row-reverse" : "flex-row"
                    } animate-slide-up`}
                  >
                    {/* Avatar */}
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                        msg.type === "user"
                          ? "bg-indigo-600 text-white"
                          : "bg-emerald-600 text-white"
                      }`}
                    >
                      {msg.type === "user" ? (
                        <svg
                          className="w-5 h-5"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                          />
                        </svg>
                      ) : (
                        <span className="text-sm font-bold">AI</span>
                      )}
                    </div>

                    {/* Bubble */}
                    <div
                      className={`max-w-[85%] lg:max-w-[75%] rounded-2xl px-6 py-4 shadow-sm ${
                        msg.type === "user"
                          ? "bg-indigo-600 text-white rounded-tr-sm"
                          : "bg-white border border-gray-200 text-gray-800 rounded-tl-sm"
                      }`}
                    >
                      {msg.type === "assistant" ? (
                        <div
                          className="prose prose-sm max-w-none prose-headings:text-gray-800 prose-p:text-gray-700 prose-a:text-indigo-600"
                          dangerouslySetInnerHTML={{
                            __html: formatMarkdown(msg.content),
                          }}
                        />
                      ) : (
                        <p className="text-[15px] leading-relaxed">
                          {msg.content}
                        </p>
                      )}
                      <div
                        className={`text-[10px] mt-2 opacity-70 ${
                          msg.type === "user"
                            ? "text-indigo-100 text-right"
                            : "text-gray-400"
                        }`}
                      >
                        {new Date(msg.timestamp).toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </div>
                    </div>
                  </div>
                ))
              )}

              {/* Loading Indicator */}
              {isTyping && (
                <div className="flex gap-4 items-center">
                  <div className="w-8 h-8 rounded-full bg-emerald-600 text-white flex items-center justify-center flex-shrink-0">
                    <span className="text-sm font-bold">AI</span>
                  </div>
                  <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm flex items-center gap-1.5">
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></span>
                    <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          </div>

          {/* Floating Input Area */}
          <div className="bg-gradient-to-t from-white via-white to-transparent pb-6 pt-2 px-4">
            <div className="max-w-4xl mx-auto relative">
              <div className="bg-white rounded-2xl shadow-[0_0_15px_rgba(0,0,0,0.1)] border border-gray-200 p-2 flex items-end gap-2">
                <textarea
                  ref={input}
                  placeholder="Ask a question regarding policies..."
                  className="w-full max-h-32 min-h-[50px] bg-transparent border-0 focus:ring-0 text-gray-800 placeholder-gray-400 resize-none py-3 px-3 scrollbar-hide"
                  rows={1}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      sendMessage();
                    }
                    // Auto-resize height
                    e.target.style.height = "auto";
                    e.target.style.height = e.target.scrollHeight + "px";
                  }}
                  onInput={(e) => {
                    e.target.style.height = "auto";
                    e.target.style.height = e.target.scrollHeight + "px";
                  }}
                />
                <button
                  disabled={isTyping}
                  onClick={sendMessage}
                  className={`p-3 rounded-xl flex-shrink-0 transition-all duration-200 ${
                    isTyping
                      ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                      : "bg-indigo-600 text-white hover:bg-indigo-700 shadow-md hover:shadow-lg transform hover:-translate-y-0.5"
                  }`}
                >
                  <svg
                    className="w-5 h-5 rotate-90"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                    />
                  </svg>
                </button>
              </div>
              <div className="text-center text-xs text-gray-400 mt-3">
                AI can make mistakes. Please verify policy details with official
                documents.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ================= 3D AVATAR MODE (Unchanged logic, slight style tweaks) ================= */}
      {(chatMode === "human" || chatMode === "nexbot") && !textChatMode && (
        <div className="fixed inset-0 z-10 pointer-events-none flex flex-col justify-between p-6">
          {/* 3D Header */}
          <div className="pointer-events-auto self-start bg-white/80 backdrop-blur-md border border-white/20 p-4 rounded-2xl shadow-lg hover:bg-white transition-all">
            <h1 className="font-black text-xl text-gray-800 tracking-tight">
              Policy Assistant 🎓
            </h1>
            <p className="text-sm text-gray-600 font-medium">
              {chatMode === "human"
                ? "👨 Human Avatar Mode"
                : chatMode === "nexbot"
                ? "🤖 NexBot Robot Mode"
                : "Interactive Avatar Mode"}
            </p>
          </div>

          {/* 3D Controls */}
          <div className="absolute right-6 top-1/2 -translate-y-1/2 flex flex-col gap-3 pointer-events-auto">
            {/* Switch Button */}
            <button
              onClick={() => setTextChatMode(true)}
              className="bg-white hover:bg-gray-50 text-gray-800 p-3 rounded-xl shadow-lg border border-gray-200 transition-all hover:scale-105 group relative"
            >
              <svg
                className="w-6 h-6"
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
              <span className="absolute right-full mr-3 top-1/2 -translate-y-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                Text Mode
              </span>
            </button>

            <button
              onClick={() => setCameraZoomed(!cameraZoomed)}
              className="bg-white hover:bg-gray-50 text-gray-800 p-3 rounded-xl shadow-lg border border-gray-200 transition-all hover:scale-105"
            >
              {cameraZoomed ? (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                  className="w-6 h-6"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607zM13.5 10.5h-6"
                  />
                </svg>
              ) : (
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                  className="w-6 h-6"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607zM10.5 7.5v6m3-3h-6"
                  />
                </svg>
              )}
            </button>

            <button
              onClick={() => {
                const body = document.querySelector("body");
                if (body.classList.contains("greenScreen")) {
                  body.classList.remove("greenScreen");
                } else {
                  body.classList.add("greenScreen");
                }
              }}
              className="bg-white hover:bg-gray-50 text-gray-800 p-3 rounded-xl shadow-lg border border-gray-200 transition-all hover:scale-105"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
                className="w-6 h-6"
              >
                <path
                  strokeLinecap="round"
                  d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z"
                />
              </svg>
            </button>
          </div>

          {/* 3D Input */}
          <div className="pointer-events-auto max-w-2xl w-full mx-auto">
            <div className="flex items-end gap-2 bg-white/90 backdrop-blur-lg p-2 rounded-2xl shadow-2xl border border-white/50">
              <input
                className="w-full bg-transparent border-none focus:ring-0 p-3 text-gray-800 placeholder-gray-500"
                placeholder="Speak to your avatar..."
                ref={input}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    sendMessage();
                  }
                }}
                onInput={(e) => {
                  // Trigger thinking animation when user starts typing
                  if (e.target.value.trim().length > 0) {
                    setGlobalIsTyping(true);
                  } else {
                    setGlobalIsTyping(false);
                  }
                }}
                onFocus={() => {
                  // Also trigger when input is focused and has content
                  if (input.current && input.current.value.trim().length > 0) {
                    setGlobalIsTyping(true);
                  }
                }}
                onBlur={() => {
                  // Stop thinking when input loses focus
                  setGlobalIsTyping(false);
                }}
              />
              <button
                disabled={loading || message}
                onClick={sendMessage}
                className={`p-3 rounded-xl font-bold transition-all ${
                  loading || message
                    ? "bg-gray-200 text-gray-400"
                    : "bg-indigo-600 text-white hover:bg-indigo-700 shadow-lg"
                }`}
              >
                <svg
                  className="w-5 h-5 rotate-90"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};
