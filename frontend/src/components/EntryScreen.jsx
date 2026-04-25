import { useEffect } from 'react';
import { motion } from 'framer-motion';
import styles from '../styles/EntryScreen.module.css';
import useStore from '../store/useStore.js';

export default function EntryScreen() {
  const setAudioReady = useStore(s => s.setAudioReady);

  // Otomatik geçiş — 2.2 saniye sonra ana sayfaya geç
  useEffect(() => {
    const id = setTimeout(() => setAudioReady(true), 2200);
    return () => clearTimeout(id);
  }, [setAudioReady]);

  return (
    <motion.div
      className={styles.container}
      exit={{ opacity: 0, scale: 0.97, filter: 'blur(10px)' }}
      transition={{ duration: 0.65, ease: 'easeInOut' }}
    >
      <div className={styles.bgGrid} />
      <div className={styles.bgGlow} />
      <div className={styles.bgGlow2} />

      <motion.div
        className={styles.titleGroup}
        initial={{ opacity: 0, y: -32 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15, duration: 0.8, ease: 'easeOut' }}
      >
        <span className={styles.eyebrow}>AI · Avatar · Portfolio</span>
        <h1 className={styles.title}>BUĞRA.AI</h1>
        <p className={styles.subtitle}>Dijital Klon</p>
      </motion.div>

      <motion.p
        className={styles.desc}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.65, duration: 0.8 }}
      >
        Bir portfolyo okumayacaksın — Benimle konuşacaksın...
      </motion.p>

      {/* Yükleme çubuğu */}
      <motion.div
        className={styles.progressWrap}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.9 }}
      >
        <motion.div
          className={styles.progressBar}
          initial={{ scaleX: 0 }}
          animate={{ scaleX: 1 }}
          transition={{ delay: 1.0, duration: 1.1, ease: 'easeInOut' }}
          style={{ transformOrigin: 'left' }}
        />
      </motion.div>
    </motion.div>
  );
}
