/**
 * SourceCards.jsx — RAG kaynaklarından gelen proje kartları.
 *
 * • Yalnızca /chat response'undaki sources dizisi doluysa render edilir.
 * • Framer Motion ile sağ kenardan stagger'lı giriş.
 * • 12 saniye sonra otomatik kaybolma.
 * • Halüsinasyon yok — yalnızca gerçek metadata'dan kart üretilir.
 */
import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import useStore from '../store/useStore.js';
import styles from '../styles/SourceCards.module.css';
import { SOURCE_CARDS_TIMEOUT_MS } from '../config.js';

const TYPE_LABELS = { json: 'Knowledge', github: 'GitHub', pdf: 'CV' };

export default function SourceCards() {
  const sources = useStore((s) => s.sources);
  const [shown, setShown] = useState(false);

  useEffect(() => {
    if (sources.length > 0) {
      setShown(true);
      const t = setTimeout(() => setShown(false), SOURCE_CARDS_TIMEOUT_MS);
      return () => clearTimeout(t);
    } else {
      setShown(false);
    }
  }, [sources]);

  const validSources = sources.filter((s) => s.project_name || s.source_type);

  if (!shown || validSources.length === 0) return null;

  return (
    <div className={styles.container} aria-label="Kaynak kartları">
      <AnimatePresence>
        {validSources.map((src, idx) => (
          <motion.article
            key={`${src.project_name}-${idx}`}
            className={styles.card}
            initial={{ x: 130, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 130, opacity: 0 }}
            transition={{ delay: idx * 0.1, duration: 0.4, ease: 'easeOut' }}
          >
            <span className={`${styles.badge} ${styles[src.source_type] ?? ''}`}>
              {TYPE_LABELS[src.source_type] ?? src.source_type}
            </span>

            {src.project_name && (
              <h3 className={styles.name}>{src.project_name}</h3>
            )}

            {src.tags?.length > 0 && (
              <div className={styles.tags}>
                {src.tags.slice(0, 3).map((tag) => (
                  <span key={tag} className={styles.tag}>{tag}</span>
                ))}
              </div>
            )}

            {src.github && (
              <a
                href={src.github}
                target="_blank"
                rel="noopener noreferrer"
                className={styles.link}
              >
                GitHub&nbsp;↗
              </a>
            )}
          </motion.article>
        ))}
      </AnimatePresence>
    </div>
  );
}
