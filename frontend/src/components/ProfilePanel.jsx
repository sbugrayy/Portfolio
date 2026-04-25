/**
 * ProfilePanel.jsx — Üst kısımda Buğra hakkında kısa bilgi kartı.
 * GitHub ve LinkedIn linkleri, unvan, okul ve AI avatar etiketi içerir.
 */
import { motion } from 'framer-motion';
import styles from '../styles/ProfilePanel.module.css';

const GITHUB_URL  = 'https://github.com/sbugrayy';
const LINKEDIN_URL = 'https://www.linkedin.com/in/bugra-yildirim';

export default function ProfilePanel() {
  return (
    <motion.div
      className={styles.panel}
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: 'easeOut', delay: 0.3 }}
    >
      {/* Avatar placeholder — initials */}
      <div className={styles.avatar}>BY</div>

      {/* Bilgi */}
      <div className={styles.info}>
        <h1 className={styles.name}>Buğra Yıldırım</h1>
        <p className={styles.title}>
          AI &amp; Deep Learning Engineer&nbsp;
          <span className={styles.badge}>AI Avatar</span>
        </p>
        <p className={styles.school}>
          Balıkesir Üniversitesi · Bilgisayar Mühendisliği
        </p>
      </div>

      {/* Social linkler */}
      <div className={styles.links}>
        <a
          href={GITHUB_URL}
          target="_blank"
          rel="noopener noreferrer"
          className={styles.link}
          title="GitHub"
        >
          {/* GitHub icon */}
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 .5C5.65.5.5 5.65.5 12c0 5.1 3.3 9.42 7.88 10.95.58.1.79-.25.79-.56v-2c-3.2.7-3.87-1.54-3.87-1.54-.53-1.34-1.3-1.7-1.3-1.7-1.06-.72.08-.71.08-.71 1.17.08 1.79 1.2 1.79 1.2 1.04 1.78 2.73 1.27 3.4.97.1-.75.41-1.27.74-1.56-2.56-.29-5.25-1.28-5.25-5.7 0-1.26.45-2.29 1.19-3.09-.12-.29-.52-1.46.11-3.04 0 0 .97-.31 3.18 1.18a11.1 11.1 0 0 1 2.9-.39c.98 0 1.97.13 2.9.39 2.2-1.49 3.17-1.18 3.17-1.18.63 1.58.23 2.75.11 3.04.74.8 1.19 1.83 1.19 3.09 0 4.43-2.7 5.41-5.27 5.69.41.36.78 1.07.78 2.15v3.19c0 .31.21.67.8.56C20.21 21.42 23.5 17.1 23.5 12 23.5 5.65 18.35.5 12 .5z" />
          </svg>
          GitHub
        </a>

        <a
          href={LINKEDIN_URL}
          target="_blank"
          rel="noopener noreferrer"
          className={`${styles.link} ${styles.linkedin}`}
          title="LinkedIn"
        >
          {/* LinkedIn icon */}
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20.45 20.45h-3.56v-5.57c0-1.33-.03-3.04-1.85-3.04-1.85 0-2.13 1.45-2.13 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.45v6.29zM5.34 7.43a2.07 2.07 0 1 1 0-4.14 2.07 2.07 0 0 1 0 4.14zM6.96 20.45H3.7V9h3.26v11.45zM22.23 0H1.77C.79 0 0 .77 0 1.72v20.56C0 23.23.79 24 1.77 24h20.46C23.2 24 24 23.23 24 22.28V1.72C24 .77 23.2 0 22.23 0z" />
          </svg>
          LinkedIn
        </a>
      </div>
    </motion.div>
  );
}
