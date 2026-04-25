/**
 * ChatEngine.js — /chat API iletişimi, typing efekti, state yönetimi
 *
 * sendMessage(query) fonksiyonu sırasıyla:
 *  1. Kullanıcı mesajını store'a ekler
 *  2. sphereState → 'thinking', perc+arp açılır
 *  3. POST /chat isteği atılır
 *  4. stem_hint'e göre ses katmanları güncellenir
 *  5. Typing efektiyle cevap yazılır (sphereState → 'speaking')
 *  6. 8 saniye sonra idle'a döner
 */

import useStore from '../store/useStore.js';
import { API_URL, TYPING_SPEED_MS, IDLE_TIMEOUT_MS, MAX_HISTORY_TURNS } from '../config.js';
import { translations } from '../i18n/translations.js';

let msgCounter = 0;
const newId = () => `msg-${++msgCounter}-${Date.now()}`;

/**
 * Kullanıcının sorgusunu gönderir ve tüm state geçişlerini yönetir.
 * @param {string} query
 */
export async function sendMessage(query) {
  const store = useStore.getState();

  // 1. Geçmiş mesajları topla (kullanıcı mesajı eklenmeden önce)
  const history = useStore.getState().messages
    .slice(-(MAX_HISTORY_TURNS * 2))
    .map((m) => ({ role: m.role, content: m.text }));

  // 2. Kullanıcı mesajı
  store.addMessage({ id: newId(), role: 'user', text: query, displayText: query });

  // 3. Thinking state
  store.setSphereState('thinking');

  const startTime = Date.now();
  const MIN_THINKING_TIME = 2500; // 2.5 saniye zorunlu bekletme (sinematik animasyon için)

  try {
    // 4. Backend isteği
    const res = await fetch(`${API_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, history }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    const data = await res.json();
    const { answer, sources } = data;

    // Animasyonun tamamlanması için minimum süreyi bekle
    const elapsed = Date.now() - startTime;
    if (elapsed < MIN_THINKING_TIME) {
      await new Promise(r => setTimeout(r, MIN_THINKING_TIME - elapsed));
    }

    // Kaynak kartlarını güncelle
    store.setSources(sources ?? []);

    // 5. Speaking state + typing efekti
    store.setSphereState('speaking');
    await typeMessage(answer);

    // 6. Idle'a dön
    setTimeout(() => store.setSphereState('idle'), IDLE_TIMEOUT_MS);
  } catch (err) {
    console.error('Chat isteği başarısız:', err);
    const lang = store.language;
    const fallback = translations[lang]?.chatError || "Üzgünüm, şu an bir sorun oluştu. Lütfen tekrar dene.";
    store.addMessage({ id: newId(), role: 'assistant', text: fallback, displayText: fallback });
    
    // Hata gelse bile animasyonun tamamlanması için minimum süreyi bekle
    const elapsed = Date.now() - startTime;
    if (elapsed < MIN_THINKING_TIME) {
      await new Promise(r => setTimeout(r, MIN_THINKING_TIME - elapsed));
    }

    store.setSphereState('idle');
  }
}

/**
 * Cevap metnini karakter karakter DOM'a yazar (typing efekti).
 * @param {string} fullText
 */
function typeMessage(fullText) {
  const store = useStore.getState();
  const msgId = newId();

  store.addMessage({ id: msgId, role: 'assistant', text: fullText, displayText: '' });

  return new Promise((resolve) => {
    let i = 0;
    const interval = setInterval(() => {
      i++;
      useStore.getState().updateMessageDisplay(msgId, fullText.slice(0, i));
      if (i >= fullText.length) {
        clearInterval(interval);
        resolve();
      }
    }, TYPING_SPEED_MS);
  });
}
