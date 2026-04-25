import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import AnimatedSection from './AnimatedSection.jsx';
import { certifications, pick } from '../data/portfolio.js';
import useStore from '../store/useStore.js';
import { translations } from '../i18n/translations.js';
import styles from './CertificationsSection.module.css';

const ISSUER_COLORS = {
  'Huawei':                   '#06b6d4',
  'Milli Teknoloji Akademisi': '#a855f7',
  'Akbank':                   '#ec4899',
  'Google':                   '#3b82f6',
  'Balıkesir Teknokent':      '#f59e0b',
  'PAGİT DOGE':               '#f59e0b',
  'Udemy':                    '#10b981',
  'Dil Okulu':                '#6366f1',
};

export default function CertificationsSection() {
  const language = useStore(s => s.language);
  const t = translations[language];
  const [lightbox, setLightbox] = useState(null);

  const openLightbox  = useCallback((cert) => { if (cert.image) setLightbox(cert); }, []);
  const closeLightbox = useCallback(() => setLightbox(null), []);

  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') closeLightbox(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [closeLightbox]);

  return (
    <section id="certifications" className={styles.section}>
      <AnimatedSection className={styles.inner}>
        <span className={styles.ghost} aria-hidden="true">05</span>

        <div className={styles.header}>
          <p className={styles.label}>{t.certificationsLabel}</p>
          <h2 className={styles.title}>{t.certificationsTitle}</h2>
        </div>

        {/* Certificate grid */}
        <div className={styles.grid}>
          {certifications.map((cert, i) => {
            const color = ISSUER_COLORS[cert.issuer] || '#94a3b8';
            return (
              <motion.div
                key={cert.name}
                className={`${styles.card} ${cert.image ? styles.clickable : ''} cursor-target`}
                initial={{ opacity: 0, y: 24 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, amount: 0.05 }}
                transition={{ duration: 0.4, delay: i * 0.05, ease: 'easeOut' }}
                onClick={() => openLightbox(cert)}
                style={{ '--cc': color }}
              >
                {cert.image ? (
                  <div className={styles.imgWrap}>
                    <img
                      src={cert.image}
                      alt={cert.name}
                      className={styles.img}
                      loading="lazy"
                    />
                    <div className={styles.overlay}>
                      <span className={styles.overlayText}>{t.certificationsView}</span>
                    </div>
                    <div className={styles.imgFade} />
                  </div>
                ) : (
                  <div className={styles.placeholder}>
                    <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                      <path d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"/>
                    </svg>
                  </div>
                )}

                <div className={styles.info}>
                  <span
                    className={styles.badge}
                    style={{ color, borderColor: color + '55', background: color + '12' }}
                  >
                    {cert.issuer}
                  </span>
                  <p className={styles.name}>{pick(cert, 'name', language)}</p>
                  {cert.image && (
                    <span className={styles.viewHint}>
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M1 12S5 4 12 4s11 8 11 8-4 8-11 8S1 12 1 12z"/>
                        <circle cx="12" cy="12" r="3"/>
                      </svg>
                      {t.certificationsViewHint}
                    </span>
                  )}
                </div>

                <div className={styles.accentLine} style={{ background: color }} />
              </motion.div>
            );
          })}
        </div>
      </AnimatedSection>

      {/* Lightbox */}
      <AnimatePresence>
        {lightbox && (
          <motion.div
            className={styles.lbBg}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closeLightbox}
          >
            <motion.div
              className={styles.lbBox}
              initial={{ scale: 0.88, opacity: 0, y: 24 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.88, opacity: 0, y: 24 }}
              transition={{ type: 'spring', stiffness: 280, damping: 28 }}
              onClick={e => e.stopPropagation()}
            >
              <div className={styles.lbHeader}>
                <div>
                  <p className={styles.lbIssuer}>{lightbox.issuer}</p>
                  <h3 className={styles.lbName}>{pick(lightbox, 'name', language)}</h3>
                </div>
                <button className={`${styles.lbClose} cursor-target`} onClick={closeLightbox}>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M18 6L6 18M6 6l12 12"/>
                  </svg>
                </button>
              </div>
              <div className={styles.lbImgWrap}>
                <img src={lightbox.image} alt={lightbox.name} className={styles.lbImg} />
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}
