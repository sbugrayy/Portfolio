import useStore from '../store/useStore.js';
import styles from '../styles/LangToggle.module.css';

export default function LangToggle() {
  const language = useStore((s) => s.language);
  const setLanguage = useStore((s) => s.setLanguage);

  return (
    <div className={styles.toggleContainer}>
      <button 
        className={`${styles.langBtn} ${language === 'tr' ? styles.active : ''} cursor-target`}
        onClick={() => setLanguage('tr')}
        aria-label="Türkçe"
      >
        TR
      </button>
      <button 
        className={`${styles.langBtn} ${language === 'en' ? styles.active : ''} cursor-target`}
        onClick={() => setLanguage('en')}
        aria-label="English"
      >
        EN
      </button>
    </div>
  );
}
