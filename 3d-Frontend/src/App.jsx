import { Loader } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { Leva } from "leva";
import { useState, useEffect } from "react";
import { NexBot } from "./components/NexBot";
import { UI } from "./components/UI";
import ErrorBoundary from "./components/ErrorBoundary";
import { useChat } from "./hooks/useChat";

function App() {
  const [avatarType, setAvatarType] = useState("text"); // 'nexbot' or 'text'

  const handleAvatarChange = (newAvatarType) => {
    setAvatarType(newAvatarType);
    console.log(
      `🎭 Avatar changed to ${newAvatarType} - using British female voice for all avatars`
    );
  };

  const renderAvatar = () => {
    switch (avatarType) {
      case "nexbot":
        return (
          <ErrorBoundary key="nexbot">
            <div className="fixed inset-0 w-full h-full">
              <NexBot />
            </div>
          </ErrorBoundary>
        );
      case "text":
        return null; // Text-only mode handled by UI component
      default:
        return null;
    }
  };

  return (
    <>
      <Loader />
      <Leva hidden />

      {/* Avatar Selection Panel - Right Side */}
      <div className="fixed right-6 top-1/2 -translate-y-1/2 z-50 bg-white/95 backdrop-blur-md rounded-2xl shadow-xl border border-white/50 p-3">
        <div className="flex flex-col gap-2">
          {/* Header */}
          <div className="text-center mb-2">
            <h3 className="text-sm font-bold text-gray-800 mb-1">
              Avatar Mode
            </h3>
            <div className="w-8 h-0.5 bg-gradient-to-r from-black to-gray-600 mx-auto rounded-full"></div>
          </div>

          {/* Avatar Options */}
          <button
            onClick={() => handleAvatarChange("nexbot")}
            className={`group relative p-4 rounded-xl transition-all duration-300 ${
              avatarType === "nexbot"
                ? "bg-black text-white shadow-lg scale-105"
                : "bg-gray-100 hover:bg-gray-200 text-gray-700 hover:scale-105"
            }`}
            title="NexBot Robot (British Female Voice)"
          >
            <div className="flex flex-col items-center gap-2">
              <div className="text-2xl">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="lucide lucide-bot-message-square-icon lucide-bot-message-square"
                >
                  <path d="M12 6V2H8" />
                  <path d="M15 11v2" />
                  <path d="M2 12h2" />
                  <path d="M20 12h2" />
                  <path d="M20 16a2 2 0 0 1-2 2H8.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 4 20.286V8a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2z" />
                  <path d="M9 11v2" />
                </svg>
              </div>
              <span className="text-xs font-medium">Robot</span>
            </div>
            {avatarType === "nexbot" && (
              <div className="absolute -right-1 -top-1 w-3 h-3 bg-green-500 rounded-full border-2 border-white animate-pulse"></div>
            )}
          </button>

          <button
            onClick={() => handleAvatarChange("text")}
            className={`group relative p-4 rounded-xl transition-all duration-300 ${
              avatarType === "text"
                ? "bg-black text-white shadow-lg scale-105"
                : "bg-gray-100 hover:bg-gray-200 text-gray-700 hover:scale-105"
            }`}
            title="Text Only Mode (British Female Voice)"
          >
            <div className="flex flex-col items-center gap-2">
              <div className="text-2xl">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="lucide lucide-messages-square-icon lucide-messages-square"
                >
                  <path d="M16 10a2 2 0 0 1-2 2H6.828a2 2 0 0 0-1.414.586l-2.202 2.202A.71.71 0 0 1 2 14.286V4a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z" />
                  <path d="M20 9a2 2 0 0 1 2 2v10.286a.71.71 0 0 1-1.212.502l-2.202-2.202A2 2 0 0 0 17.172 19H10a2 2 0 0 1-2-2v-1" />
                </svg>
              </div>
              <span className="text-xs font-medium">Text</span>
            </div>
            {avatarType === "text" && (
              <div className="absolute -right-1 -top-1 w-3 h-3 bg-green-500 rounded-full border-2 border-white animate-pulse"></div>
            )}
          </button>
        </div>
      </div>

      <UI chatMode={avatarType} onModeChange={handleAvatarChange} />
      {renderAvatar()}
    </>
  );
}

export default App;
