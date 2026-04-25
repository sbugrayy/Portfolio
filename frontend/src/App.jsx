import { useEffect, useState } from 'react';
import { AnimatePresence, motion, useMotionValue, useTransform } from 'framer-motion';
import EntryScreen      from './components/EntryScreen.jsx';
import ChatInterface    from './components/ChatInterface.jsx';
import SourceCards      from './components/SourceCards.jsx';
import MobileLayout     from './components/MobileLayout.jsx';
import FloatingNav      from './components/FloatingNav.jsx';
import TargetCursor     from './components/TargetCursor.jsx';
import EvilEye          from './components/EvilEye.jsx';
import AboutSection     from './components/AboutSection.jsx';
import ExperienceSection from './components/ExperienceSection.jsx';
import SkillsSection    from './components/SkillsSection.jsx';
import ProjectsSection        from './components/ProjectsSection.jsx';
import CertificationsSection  from './components/CertificationsSection.jsx';
import ContactSection         from './components/ContactSection.jsx';
import LangToggle             from './components/LangToggle.jsx';
import ErrorBoundary          from './components/ErrorBoundary.jsx';
import { cleanup as cleanupAudio } from './systems/AudioEngine.js';
import useStore         from './store/useStore.js';
import { MOBILE_BREAKPOINT_PX } from './config.js';
import styles from './App.module.css';

export default function App() {
  const [isMobile, setIsMobile] = useState(
    () => window.innerWidth < MOBILE_BREAKPOINT_PX
  );
  const audioReady = useStore(s => s.audioReady);

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < MOBILE_BREAKPOINT_PX);
    window.addEventListener('resize', check);
    return () => {
      window.removeEventListener('resize', check);
      cleanupAudio();
    };
  }, []);

  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  const handleMouseMove = (e) => {
    if (isMobile) return;
    const x = (e.clientX / window.innerWidth) * 2 - 1;
    const y = (e.clientY / window.innerHeight) * 2 - 1;
    mouseX.set(x);
    mouseY.set(y);
  };

  const xEye = useTransform(mouseX, [-1, 1], [-25, 25]);
  const yEye = useTransform(mouseY, [-1, 1], [-25, 25]);
  const xUI = useTransform(mouseX, [-1, 1], [15, -15]);
  const yUI = useTransform(mouseY, [-1, 1], [15, -15]);

  if (isMobile) return <MobileLayout />;

  return (
    <div className={styles.page}>
      <TargetCursor targetSelector=".cursor-target" />

      <AnimatePresence mode="wait">
        {!audioReady ? (
          <EntryScreen key="entry" />
        ) : (
          <motion.div
            key="main"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.9, ease: 'easeOut' }}
          >
            <FloatingNav />
            <LangToggle />

            {/* ── Hero: AI avatar (Ana Sayfa) ─────────────────── */}
            <section id="home" className={styles.hero} onMouseMove={handleMouseMove}>
              <motion.div 
                style={{ x: xEye, y: yEye, position: 'absolute', top: 0, left: 0, right: 0, bottom: 0 }}
              >
                <EvilEye
                  eyeColor="#a7dafcff"
                  intensity={0.6}
                  pupilSize={0.6}
                  irisWidth={0.25}
                  glowIntensity={0.35}
                  scale={0.6}
                  noiseScale={1.0}
                  pupilFollow={1.0}
                  flameSpeed={0.4}
                  backgroundColor="#050510"
                />
              </motion.div>
              
              <motion.div 
                style={{ x: xUI, y: yUI, position: 'relative', zIndex: 10, width: '100%', height: '100%' }}
              >
                <ErrorBoundary>
                  <ChatInterface />
                </ErrorBoundary>
                <SourceCards />
              </motion.div>
            </section>

            {/* ── Scroll sections ──────────────────────────────── */}
            <div className={styles.sections}>
              <ErrorBoundary>
                <AboutSection />
                <ExperienceSection />
                <SkillsSection />
                <ProjectsSection />
                <CertificationsSection />
                <ContactSection />
              </ErrorBoundary>
            </div>

            <footer className={styles.footer}>
              © 2026 Buğra Yıldırım. Tüm hakları saklıdır.
            </footer>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
