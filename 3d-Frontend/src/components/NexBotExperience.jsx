import {
  Environment,
  Float,
  Lightformer,
  ContactShadows,
} from "@react-three/drei";
import { NexBot } from "./NexBot";
import { Suspense } from "react";

export const NexBotExperience = () => {
  return (
    <>
      {/* Lighting */}
      <Environment resolution={256}>
        <group rotation={[-Math.PI / 3, 0, 1]}>
          <Lightformer
            form="circle"
            intensity={4}
            rotation-x={Math.PI / 2}
            position={[0, 5, -9]}
            scale={2}
          />
          <Lightformer
            form="circle"
            intensity={2}
            rotation-y={Math.PI / 2}
            position={[-5, 1, -1]}
            scale={2}
          />
          <Lightformer
            form="circle"
            intensity={2}
            rotation-y={Math.PI / 2}
            position={[-5, -1, -1]}
            scale={2}
          />
          <Lightformer
            form="circle"
            intensity={2}
            rotation-y={-Math.PI / 2}
            position={[10, 1, 0]}
            scale={8}
          />
        </group>
      </Environment>

      {/* Main lighting */}
      <directionalLight
        position={[5, 5, 5]}
        castShadow
        intensity={2}
        shadow-mapSize={[1024, 1024]}
        shadow-camera-near={-10}
        shadow-camera-far={20}
        shadow-camera-top={5}
        shadow-camera-right={5}
        shadow-camera-bottom={-5}
        shadow-camera-left={-5}
      />

      <ambientLight intensity={1} />
      <pointLight position={[10, 10, 10]} intensity={1} />
      <pointLight position={[-10, 10, -10]} intensity={0.5} color="#4444ff" />

      {/* Robot */}
      <Suspense fallback={null}>
        <Float
          speed={2} // Animation speed
          rotationIntensity={0.05} // XYZ rotation intensity
          floatIntensity={0.05} // Up/down float intensity
        >
          <NexBot position={[0, -0.5, 0]} scale={0.3} rotation={[0, 0, 0]} />
        </Float>
      </Suspense>

      {/* Ground/Contact shadows */}
      <ContactShadows
        position={[0, -2, 0]}
        opacity={0.4}
        scale={10}
        blur={1}
        far={10}
        resolution={256}
        color="#000000"
      />

      {/* Background gradient */}
      <mesh position={[0, 0, -5]} scale={[20, 20, 1]}>
        <planeGeometry />
        <meshBasicMaterial color="#1a1a2e" transparent opacity={0.3} />
      </mesh>
    </>
  );
};
