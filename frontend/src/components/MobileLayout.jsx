import MobileNav            from './MobileNav.jsx';
import ChatInterface        from './ChatInterface.jsx';
import ErrorBoundary        from './ErrorBoundary.jsx';
import AboutSection         from './AboutSection.jsx';
import ExperienceSection    from './ExperienceSection.jsx';
import SkillsSection        from './SkillsSection.jsx';
import ProjectsSection      from './ProjectsSection.jsx';
import CertificationsSection from './CertificationsSection.jsx';
import ContactSection       from './ContactSection.jsx';
import styles from './MobileLayout.module.css';

export default function MobileLayout() {
  return (
    <div className={styles.page}>
      <MobileNav />

      {/* Hero: AI chat, 3D/audio yok */}
      <section id="home" className={styles.hero}>
        <div className={styles.heroBg} aria-hidden="true" />
        <div className={styles.heroTop}>
          <h1 className={styles.heroTitle}>BUĞRA.AI</h1>
          <p className={styles.heroSub}>Dijital Klon</p>
        </div>
        <ErrorBoundary>
          <ChatInterface />
        </ErrorBoundary>
      </section>

      {/* Scroll sections */}
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
    </div>
  );
}
