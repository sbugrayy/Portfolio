import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import useStore from '../store/useStore.js';
import { translations } from '../i18n/translations.js';
import styles from './MobileNav.module.css';

const SECTIONS = [
  { id: 'home',           translationKey: 'navHome' },
  { id: 'about',          translationKey: 'navAbout' },
  { id: 'experience',     translationKey: 'navExperience' },
  { id: 'skills',         translationKey: 'navSkills' },
  { id: 'projects',       translationKey: 'navProjects' },
  { id: 'certifications', translationKey: 'navCertifications' },
  { id: 'contact',        translationKey: 'navContact' },
];

const LINE_VARIANTS = {
  top:    { closed: { rotate: 0,   y: 0 },  open: { rotate: 45,  y: 7  } },
  mid:    { closed: { opacity: 1,  scaleX: 1 }, open: { opacity: 0, scaleX: 0 } },
  bottom: { closed: { rotate: 0,   y: 0 },  open: { rotate: -45, y: -7 } },
};

const ITEM_VARIANTS = {
  hidden: { opacity: 0, x: -28 },
  show:   (i) => ({ opacity: 1, x: 0, transition: { delay: 0.05 + i * 0.055, duration: 0.32, ease: 'easeOut' } }),
};

export default function MobileNav() {
  const [open, setOpen]     = useState(false);
  const [active, setActive] = useState('home');
  const [scrolled, setScrolled] = useState(false);
  const language    = useStore(s => s.language);
  const setLanguage = useStore(s => s.setLanguage);
  const t = translations[language];

  /* Scroll glass effect */
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  /* Active section detection */
  useEffect(() => {
    const observers = [];
    SECTIONS.forEach(({ id }) => {
      const el = document.getElementById(id);
      if (!el) return;
      const obs = new IntersectionObserver(
        ([entry]) => { if (entry.isIntersecting) setActive(id); },
        { rootMargin: '-35% 0px -60% 0px' }
      );
      obs.observe(el);
      observers.push(obs);
    });
    return () => observers.forEach(o => o.disconnect());
  }, []);

  /* Body scroll lock when drawer open */
  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [open]);

  const scrollTo = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
    setOpen(false);
  };

  const toggle = () => setOpen(o => !o);
  const state  = open ? 'open' : 'closed';

  return (
    <>
      {/* ── Top bar ─────────────────────────────────────────── */}
      <nav className={`${styles.bar} ${scrolled ? styles.scrolled : ''}`}>

        {/* Hamburger — sol */}
        <button
          className={styles.hamburger}
          onClick={toggle}
          aria-label={open ? 'Menüyü kapat' : 'Menüyü aç'}
          aria-expanded={open}
        >
          <motion.span
            className={styles.line}
            variants={LINE_VARIANTS.top}
            animate={state}
            transition={{ duration: 0.28, ease: 'easeInOut' }}
          />
          <motion.span
            className={styles.line}
            variants={LINE_VARIANTS.mid}
            animate={state}
            transition={{ duration: 0.2, ease: 'easeInOut' }}
          />
          <motion.span
            className={styles.line}
            variants={LINE_VARIANTS.bottom}
            animate={state}
            transition={{ duration: 0.28, ease: 'easeInOut' }}
          />
        </button>

        {/* Dil toggle — sağ */}
        <div className={styles.langRow}>
          {['tr', 'en'].map(lang => (
            <button
              key={lang}
              className={`${styles.langBtn} ${language === lang ? styles.langActive : ''}`}
              onClick={() => setLanguage(lang)}
            >
              {lang.toUpperCase()}
            </button>
          ))}
        </div>
      </nav>

      {/* ── Drawer + Backdrop ───────────────────────────────── */}
      <AnimatePresence>
        {open && (
          <>
            {/* Backdrop */}
            <motion.div
              className={styles.backdrop}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.28 }}
              onClick={() => setOpen(false)}
            />

            {/* Drawer */}
            <motion.aside
              className={styles.drawer}
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', stiffness: 340, damping: 34 }}
            >
              {/* Brand */}
              <div className={styles.drawerBrand}>
                <span className={styles.drawerTitle}>BUĞRA.AI</span>
                <span className={styles.drawerSub}>Dijital Klon</span>
              </div>

              {/* Divider */}
              <div className={styles.divider} />

              {/* Nav items */}
              <nav className={styles.drawerNav}>
                {SECTIONS.map(({ id, translationKey }, i) => {
                  const isActive = active === id;
                  return (
                    <motion.button
                      key={id}
                      className={`${styles.navItem} ${isActive ? styles.navItemActive : ''}`}
                      onClick={() => scrollTo(id)}
                      custom={i}
                      variants={ITEM_VARIANTS}
                      initial="hidden"
                      animate="show"
                    >
                      <span className={styles.navNum}>0{i + 1}</span>
                      <span className={styles.navLabel}>{t[translationKey]}</span>
                      {isActive && (
                        <motion.span
                          className={styles.navDot}
                          layoutId="mobileNavDot"
                          transition={{ type: 'spring', stiffness: 400, damping: 32 }}
                        />
                      )}
                    </motion.button>
                  );
                })}
              </nav>

              {/* Drawer footer */}
              <div className={styles.drawerFooter}>
                <a
                  href="https://github.com/sbugrayy"
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.socialLink}
                >
                  GitHub
                </a>
                <span className={styles.socialSep}>·</span>
                <a
                  href="https://www.linkedin.com/in/bugra-yildirim"
                  target="_blank"
                  rel="noopener noreferrer"
                  className={styles.socialLink}
                >
                  LinkedIn
                </a>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
