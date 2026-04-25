import { useEffect, useState, useRef } from 'react';
import { useInView, useSpring } from 'framer-motion';
import AnimatedSection from './AnimatedSection.jsx';
import { about, pick } from '../data/portfolio.js';
import useStore from '../store/useStore.js';
import { translations } from '../i18n/translations.js';
import styles from './AboutSection.module.css';

function Counter({ target, suffix }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, amount: 0.5 });
  const [display, setDisplay] = useState(0);

  const springValue = useSpring(0, {
    stiffness: 50,
    damping: 20,
    restDelta: 0.5,
  });

  useEffect(() => {
    if (inView) {
      springValue.set(target);
    }
  }, [inView, springValue, target]);

  useEffect(() => {
    return springValue.on("change", (latest) => {
      setDisplay(Math.floor(latest));
    });
  }, [springValue]);

  return <span ref={ref}>{display}{suffix}</span>;
}

export default function AboutSection() {
  const language = useStore(s => s.language);
  const t = translations[language];

  return (
    <section id="about" className={styles.section}>
      <AnimatedSection className={styles.inner}>

        {/* Ghost number */}
        <span className={styles.ghost} aria-hidden="true">01</span>

        {/* Header */}
        <div className={styles.header}>
          <p className={styles.label}>{t.aboutLabel}</p>
          <h2 className={styles.title}>{t.aboutTitle}</h2>
        </div>

        {/* Body grid */}
        <div className={styles.grid}>

          {/* Bio column */}
          <div className={styles.bioCol}>
            <div className={styles.profileImageWrapper}>
              <img src="/images/profilFoto.webp" alt="Buğra Yıldırım" className={styles.profileImage} />
            </div>
            <p className={styles.bio}>{pick(about, 'longBio', language)}</p>

            {/* Tech stack */}
            <div className={styles.stackWrap}>
              {about.techStack.map(t => (
                <span key={t} className={styles.chip}>{t}</span>
              ))}
            </div>
          </div>

          {/* Right column */}
          <div className={styles.rightCol}>

            {/* Stat counters */}
            <div className={styles.stats}>
              {about.highlights.map(h => (
                <div key={h.label} className={styles.stat}>
                  <span className={styles.statNum}>
                    <Counter target={h.value} suffix={h.suffix} />
                  </span>
                  <span className={styles.statLabel}>{pick(h, 'label', language)}</span>
                </div>
              ))}
            </div>

            {/* Education */}
            <div className={styles.edu}>
              {about.education.map(e => (
                <div key={e.school} className={styles.eduItem}>
                  <span className={styles.eduDate}>{pick(e, 'date', language)}</span>
                  <span className={styles.eduSchool}>{e.school}</span>
                  <span className={styles.eduDegree}>{pick(e, 'degree', language)}</span>
                </div>
              ))}
            </div>

            {/* Location */}
            <p className={styles.location}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"/>
                <circle cx="12" cy="9" r="2.5"/>
              </svg>
              {about.location}
            </p>
          </div>
        </div>
      </AnimatedSection>
    </section>
  );
}
