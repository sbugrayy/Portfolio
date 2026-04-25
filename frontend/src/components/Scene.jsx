/**
 * Scene.jsx — Ana Three.js canvas sarmalayıcısı.
 * Işıklar, AvatarSphere ve bloom post-processing burada.
 */
import { Suspense } from 'react';
import { Canvas } from '@react-three/fiber';
import { EffectComposer, Bloom } from '@react-three/postprocessing';
import AvatarSphere from './AvatarSphere.jsx';

export default function Scene() {
  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 0 }}>
      <Canvas
        camera={{ position: [0, 0, 6], fov: 60, near: 0.1, far: 100 }}
        gl={{ antialias: true, alpha: true, powerPreference: 'high-performance' }}
        style={{ background: 'transparent' }}
        dpr={[1, 2]}
      >
        <Suspense fallback={null}>
          {/* Işıklar */}
          <ambientLight intensity={0.08} />
          <pointLight position={[4, 4, 4]} color="#7c3aed" intensity={3} />
          <pointLight position={[-4, -3, 4]} color="#06b6d4" intensity={2} />
          <pointLight position={[0, -5, -4]} color="#1e1b4b" intensity={0.8} />

          {/* Ana küre + parçacık bulutu */}
          <AvatarSphere />

          {/* Post-processing: bloom */}
          <EffectComposer>
            <Bloom
              intensity={0.7}
              luminanceThreshold={0.65}
              luminanceSmoothing={0.85}
              mipmapBlur
            />
          </EffectComposer>
        </Suspense>
      </Canvas>
    </div>
  );
}
