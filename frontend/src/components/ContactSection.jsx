import useInView from '../hooks/useInView.js';
import { social, about } from '../data/portfolio.js';
import useStore from '../store/useStore.js';
import { translations } from '../i18n/translations.js';
import styles from './ContactSection.module.css';

const IconGitHub = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 .5C5.65.5.5 5.65.5 12c0 5.1 3.3 9.42 7.88 10.95.58.1.79-.25.79-.56v-2c-3.2.7-3.87-1.54-3.87-1.54-.53-1.34-1.3-1.7-1.3-1.7-1.06-.72.08-.71.08-.71 1.17.08 1.79 1.2 1.79 1.2 1.04 1.78 2.73 1.27 3.4.97.1-.75.41-1.27.74-1.56-2.56-.29-5.25-1.28-5.25-5.7 0-1.26.45-2.29 1.19-3.09-.12-.29-.52-1.46.11-3.04 0 0 .97-.31 3.18 1.18a11.1 11.1 0 0 1 2.9-.39c.98 0 1.97.13 2.9.39 2.2-1.49 3.17-1.18 3.17-1.18.63 1.58.23 2.75.11 3.04.74.8 1.19 1.83 1.19 3.09 0 4.43-2.7 5.41-5.27 5.69.41.36.78 1.07.78 2.15v3.19c0 .31.21.67.8.56C20.21 21.42 23.5 17.1 23.5 12 23.5 5.65 18.35.5 12 .5z" />
  </svg>
);

const IconLinkedIn = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
    <path d="M20.45 20.45h-3.56v-5.57c0-1.33-.03-3.04-1.85-3.04-1.85 0-2.13 1.45-2.13 2.94v5.67H9.35V9h3.41v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.45v6.29zM5.34 7.43a2.07 2.07 0 1 1 0-4.14 2.07 2.07 0 0 1 0 4.14zM6.96 20.45H3.7V9h3.26v11.45zM22.23 0H1.77C.79 0 0 .77 0 1.72v20.56C0 23.23.79 24 1.77 24h20.46C23.2 24 24 23.23 24 22.28V1.72C24 .77 23.2 0 22.23 0z" />
  </svg>
);

const IconMedium = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
    <path d="M13.54 12a6.8 6.8 0 0 1-6.77 6.82A6.8 6.8 0 0 1 0 12a6.8 6.8 0 0 1 6.77-6.82A6.8 6.8 0 0 1 13.54 12zm7.42 0c0 3.54-1.51 6.42-3.38 6.42-1.87 0-3.39-2.88-3.39-6.42s1.52-6.42 3.39-6.42 3.38 2.88 3.38 6.42M24 12c0 3.17-.53 5.75-1.19 5.75-.66 0-1.19-2.58-1.19-5.75s.53-5.75 1.19-5.75C23.47 6.25 24 8.83 24 12z" />
  </svg>
);

export default function ContactSection() {
  const language = useStore(s => s.language);
  const t = translations[language];
  const [sectionRef, inView] = useInView(0.1);

  return (
    <section id="contact" ref={sectionRef} className={styles.section}>
      <div className={`${styles.inner} ${inView ? styles.visible : ''}`}>

        <span className={styles.ghost} aria-hidden="true">05</span>

        <div className={styles.header}>
          <p className={styles.label}>{t.contactLabel}</p>
          <h2 className={styles.title}>{t.contactTitle}</h2>
        </div>

        <div className={styles.body}>
          <p className={styles.cta}>
            {t.contactCta}
          </p>

          <a
            href={`mailto:${social.email}`}
            className={`${styles.emailLink} cursor-target`}
          >
            {social.email}
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
              stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M7 17 17 7M7 7h10v10" />
            </svg>
          </a>

          <div className={styles.links}>
            <a href={social.github} target="_blank" rel="noopener noreferrer" className={`${styles.link} cursor-target`}>
              <IconGitHub />
              <span>GitHub</span>
            </a>
            <a href={social.linkedin} target="_blank" rel="noopener noreferrer" className={`${styles.link} cursor-target`}>
              <IconLinkedIn />
              <span>LinkedIn</span>
            </a>
            <a href={social.medium} target="_blank" rel="noopener noreferrer" className={`${styles.link} cursor-target`}>
              <IconMedium />
              <span>Medium</span>
            </a>
          </div>

          <div className={styles.footer}>
            <span className={styles.footerName}>
              {about.name} — {about.title}
            </span>
            <span className={styles.footerLoc}>{about.location}</span>
          </div>
        </div>
      </div>
    </section>
  );
}
