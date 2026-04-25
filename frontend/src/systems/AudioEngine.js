/**
 * AudioEngine.js — Tone.js tabanlı procedural stem ses sistemi
 *
 * 4 katman (stem):
 *   pad  → ambient chord pad  (her zaman çalar, başlangıç)
 *   perc → ritim (kick + hat) (soru gönderilince)
 *   arp  → arpeji             (cevap gelince)
 *   bass → bas melodisi       (proje cevabı gelince)
 *
 * MP3 dosyası gerekmez — tamamen procedural sentez.
 * Gerçek stem MP3'leri eklenince bu dosya güncellenecek.
 */

import * as Tone from 'tone';
import {
  AUDIO_BPM,
  STEM_RAMP_TIME,
  IDLE_TIMEOUT_MS,
  ANALYSER_FFT_SIZE,
} from '../config.js';

// ── Internal state ───────────────────────────────────────────────────
let isInitialized = false;
let idleTimer = null;
let analyserReadInterval = null;
let storeRef = null;

// ── Audio nodes ──────────────────────────────────────────────────────
let masterBus = null;
let toneAnalyser = null;

// ── Gain nodes (her stem için ayrı) ─────────────────────────────────
const gains = { pad: null, perc: null, arp: null, bass: null };

// ── Synthlar ─────────────────────────────────────────────────────────
let padSynth = null;
let percKick = null;
let percHat = null;
let arpSynth = null;
let bassSynth = null;

// ── Transport döngüleri ──────────────────────────────────────────────
let padLoop = null;
let percSeq = null;
let arpSeq = null;
let bassSeq = null;

// Chord progression (ambient Cmaj7 → Fmaj7 → Am7 → G7)
const CHORD_LIST = [
  ['C3', 'E3', 'G3', 'B3'],
  ['F3', 'A3', 'C4', 'E4'],
  ['A2', 'C3', 'E3', 'G3'],
  ['G2', 'B2', 'D3', 'F3'],
];
let chordIdx = 0;

// ── Graf oluşturma ───────────────────────────────────────────────────
function buildGraph() {
  // Sinyal zinciri: her stem gain → masterBus → analyser → destination
  masterBus = new Tone.Gain(1);
  toneAnalyser = new Tone.Analyser('fft', ANALYSER_FFT_SIZE);
  masterBus.connect(toneAnalyser);
  toneAnalyser.toDestination();

  // PAD — uzun süreli ambient chord pad
  padSynth = new Tone.PolySynth(Tone.Synth, {
    oscillator: { type: 'sine' },
    envelope: { attack: 2.5, decay: 0.5, sustain: 0.9, release: 8 },
    volume: -14,
  });
  gains.pad = new Tone.Gain(0.8);
  padSynth.connect(gains.pad);
  gains.pad.connect(masterBus);

  // PERC — kick (MembraneSynth) + hi-hat (MetalSynth)
  percKick = new Tone.MembraneSynth({
    pitchDecay: 0.05,
    octaves: 5,
    envelope: { attack: 0.001, decay: 0.35, sustain: 0, release: 0.5 },
    volume: -6,
  });
  percHat = new Tone.MetalSynth({
    frequency: 400,
    envelope: { attack: 0.001, decay: 0.08, release: 0.08 },
    harmonicity: 5.1,
    modulationIndex: 32,
    resonance: 4000,
    octaves: 1.5,
    volume: -20,
  });
  gains.perc = new Tone.Gain(0);
  percKick.connect(gains.perc);
  percHat.connect(gains.perc);
  gains.perc.connect(masterBus);

  // ARP — üçgen dalga arpeji
  arpSynth = new Tone.Synth({
    oscillator: { type: 'triangle' },
    envelope: { attack: 0.02, decay: 0.12, sustain: 0.4, release: 1.2 },
    volume: -20,
  });
  gains.arp = new Tone.Gain(0);
  arpSynth.connect(gains.arp);
  gains.arp.connect(masterBus);

  // BASS — sawtooth mono synth
  bassSynth = new Tone.MonoSynth({
    oscillator: { type: 'sawtooth' },
    filter: { Q: 3, type: 'lowpass', rolloff: -24 },
    envelope: { attack: 0.04, decay: 0.15, sustain: 0.6, release: 1.5 },
    filterEnvelope: {
      attack: 0.04, decay: 0.15, sustain: 0.5, release: 2,
      baseFrequency: 150, octaves: 3,
    },
    volume: -16,
  });
  gains.bass = new Tone.Gain(0);
  bassSynth.connect(gains.bass);
  gains.bass.connect(masterBus);
}

