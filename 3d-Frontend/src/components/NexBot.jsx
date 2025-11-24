/*
NexBot - Spline Robot Component
*/

import React, { useRef, useEffect, useState } from "react";
import Spline from "@splinetool/react-spline";
import { useChat } from "../hooks/useChat";

export function NexBot(props) {
  const splineRef = useRef();
  const { message, onMessagePlayed, isTyping: userIsTyping } = useChat();

  // Animation states
  const [isLoaded, setIsLoaded] = useState(false);
  const [isGreeting, setIsGreeting] = useState(false);
  const [isTalking, setIsTalking] = useState(false);
  const [isThinking, setIsThinking] = useState(false);
  const [audio, setAudio] = useState();
  const [hasGreeted, setHasGreeted] = useState(false);

  // Caption states
  const [showCaption, setShowCaption] = useState(false);
  const [captionText, setCaptionText] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [lastMessageId, setLastMessageId] = useState(null);
  const [captionChunks, setCaptionChunks] = useState([]);
  const [currentChunkIndex, setCurrentChunkIndex] = useState(0);

  // Split text into chunks of 3 lines and display them sequentially
  const typeTextChunked = (fullText, callback) => {
    // Split text into words and create chunks of approximately 3 lines
    const words = fullText.split(" ");
    const chunks = [];
    const wordsPerChunk = Math.ceil(
      words.length / Math.ceil(words.length / 15)
    ); // ~15 words per chunk (3 lines)

    for (let i = 0; i < words.length; i += wordsPerChunk) {
      chunks.push(words.slice(i, i + wordsPerChunk).join(" "));
    }

    setCaptionChunks(chunks);
    setCurrentChunkIndex(0);
    setShowCaption(true);

    // Start typing the first chunk
    typeChunk(chunks[0], 0, chunks.length, chunks, callback);
  };

  // Type individual chunk with typing effect
  const typeChunk = (
    chunkText,
    chunkIndex,
    totalChunks,
    allChunks,
    callback
  ) => {
    setIsTyping(true);
    setCaptionText("");

    let i = 0;
    const typeInterval = setInterval(() => {
      setCaptionText(chunkText.substring(0, i + 1));
      i++;
      if (i >= chunkText.length) {
        clearInterval(typeInterval);
        setIsTyping(false);

        // If there are more chunks, wait and show the next one
        if (chunkIndex < totalChunks - 1) {
          setTimeout(() => {
            const nextChunkIndex = chunkIndex + 1;
            setCurrentChunkIndex(nextChunkIndex);
            typeChunk(
              allChunks[nextChunkIndex],
              nextChunkIndex,
              totalChunks,
              allChunks,
              callback
            );
          }, 2000); // 2 second pause between chunks
        } else {
          // All chunks complete
          if (callback) callback();
        }
      }
    }, 50); // Typing speed
  };

  // Backward compatibility function
  const typeText = (text, callback) => {
    typeTextChunked(text, callback);
  };

  // Greeting animation when model loads
  useEffect(() => {
    if (splineRef.current && isLoaded && !hasGreeted) {
      try {
        console.log("👋 Playing greeting animation");
        // Trigger greeting animation in Spline
        splineRef.current.emitEvent("mouseDown", "greeting");
        setIsGreeting(true);
        setHasGreeted(true);

        // Show greeting caption
        typeText("Robot Transcript: System initialized. Ready for your query.");

        // Return to idle after greeting
        setTimeout(() => {
          setIsGreeting(false);
        }, 3000);
      } catch (error) {
        console.log("Greeting animation error:", error);
      }
    }
  }, [isLoaded, hasGreeted]);

  // Handle messages and audio with Spline animations
  useEffect(() => {
    if (!message) {
      return;
    }

    const currentMessageId = message.text + (message.audio || "");

    // Skip if this is the same message we just processed
    if (currentMessageId === lastMessageId) {
      return;
    }

    setLastMessageId(currentMessageId);

    // Cleanup previous audio
    if (audio) {
      audio.pause();
      audio.src = "";
      setAudio(null);
    }

    console.log("🤖 Spline NexBot received new message:", message);
    if (!message) {
      if (splineRef.current && isLoaded) {
        try {
          splineRef.current.emitEvent("mouseDown", "idle");
        } catch (error) {
          console.log("Idle animation error:", error);
        }
      }
      setIsTalking(false);
      return;
    }

    // Start talking animation in Spline
    if (splineRef.current && isLoaded) {
      try {
        console.log("🎤 Starting talk animation");
        splineRef.current.emitEvent("mouseDown", "talking");
        setIsTalking(true);
      } catch (error) {
        console.log("Talk animation error:", error);
      }
    }

    // Handle audio if available
    if (message.audio) {
      try {
        // Extract base64 data from data URI if present
        const base64Data = message.audio.startsWith("data:")
          ? message.audio.split(",")[1]
          : message.audio;

        // Convert base64 to blob URL for better compatibility
        const byteCharacters = atob(base64Data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const audioBlob = new Blob([byteArray], { type: "audio/mpeg" });
        const audioUrl = URL.createObjectURL(audioBlob);

        const audioElement = new Audio(audioUrl);

        // Start audio immediately while caption is typing for better sync
        console.log("🤖 NexBot: Starting audio with caption");
        audioElement.play().catch(console.error);

        // Show caption with typing effect simultaneously
        typeText(`Robot Transcript: ${message.text || "Speaking..."}`);

        setAudio(audioElement);

        audioElement.onended = () => {
          console.log("💤 Audio finished, stopping talk animation");
          setIsTalking(false);

          // Show ready state after audio completes (only once)
          setTimeout(() => {
            typeText("Robot Transcript: Ready for your next query.");
          }, 500);

          if (splineRef.current && isLoaded) {
            try {
              splineRef.current.emitEvent("mouseDown", "idle");
            } catch (error) {
              console.log("Idle animation error:", error);
            }
          }
          if (onMessagePlayed) {
            onMessagePlayed();
          }
          // Clean up blob URL
          URL.revokeObjectURL(audioUrl);
        };
      } catch (error) {
        console.error("Error playing audio:", error);

        setIsTalking(false);
        if (splineRef.current && isLoaded) {
          try {
            splineRef.current.emitEvent("mouseDown", "idle");
          } catch (error) {
            console.log("Idle animation error:", error);
          }
        }
        if (onMessagePlayed) {
          onMessagePlayed();
        }
      }
    } else {
      // No audio, simulate talking duration
      console.log("📢 No audio, simulating speech duration");
      setTimeout(() => {
        setIsTalking(false);
        if (splineRef.current && isLoaded) {
          try {
            splineRef.current.emitEvent("mouseDown", "idle");
          } catch (error) {
            console.log("Idle animation error:", error);
          }
        }
        if (onMessagePlayed) {
          onMessagePlayed();
        }
      }, 3000);
    }
  }, [message, onMessagePlayed, isLoaded]);

  // Handle user typing - trigger thinking animation
  useEffect(() => {
    if (userIsTyping && !isTalking && isLoaded) {
      if (!isThinking) {
        setIsThinking(true);
        typeText(
          "Robot Transcript: Processing your request... Analyzing data..."
        );

        if (splineRef.current) {
          try {
            splineRef.current.emitEvent("mouseDown", "thinking");
          } catch (error) {
            console.log("Thinking animation error:", error);
          }
        }
      }
    } else if (!userIsTyping && isThinking && !isTalking) {
      // User stopped typing, return to idle
      setTimeout(() => {
        setIsThinking(false);
        if (splineRef.current && isLoaded) {
          try {
            splineRef.current.emitEvent("mouseDown", "idle");
          } catch (error) {
            console.log("Idle animation error:", error);
          }
        }
        typeText("Robot Transcript: Ready for your query.");
      }, 500);
    }
  }, [userIsTyping, isTalking, isThinking, isLoaded]);

  // Cleanup audio on component unmount
  useEffect(() => {
    return () => {
      if (audio) {
        audio.pause();
        audio.src = "";
      }
    };
  }, []);

  // Spline event handlers
  const onLoad = (spline) => {
    splineRef.current = spline;
    setIsLoaded(true);
    console.log("✅ Spline NexBot model loaded successfully");
  };

  const onError = (error) => {
    console.error("❌ Spline loading error:", error);
  };

  return (
    <div
      className="w-full h-full relative overflow-hidden "
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: "transparent",
        backgroundColor: "transparent",
      }}
    >
      {/* Loading indicator */}
      {!isLoaded && (
        <div className="absolute inset-0 flex items-center justify-center z-10">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-white text-lg font-medium">
              Loading NexBot Robot...
            </p>
            <p className="text-white/60 text-sm mt-2">Powered by Spline 3D</p>
          </div>
        </div>
      )}

      {/* Spline Scene - NexBot Robot Model */}
      <Spline
        scene="https://prod.spline.design/VQpbn0QpXVEp2tyt/scene.splinecode"
        onLoad={onLoad}
        onError={onError}
        style={{
          width: "105%",
          height: "110%",
          background: "none",
          pointerEvents: "all",
        }}
      />

      {/* Status indicator overlay */}
      {isLoaded && (
        <div className="absolute bottom-4 left-4 bg-black/50 backdrop-blur-sm text-white px-3 py-2 rounded-full text-sm flex items-center gap-2 z-20">
          <div
            className={`w-2 h-2 rounded-full ${
              isTalking
                ? "bg-green-400 animate-pulse"
                : isGreeting
                ? "bg-blue-400 animate-pulse"
                : isThinking
                ? "bg-yellow-400 animate-pulse"
                : "bg-gray-400"
            }`}
          ></div>
          {isTalking
            ? "Speaking"
            : isGreeting
            ? "Greeting"
            : isThinking
            ? "Thinking"
            : "Ready"}
        </div>
      )}

      {/* Robot Transcript Caption - Matching the second image style */}
      {showCaption && (
        <div className="absolute bottom-40 left-1/2 transform -translate-x-1/2 z-30 max-w-lg w-full px-4">
          <div className="bg-black/20 backdrop-blur-2xl border border-purple-500/60 rounded-xl p-4 shadow-2xl">
            {/* Progress indicator for chunks */}
            {captionChunks.length > 1 && (
              <div className="flex justify-center mb-2 gap-1">
                {captionChunks.map((_, index) => (
                  <div
                    key={index}
                    className={`w-1.5 h-1.5 rounded-full transition-all duration-300 ${
                      index <= currentChunkIndex
                        ? "bg-cyan-400"
                        : "bg-cyan-400/30"
                    }`}
                  />
                ))}
              </div>
            )}

            <div
              className="text-white text-sm leading-relaxed font-mono tracking-wide min-h-[2.5rem]"
              style={{
                fontFamily:
                  "'Courier New', 'JetBrains Mono', 'Fira Code', monospace",
                textShadow: "0 0 8px rgba(6, 182, 212, 0.4)",
                letterSpacing: "0.3px",
              }}
            >
              <span className="text-cyan-300 font-semibold">
                Robot Transcript:{" "}
              </span>
              <span className="text-white">
                {captionText.replace("Robot Transcript: ", "")}
              </span>

              {isTyping && (
                <span className="inline-block w-0.5 h-4 bg-cyan-400 ml-1 animate-pulse"></span>
              )}

              {/* Continue indicator */}
              {!isTyping && currentChunkIndex < captionChunks.length - 1 && (
                <div className="flex items-center justify-center mt-2 text-cyan-300 text-xs">
                  <span className="animate-pulse">Continuing...</span>
                  <div className="flex gap-1 ml-2">
                    <div className="w-0.5 h-0.5 bg-cyan-300 rounded-full animate-bounce"></div>
                    <div className="w-0.5 h-0.5 bg-cyan-300 rounded-full animate-bounce delay-100"></div>
                    <div className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce delay-200"></div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
