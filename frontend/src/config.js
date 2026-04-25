// ──────────────────────────────────────────────────────────────
// config.js — Frontend sabitleri (tüm magic number'lar burada)
// ──────────────────────────────────────────────────────────────

// Backend API URL'i (geliştirmede localhost, prod'da Railway/Render)
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Typing efekti hızı (ms cinsinden, karakter başına)
export const TYPING_SPEED_MS = 28;

// Typing bittikten sonra idle'a dönüş bekleme süresi (ms)
export const IDLE_TIMEOUT_MS = 8000;

// Stem gain geçiş süresi (saniye) — Tone.js rampTo için
export const STEM_RAMP_TIME = 1.5;

// Kaynak kartlarının ekranda kalma süresi (ms)
export const SOURCE_CARDS_TIMEOUT_MS = 12000;

// Parçacık bulutu nokta sayısı
export const PARTICLE_COUNT = 800;

// AnalyserNode FFT boyutu (güç 2'nin katı olmalı)
export const ANALYSER_FFT_SIZE = 128;

// Küre yarıçapı (Three.js birim)
export const SPHERE_RADIUS = 2;

// Küre geometri segment sayısı (yüksek = daha detaylı displacement)
export const SPHERE_SEGMENTS = 128;

// Procedural müzik temposu (BPM)
export const AUDIO_BPM = 88;

// Mobil breakpoint (px — bu değerin altında MobileFallback gösterilir)
export const MOBILE_BREAKPOINT_PX = 768;

// Mesaj geçmişi maksimum uzunluğu (soru + cevap çifti)
export const MAX_MESSAGES = 10;

// Backend'e gönderilecek sohbet geçmişi tur sayısı (1 tur = 1 kullanıcı + 1 asistan)
export const MAX_HISTORY_TURNS = 3;

// ChatInterface textarea maksimum yüksekliği (px)
export const TEXTAREA_MAX_HEIGHT_PX = 120;
