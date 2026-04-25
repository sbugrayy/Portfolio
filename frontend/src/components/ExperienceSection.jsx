import { motion } from 'framer-motion';
import AnimatedSection from './AnimatedSection.jsx';
import { experience, pick } from '../data/portfolio.js';
import useStore from '../store/useStore.js';
import { translations } from '../i18n/translations.js';
import styles from './ExperienceSection.module.css';

function Entry({ item, index, language }) {
  const t = translations[language];
  return (
    <motion.div
      className={styles.entry}
      initial={{ opacity: 0, x: -20 }}
      whileInView={{ opacity: 1, x: 0 }}
      viewport={{ once: true, amount: 0.2 }}
      transition={{ duration: 0.55, delay: index * 0.08, ease: "easeOut" }}
    >
      {/* Left: meta */}
      <div className={styles.meta}>
        <span className={styles.date}>{pick(item, 'date', language)}</span>
        {item.current && <span className={styles.badge}>{t.experienceBadgeActive}</span>}
      </div>

      {/* Right: content */}
      <div className={styles.content}>
        <div className={styles.connector}>
          <span className={styles.dot} />
          <span className={styles.line} />
        </div>
        <div className={styles.body}>
          <h3 className={styles.company}>{pick(item, 'company', language)}</h3>
          <p className={styles.role}>{pick(item, 'role', language)}</p>
          {item.bullets && item.bullets.length > 0 ? (
            <ul className={styles.bullets}>
              {(item[language === 'en' ? 'bullets_en' : 'bullets'] ?? item.bullets).map((b, i) => (
                <li key={i} className={styles.bullet}>{b}</li>
              ))}
            </ul>
          ) : (
            <p className={styles.desc}>{item.description}</p>
          )}
          <div className={styles.tags}>
            {(item[language === 'en' && item.tags_en ? 'tags_en' : 'tags'] ?? item.tags).map(t => (
              <span key={t} className={styles.tag}>{t}</span>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default function ExperienceSection() {
  const language = useStore(s => s.language);
  const t = translations[language];

  return (
    <section id="experience" className={styles.section}>
      <AnimatedSection className={styles.inner}>

        <span className={styles.ghost} aria-hidden="true">02</span>

        <div className={styles.header}>
          <p className={styles.label}>{t.experienceLabel}</p>
          <h2 className={styles.title}>{t.experienceTitle}</h2>
        </div>

        <div className={styles.feed}>
          {experience.map((item, i) => (
            <Entry key={i} item={item} index={i} language={language} />
          ))}
        </div>
      </AnimatedSection>
    </section>
  );
}
