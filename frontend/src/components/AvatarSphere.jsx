/**
 * AvatarSphere.jsx — Buğra'nın dijital temsili.
 *
 * State davranışları:
 *   idle    → yavaş rotasyon + floating bob
 *   thinking → hızlı rotasyon + bass'a göre scale
 *   speaking → vertex displacement (FFT verisi)
 *
 * ParticleCloud: 800 nokta, speaking state'inde dışa saçılır.
 */
import { useRef, useMemo, useEffect } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import useStore from '../store/useStore.js';
import { PARTICLE_COUNT, SPHERE_RADIUS, SPHERE_SEGMENTS } from '../config.js';

// ── Parçacık Bulutu ──────────────────────────────────────────────────
function ParticleCloud({ sphereState, analyserData }) {
  const pointsRef = useRef();

  // 800 noktayı küre kabuğu üzerinde dağıt (r: 2.8–4.2)
  const { positions, origPositions } = useMemo(() => {
    const pos = new Float32Array(PARTICLE_COUNT * 3);
    const orig = new Float32Array(PARTICLE_COUNT * 3);
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const r = 2.8 + Math.random() * 1.4;
      const x = r * Math.sin(phi) * Math.cos(theta);
      const y = r * Math.sin(phi) * Math.sin(theta);
      const z = r * Math.cos(phi);
      pos[i * 3] = orig[i * 3] = x;
      pos[i * 3 + 1] = orig[i * 3 + 1] = y;
      pos[i * 3 + 2] = orig[i * 3 + 2] = z;
    }
    return { positions: pos, origPositions: orig };
  }, []);

  useFrame((_, delta) => {
    if (!pointsRef.current) return;
    const attr = pointsRef.current.geometry.attributes.position;

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const ox = origPositions[i * 3];
      const oy = origPositions[i * 3 + 1];
      const oz = origPositions[i * 3 + 2];

      let scale = 1.0;
      if (sphereState === 'speaking' && analyserData.length > 0) {
        const fi = Math.floor((i / PARTICLE_COUNT) * analyserData.length);
        const fv = Math.max(0, (analyserData[fi] + 100) / 100);
        scale = 1.0 + fv * 0.55;
      } else if (sphereState === 'thinking') {
        scale = 1.0 + Math.sin(Date.now() * 0.004 + i * 0.12) * 0.12;
      }

      attr.array[i * 3] = ox * scale;
      attr.array[i * 3 + 1] = oy * scale;
      attr.array[i * 3 + 2] = oz * scale;
    }
    attr.needsUpdate = true;
    pointsRef.current.rotation.y += delta * 0.08;
    pointsRef.current.rotation.x += delta * 0.03;
  });

  return (
    <points ref={pointsRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          array={positions}
          count={PARTICLE_COUNT}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.022}
        color="#7c3aed"
        transparent
        opacity={0.55}
        sizeAttenuation
      />
    </points>
  );
}

// ── Ana küre ─────────────────────────────────────────────────────────
export default function AvatarSphere() {
  const meshRef = useRef();
  const origPositions = useRef(null);

  const sphereState = useStore((s) => s.sphereState);
  const analyserData = useStore((s) => s.analyserData);

  // Three.js objeleri — bir kere oluşturulur
  const geometry = useMemo(
    () => new THREE.SphereGeometry(SPHERE_RADIUS, SPHERE_SEGMENTS, SPHERE_SEGMENTS),
    [],
  );
  const material = useMemo(
    () =>
      new THREE.MeshStandardMaterial({
        color: new THREE.Color('#120024'),
        emissive: new THREE.Color('#1a0533'),
        emissiveIntensity: 1.6,
        roughness: 0.18,
        metalness: 0.85,
      }),
    [],
  );

  // Hedef emissive renkler (state başına)
  const TARGET_COLORS = useMemo(
    () => ({
      idle: new THREE.Color('#1a0533'),
      thinking: new THREE.Color('#0a1a4a'),
      speaking: new THREE.Color('#003a4a'),
    }),
    [],
  );

  useEffect(() => {
    // Vertex orijinlerini sakla
    origPositions.current = Float32Array.from(
      geometry.attributes.position.array,
    );
    return () => {
      geometry.dispose();
      material.dispose();
    };
  }, [geometry, material]);

  useFrame((_, delta) => {
    if (!meshRef.current || !origPositions.current) return;
    const mesh = meshRef.current;
    const pos = geometry.attributes.position;
    const now = Date.now();

    // Emissive geçişi (lerp)
    const targetColor = TARGET_COLORS[sphereState] ?? TARGET_COLORS.idle;
    material.emissive.lerp(targetColor, Math.min(delta * 2.5, 1));

    if (sphereState === 'idle') {
      mesh.rotation.y += delta * 0.28;
      mesh.rotation.x += delta * 0.06;
      mesh.position.y = Math.sin(now * 0.001) * 0.16;
      mesh.scale.setScalar(1.0);

      // Vertex'leri orijinaline geri çek (lerp)
      for (let i = 0; i < pos.count * 3; i++) {
        pos.array[i] += (origPositions.current[i] - pos.array[i]) * 0.08;
      }
      pos.needsUpdate = true;
    } else if (sphereState === 'thinking') {
      mesh.rotation.y += delta * 1.6;
      mesh.position.y = Math.sin(now * 0.003) * 0.08;

      const bassVal =
        analyserData.length > 0
          ? Math.max(0, (analyserData[2] + 100) / 100)
          : 0.3;
      const targetScale = 1 + bassVal * 0.18;
      mesh.scale.setScalar(
        mesh.scale.x + (targetScale - mesh.scale.x) * delta * 4,
      );

      // Hafif titreşim
      for (let i = 0; i < pos.count; i++) {
        const osc = Math.sin(now * 0.006 + i * 0.035) * 0.04;
        pos.array[i * 3] = origPositions.current[i * 3] * (1 + osc);
        pos.array[i * 3 + 1] = origPositions.current[i * 3 + 1] * (1 + osc);
        pos.array[i * 3 + 2] = origPositions.current[i * 3 + 2] * (1 + osc);
      }
      pos.needsUpdate = true;
    } else if (sphereState === 'speaking') {
      mesh.rotation.y += delta * 0.5;
      mesh.position.y = Math.sin(now * 0.0012) * 0.12;
      mesh.scale.setScalar(1.0);

      if (analyserData.length > 0) {
        for (let i = 0; i < pos.count; i++) {
          const fi = Math.floor((i / pos.count) * analyserData.length);
          const fv = Math.max(0, (analyserData[fi] + 100) / 100);
          const disp =
            fv * 0.38 + Math.sin(now * 0.002 + i * 0.01) * 0.04;

          const ox = origPositions.current[i * 3];
          const oy = origPositions.current[i * 3 + 1];
          const oz = origPositions.current[i * 3 + 2];
          const len = Math.sqrt(ox * ox + oy * oy + oz * oz) || 1;

          pos.array[i * 3] = ox + (ox / len) * disp;
          pos.array[i * 3 + 1] = oy + (oy / len) * disp;
          pos.array[i * 3 + 2] = oz + (oz / len) * disp;
        }
        pos.needsUpdate = true;
        geometry.computeVertexNormals();
      }
    }
  });

  return (
    <group>
      <mesh ref={meshRef} geometry={geometry} material={material} />
      <ParticleCloud sphereState={sphereState} analyserData={analyserData} />
    </group>
  );
}
