import { useMemo, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import AnimatedSection from './AnimatedSection.jsx';
import { projects, pick } from '../data/portfolio.js';
import useStore from '../store/useStore.js';
import { translations } from '../i18n/translations.js';
import styles from './ProjectsSection.module.css';

const IconArrow = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M7 17 17 7M7 7h10v10" />
  </svg>
);

const IconGithub = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 2C6.477 2 2 6.477 2 12c0 4.418 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.009-.868-.013-1.703-2.782.604-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.831.092-.646.35-1.086.636-1.336-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.579.688.481C19.138 20.163 22 16.418 22 12c0-5.523-4.477-10-10-10z"/>
  </svg>
);

const IconDemo = () => (
  <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/>
    <polyline points="15 3 21 3 21 9"/>
    <line x1="10" y1="14" x2="21" y2="3"/>
  </svg>
);

function ProjectCard({ item, index, language }) {
  const t = translations[language];
  const handleCardClick = () => {
    if (item.github) window.open(item.github, '_blank', 'noopener,noreferrer');
  };

  return (
    <motion.div
      className={`${styles.card} ${item.featured ? styles.featured : ''} cursor-target`}
      onClick={handleCardClick}
      style={{ cursor: item.github ? 'pointer' : 'default' }}
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.1 }}
      transition={{ duration: 0.5, delay: index * 0.1, ease: 'easeOut' }}
    >
      {item.award && (
        <div className={styles.ribbon}>{t.projectsRibbonAward}</div>
      )}

      {item.featured && !item.award && (
        <span className={styles.featuredBadge}>Featured</span>
      )}

      <div className={styles.cardTop}>
        <span className={styles.year}>{item.year}</span>
        <span className={styles.arrow}><IconArrow /></span>
      </div>

      <h3 className={styles.name}>{item.name}</h3>
      <p className={styles.short}>{pick(item, 'short', language)}</p>
      <p className={styles.desc}>{pick(item, 'description', language)}</p>

      <div className={styles.stack}>
        {item.stack.map(t => (
          <span key={t} className={styles.stackTag}>{t}</span>
        ))}
      </div>

      {(item.github || item.demo) && (
        <div className={styles.cardActions} onClick={e => e.stopPropagation()}>
          {item.github && (
            <a
              href={item.github}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.btnGithub}
            >
              <IconGithub /> GitHub
            </a>
          )}
          {item.demo && (
            <a
              href={item.demo}
              target="_blank"
              rel="noopener noreferrer"
              className={styles.btnDemo}
            >
              <IconDemo /> Demo
            </a>
          )}
        </div>
      )}
    </motion.div>
  );
}

function filterProjects(list, key) {
  if (key === 'all')      return list;
  if (key === 'featured') return list.filter(p => p.featured);
  if (key === 'ai')       return list.filter(p => p.category === 'ai');
  return list.filter(p => p.category === key);
}

export default function ProjectsSection() {
  const language = useStore(s => s.language);
  const t = translations[language];
  const [active, setActive] = useState('all');
  const filtered = filterProjects(projects, active);

  const filters = useMemo(() => [
    { key: 'all',      label: t.projectsFilterAll },
    { key: 'featured', label: t.projectsFilterFeatured },
    { key: 'ai',       label: 'AI' },
    { key: 'web',      label: 'Web' },
    { key: 'desktop',  label: t.projectsFilterDesktop },
    { key: 'mobile',   label: t.projectsFilterMobile },
    { key: 'game',     label: t.projectsFilterGame },
  ], [t]);

  return (
    <section id="projects" className={styles.section}>
      <AnimatedSection className={styles.inner}>
        <span className={styles.ghost} aria-hidden="true">04</span>

        <div className={styles.header}>
          <p className={styles.label}>{t.projectsLabel}</p>
          <h2 className={styles.title}>{t.projectsTitle}</h2>
        </div>

        <div className={styles.filters}>
          {filters.map(f => (
            <button
              key={f.key}
              className={`${styles.filterBtn} ${active === f.key ? styles.filterActive : ''} cursor-target`}
              onClick={() => setActive(f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>

        <AnimatePresence mode="wait">
          <motion.div
            key={active}
            className={styles.grid}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
          >
            {filtered.map((p, i) => (
              <ProjectCard key={p.name} item={p} index={i} language={language} />
            ))}
          </motion.div>
        </AnimatePresence>
      </AnimatedSection>
    </section>
  );
}
