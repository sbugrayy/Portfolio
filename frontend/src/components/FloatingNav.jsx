import { useEffect, useRef, useState } from 'react';
import useStore from '../store/useStore.js';
import { translations } from '../i18n/translations.js';
import styles from './FloatingNav.module.css';

const SECTIONS = [
  { id: 'home',             translationKey: 'navHome' },
  { id: 'about',            translationKey: 'navAbout' },
  { id: 'experience',       translationKey: 'navExperience' },
  { id: 'skills',           translationKey: 'navSkills' },
  { id: 'projects',         translationKey: 'navProjects' },
  { id: 'certifications',   translationKey: 'navCertifications' },
  { id: 'contact',          translationKey: 'navContact' },
];

export default function FloatingNav() {
  const [active, setActive]     = useState('home');
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen]         = useState(false);
  const language = useStore((s) => s.language);
  const t = translations[language];
  const itemRefs   = useRef([]);
  const trackRef   = useRef(null);
  const listRef    = useRef(null);

  /* ── Scroll glass effect ─────────────────────────────────── */
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  /* ── Active section detection ────────────────────────────── */
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

  /* ── Sliding indicator ───────────────────────────────────── */
  useEffect(() => {
    const idx   = SECTIONS.findIndex(s => s.id === active);
    const item  = itemRefs.current[idx];
    const track = trackRef.current;
    const list  = listRef.current;
    if (!item || !track || !list) return;
    const listRect = list.getBoundingClientRect();
    const itemRect = item.getBoundingClientRect();
    track.style.left  = `${itemRect.left - listRect.left}px`;
    track.style.width = `${itemRect.width}px`;
  }, [active]);

  const scrollTo = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
    setOpen(false);
  };

  return (
    <nav className={`${styles.nav} ${scrolled ? styles.scrolled : ''}`}>

      {/* Monogram */}
      <button className={`${styles.logo} cursor-target`} onClick={() => scrollTo('home')}>
        Buğra Yıldırım
      </button>

      {/* Desktop nav items */}
      <div className={styles.center}>
        <ul ref={listRef} className={styles.list}>
          {SECTIONS.map(({ id, translationKey }, i) => (
            <li key={id}>
              <button
                ref={el => { itemRefs.current[i] = el; }}
                className={`${styles.item} ${active === id ? styles.active : ''} cursor-target`}
                onClick={() => scrollTo(id)}
              >
                {t[translationKey]}
              </button>
            </li>
          ))}
        </ul>
        <span ref={trackRef} className={styles.track} />
      </div>

      {/* Hamburger (mobile) */}
      <button
        className={`${styles.hamburger} ${open ? styles.hamburgerOpen : ''}`}
        onClick={() => setOpen(o => !o)}
        aria-label="Menü"
      >
        <span /><span />
      </button>

      {/* Mobile overlay */}
      {open && (
        <div className={styles.mobileMenu}>
          {SECTIONS.map(({ id, translationKey }) => (
            <button
              key={id}
              className={`${styles.mobileItem} ${active === id ? styles.mobileActive : ''}`}
              onClick={() => scrollTo(id)}
            >
              {t[translationKey]}
            </button>
          ))}
        </div>
      )}
    </nav>
  );
}
