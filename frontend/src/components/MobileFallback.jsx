/**
 * MobileFallback.jsx — Mobil uyarı ekranı.
 * window.innerWidth < 768px olduğunda gösterilir.
 */
import styles from '../styles/MobileFallback.module.css';

export default function MobileFallback() {
  return (
    <div className={styles.container} role="alert">
      <div className={styles.icon}>✦</div>
      <h1 className={styles.title}>BUĞRA.AI</h1>
      <p className={styles.subtitle}>Dijital Klon</p>
      <p className={styles.desc}>
        Bu deneyim 3D ses-reaktif görseller içeriyor
        ve masaüstü tarayıcı için tasarlandı.
      </p>
      <p className={styles.cta}>Bilgisayarından ziyaret et</p>

      <div className={styles.links}>
        <a
          href="https://github.com/sbugrayy"
          target="_blank"
          rel="noopener noreferrer"
          className={styles.link}
        >
          GitHub
        </a>
        <a
          href="https://www.linkedin.com/in/bugra-yildirim"
          target="_blank"
          rel="noopener noreferrer"
          className={styles.link}
        >
          LinkedIn
        </a>
      </div>
    </div>
  );
}