function buildSequences() {
  // PAD: her 4 ölçüde chord değişimi
  padLoop = new Tone.Loop((time) => {
    padSynth.releaseAll(time);
    padSynth.triggerAttack(CHORD_LIST[chordIdx], time + 0.1);
    chordIdx = (chordIdx + 1) % CHORD_LIST.length;
  }, '4m');
  padLoop.start(0);

  // PERC: 8 adımlı ritim (kick 0,4 / hat tek adımlar)
  percSeq = new Tone.Sequence(
    (time, step) => {
      if (step === 0 || step === 4) percKick.triggerAttackRelease('C1', '8n', time);
      if (step % 2 === 1) percHat.triggerAttackRelease('32n', time);
    },
    [0, 1, 2, 3, 4, 5, 6, 7],
    '8n',
  );
  percSeq.start(0);

  // ARP: 8 nota döngüsü
  const arpNotes = ['C5', 'E5', 'G5', 'B5', 'G5', 'E5', 'D5', 'B4'];
  arpSeq = new Tone.Sequence(
    (time, note) => { arpSynth.triggerAttackRelease(note, '16n', time); },
    arpNotes,
    '16n',
  );
  arpSeq.start(0);

  // BASS: kök notalar
  const bassNotes = ['C2', null, 'C2', null, 'F1', null, 'A1', 'G1'];
  bassSeq = new Tone.Sequence(
    (time, note) => { if (note) bassSynth.triggerAttackRelease(note, '4n', time); },
    bassNotes,
    '4n',
  );
  bassSeq.start(0);
}

// ── Public API ───────────────────────────────────────────────────────

/**
 * Sesi başlatır. Yalnızca kullanıcı tıklaması sonrası çağrılmalı
 * (tarayıcı autoplay politikası).
 * @param {object} store - Zustand useStore referansı
 */
export async function initAudio(store) {
  if (isInitialized) return;
  storeRef = store;

  await Tone.start();
  await Tone.getContext().resume();

  Tone.Transport.bpm.value = AUDIO_BPM;
  buildGraph();
  buildSequences();

  // Tüm gain'leri sıfırla, ardından pad'i aç
  Object.values(gains).forEach((g) => { if (g) g.gain.value = 0; });
  Tone.Transport.start('+0.1');
  gains.pad.gain.rampTo(0.8, STEM_RAMP_TIME);

  // Analyser verisini periyodik olarak Zustand'a yaz (50ms)
  analyserReadInterval = setInterval(() => {
    if (toneAnalyser && storeRef) {
      const raw = toneAnalyser.getValue();
      storeRef.getState().setAnalyserData(Array.from(raw));
    }
  }, 50);

  isInitialized = true;
  if (storeRef) storeRef.getState().setAudioReady(true);
}

/**
 * Backend'den gelen stem_hint değerine göre katmanları ayarlar.
 * @param {'bass'|'arp'|'pad'} hint
 */
export function setStemHint(hint) {
  if (!isInitialized) return;
  clearIdleTimer();

  if (hint === 'bass') {
    rampGain('pad', 0.45);
    rampGain('perc', 0.4);
    rampGain('arp', 0.6);
    rampGain('bass', 0.7);
  } else if (hint === 'arp') {
    rampGain('pad', 0.55);
    rampGain('perc', 0.3);
    rampGain('arp', 0.8);
    rampGain('bass', 0);
  } else {
    resetToIdle();
  }
}

/**
 * Thinking modu: perc + arp hafifçe açılır, pad kısılır.
 */
export function setThinkingMode() {
  if (!isInitialized) return;
  rampGain('pad', 0.45);
  rampGain('perc', 0.4);
  rampGain('arp', 0.25);
}

/**
 * Tüm stem'leri pad'e döndürür (idle state).
 */
export function resetToIdle() {
  if (!isInitialized) return;
  rampGain('pad', 0.8);
  rampGain('perc', 0);
  rampGain('arp', 0);
  rampGain('bass', 0);
}

/**
 * IDLE_TIMEOUT_MS ms sonra otomatik idle'a döner.
 */
export function scheduleIdleReset() {
  clearIdleTimer();
  idleTimer = setTimeout(() => {
    resetToIdle();
    if (storeRef) storeRef.getState().setSphereState('idle');
  }, IDLE_TIMEOUT_MS);
}

export function cleanup() {
  if (!isInitialized) return;
  try {
    clearIdleTimer();
    if (analyserReadInterval) clearInterval(analyserReadInterval);
    Tone.Transport.stop();
    Tone.Transport.cancel();
    [padSynth, percKick, percHat, arpSynth, bassSynth].forEach((s) => s?.dispose());
    [padLoop, percSeq, arpSeq, bassSeq].forEach((s) => s?.dispose());
    Object.values(gains).forEach((g) => g?.dispose());
    masterBus?.dispose();
    toneAnalyser?.dispose();
    isInitialized = false;
  } catch (e) {
    console.error('AudioEngine cleanup error:', e);
  }
}

// ── Yardımcı ────────────────────────────────────────────────────────
function rampGain(name, target) {
  if (gains[name]) gains[name].gain.rampTo(target, STEM_RAMP_TIME);
}

function clearIdleTimer() {
  if (idleTimer) { clearTimeout(idleTimer); idleTimer = null; }
}
