/**
 * StemVisualizer.jsx — Opsiyonel mini DAW gösterge.
 * Sol alt köşede, FFT verisiyle frekans çubuğu çizer.
 */
import { useEffect, useRef } from 'react';
import useStore from '../store/useStore.js';
import styles from '../styles/StemVisualizer.module.css';

export default function StemVisualizer() {
  const analyserData = useStore((s) => s.analyserData);
  const sphereState = useStore((s) => s.sphereState);
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || analyserData.length === 0) return;

    const ctx = canvas.getContext('2d');
    const { width, height } = canvas;
    ctx.clearRect(0, 0, width, height);

    const barW = width / analyserData.length;

    analyserData.forEach((val, i) => {
      const norm = Math.max(0, (val + 100) / 100);
      const barH = norm * height;
      const hue = 220 + (i / analyserData.length) * 140;
      ctx.fillStyle = `hsla(${hue}, 80%, 65%, 0.85)`;
      ctx.fillRect(i * barW, height - barH, Math.max(barW - 1, 1), barH);
    });
  }, [analyserData]);

  if (sphereState === 'idle') return null;

  return (
    <div className={styles.container}>
      <span className={styles.label}>AUDIO</span>
      <canvas ref={canvasRef} width={110} height={36} className={styles.canvas} />
    </div>
  );
}
