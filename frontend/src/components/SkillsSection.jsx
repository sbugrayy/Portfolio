import { useMemo } from 'react';
import AnimatedSection from './AnimatedSection.jsx';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Tooltip } from 'recharts';
import { skills, pick } from '../data/portfolio.js';
import useStore from '../store/useStore.js';
import { translations } from '../i18n/translations.js';
import styles from './SkillsSection.module.css';

const CustomTooltip = ({ active, payload }) => {
  const language = useStore(s => s.language);
  const t = translations[language];

  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className={styles.tooltip}>
        <p className={styles.tooltipTitle}>{data.subject}</p>
        <p className={styles.tooltipValue}>{t.skillsTooltipLevel}: {data.value}%</p>
      </div>
    );
  }
  return null;
};

export default function SkillsSection() {
  const language = useStore(s => s.language);
  const t = translations[language];

  const radarData = useMemo(() => {
    return skills.map(cat => {
      const sum = cat.items.reduce((acc, curr) => acc + curr.level, 0);
      const avg = sum / cat.items.length;
      return {
        subject: pick(cat, 'category', language),
        value: Math.round(avg * 20), // Scale 1-5 to 20-100
        fullMark: 100,
      };
    });
  }, [language]);

  return (
    <section id="skills" className={styles.section}>
      <AnimatedSection className={styles.inner}>
        <span className={styles.ghost} aria-hidden="true">03</span>

        <div className={styles.header}>
          <p className={styles.label}>{t.skillsLabel}</p>
          <h2 className={styles.title}>{t.skillsTitle}</h2>
        </div>

        <div className={styles.chartContainer}>
          <div className={styles.chartGlow} />
          <ResponsiveContainer width="100%" height={500}>
            <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
              <PolarGrid stroke="rgba(6, 182, 212, 0.2)" />
              <PolarAngleAxis
                dataKey="subject"
                tick={{ fill: '#e2e8f0', fontSize: 13, fontFamily: 'JetBrains Mono' }}
              />
              <PolarRadiusAxis
                angle={30}
                domain={[0, 100]}
                tick={false}
                axisLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Radar
                name={t.skillsTitle}
                dataKey="value"
                stroke="#06b6d4"
                strokeWidth={2}
                fill="#06b6d4"
                fillOpacity={0.15}
                dot={{ r: 4, fill: '#050510', stroke: '#06b6d4', strokeWidth: 2 }}
                activeDot={{ r: 6, fill: '#06b6d4', stroke: '#fff', strokeWidth: 1 }}
              />
            </RadarChart>
          </ResponsiveContainer>
        </div>

      </AnimatedSection>
    </section>
  );
}
