/**
 * ChatInterface.jsx — Sohbet arayüzü.
 *
 * Davranışlar:
 *   • Enter → gönder, Shift+Enter → satır atla
 *   • Typing efekti cevap gelince çalışır
 *   • Mesaj geçmişi: maks 10, eskiler opacity 0.4
 *   • Loading: 3 nokta animasyonu
 */
import { useRef, useState, useEffect } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import useStore from '../store/useStore.js';
import { sendMessage } from '../systems/ChatEngine.js';
import { translations } from '../i18n/translations.js';
import { API_URL, TYPING_SPEED_MS, IDLE_TIMEOUT_MS, MAX_HISTORY_TURNS, TEXTAREA_MAX_HEIGHT_PX } from '../config.js';
import styles from '../styles/ChatInterface.module.css';

export default function ChatInterface() {
  const [input, setInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const messages = useStore((s) => s.messages);
  const sphereState = useStore((s) => s.sphereState);
  const language = useStore((s) => s.language);
  const t = translations[language];
  const historyRef = useRef(null);
  const textareaRef = useRef(null);

  // Yeni mesajda otomatik scroll
  useEffect(() => {
    if (historyRef.current) {
      historyRef.current.scrollTop = historyRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSend = async () => {
    const query = input.trim();
    if (!query || isSending || sphereState === 'thinking') return;
    setInput('');
    setIsSending(true);
    try {
      await sendMessage(query);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Textarea'yı içeriğe göre büyüt (maks 120px)
  const handleInput = (e) => {
    setInput(e.target.value);
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = 'auto';
      ta.style.height = `${Math.min(ta.scrollHeight, TEXTAREA_MAX_HEIGHT_PX)}px`;
    }
  };

  const isActive = isSending || sphereState !== 'idle';

  return (
    <div className={styles.container}>
      {/* Mesaj geçmişi */}
      <div className={styles.history} ref={historyRef}>
        <AnimatePresence initial={false}>
          {messages.map((msg, idx) => {
            const isRecent = idx >= messages.length - 2;
            return (
              <motion.div
                key={msg.id}
                className={`${styles.message} ${styles[msg.role]}`}
                style={{ opacity: isRecent ? 1 : 0.38 }}
                initial={{ opacity: 0, y: 12, scale: 0.97 }}
                animate={{ opacity: isRecent ? 1 : 0.38, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.3 }}
              >
                <span className={styles.roleLabel}>
                  {msg.role === 'user' ? t.chatRoleUser : t.chatRoleBot}
                </span>
                <p className={styles.text}>{msg.displayText}</p>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>

      {/* Input alanı */}
      <div className={styles.inputWrapper}>
        <div className={`${styles.inputBox} ${isActive ? styles.active : ''}`}>
          <textarea
            id="chat-input"
            ref={textareaRef}
            className={`${styles.textarea} cursor-target`}
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder={
              sphereState === 'thinking'
                ? t.chatThinking
                : sphereState === 'speaking'
                ? t.chatSpeaking
                : t.chatPlaceholder
            }
            disabled={isActive}
            rows={1}
            autoComplete="off"
            spellCheck="false"
          />
          {isSending && (
            <div className={styles.dots} aria-label="Yükleniyor">
              <span /><span /><span />
            </div>
          )}
        </div>
        <p className={styles.shortcut}>{t.chatShortcut}</p>
      </div>
    </div>
  );
}
