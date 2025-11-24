import {
  CameraControls,
  ContactShadows,
  Environment,
  Text,
} from "@react-three/drei";
import { Suspense, useEffect, useRef, useState } from "react";
import { useChat } from "../hooks/useChat";
import { Avatar } from "./Avatar";

const Dots = (props) => {
  const { loading } = useChat();
  const [loadingText, setLoadingText] = useState("");
  useEffect(() => {
    if (loading) {
      const interval = setInterval(() => {
        setLoadingText((loadingText) => {
          if (loadingText.length > 2) {
            return ".";
          }
          return loadingText + ".";
        });
      }, 800);
      return () => clearInterval(interval);
    } else {
      setLoadingText("");
    }
  }, [loading]);
  if (!loading) return null;
  return (
    <group {...props}>
      <Text fontSize={0.14} anchorX={"left"} anchorY={"bottom"}>
        {loadingText}
        <meshBasicMaterial attach="material" color="black" />
      </Text>
    </group>
  );
};

export const Experience = ({ isActive = true }) => {
  const cameraControls = useRef();
  const { cameraZoomed, message, onMessagePlayed } = useChat();
  const [audio, setAudio] = useState();

  useEffect(() => {
    cameraControls.current.setLookAt(0, 2, 5, 0, 1.5, 0);
  }, []);

  useEffect(() => {
    if (cameraZoomed) {
      cameraControls.current.setLookAt(0, 1.5, 1.5, 0, 1.5, 0, true);
    } else {
      cameraControls.current.setLookAt(0, 2.2, 5, 0, 1.0, 0, true);
    }
  }, [cameraZoomed]);

  // Handle audio for human avatar
  useEffect(() => {
    // Cleanup previous audio
    if (audio) {
      audio.pause();
      audio.src = "";
      setAudio(null);
    }

    if (!message) return;

    if (message.audio && isActive) {
      console.log("👨 Human Avatar: Playing audio");
      const audioSrc = message.audio.startsWith("data:")
        ? message.audio
        : `data:audio/mp3;base64,${message.audio}`;
      const audioElement = new Audio(audioSrc);
      audioElement
        .play()
        .catch((error) => console.error("Audio playback failed:", error));
      setAudio(audioElement);
      audioElement.onended = onMessagePlayed;
    }
  }, [message, isActive, onMessagePlayed]);

  // Cleanup audio on component unmount
  useEffect(() => {
    return () => {
      if (audio) {
        audio.pause();
        audio.src = "";
      }
    };
  }, []);

  return (
    <>
      <CameraControls ref={cameraControls} />
      <Environment preset="sunset" />
      {/* Wrapping Dots into Suspense to prevent Blink when Troika/Font is loaded */}
      <Suspense>
        <Dots position-y={1.75} position-x={-0.02} />
      </Suspense>
      <Avatar isActive={isActive} audio={audio} />
      <ContactShadows opacity={0.7} />
    </>
  );
};
