import { create } from 'zustand';
import { MAX_MESSAGES } from '../config.js';

/**
 * Zustand global store — uygulama genelinde paylaşılan durum.
 *
 * sphereState : 3D kürenin animasyon modu
 * activeStem  : Müzik sisteminin aktif katmanı
 * messages    : Sohbet geçmişi (maks MAX_MESSAGES)
 * sources     : Kaynak kart verileri (RAG metadata)
 * analyserData: FFT frekans verisi (ses reaktiflik için)
 * audioReady  : Ses sistemi başlatıldı mı?
 */
const useStore = create((set) => ({
  // ── State ──────────────────────────────────────────────────
  language: 'tr',           // 'tr' | 'en'
  sphereState: 'idle',      // 'idle' | 'thinking' | 'speaking'
  activeStem: 'pad',        // 'pad' | 'perc' | 'arp' | 'bass'
  messages: [],             // { id, role, text, displayText }[]
  sources: [],              // SourceInfo[]
  analyserData: [],         // number[] (FFT dB değerleri)
  audioReady: false,

  // ── Setter'lar ─────────────────────────────────────────────
  setLanguage: (lang) => set({ language: lang }),
  setSphereState: (state) => set({ sphereState: state }),
  setActiveStem: (stem) => set({ activeStem: stem }),
  setAudioReady: (ready) => set({ audioReady: ready }),
  setAnalyserData: (data) => set({ analyserData: data }),
  setSources: (sources) => set({ sources }),

  /** Yeni mesaj ekler. MAX_MESSAGES aşılınca en eski çifti siler. */
  addMessage: (msg) =>
    set((state) => {
      const next = [...state.messages, msg];
      return {
        messages:
          next.length > MAX_MESSAGES
            ? next.slice(next.length - MAX_MESSAGES)
            : next,
      };
    }),

  /** Typing efekti için belirli bir mesajın displayText'ini günceller. */
  updateMessageDisplay: (msgId, displayText) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === msgId ? { ...m, displayText } : m
      ),
    })),

  clearMessages: () => set({ messages: [] }),
}));

export default useStore;
