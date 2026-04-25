# BUĞRA.AI — Dijital Klon

> "Bir portfolyo okumayacaksın — benimle konuşacaksın."

RAG destekli, ses reaktif, fütüristik bir AI Avatar portfolyosu. Ziyaretçi ekrana girdiğinde bir portfolyo okumak yerine Buğra'nın dijital klonuyla konuşur.

---

## Proje Yapısı

```
Portfolio/
  frontend/    ← React + Vite + Three.js
  backend/     ← FastAPI + LangChain + ChromaDB
  .env         ← API anahtarları (git'e ekleme!)
```

---

## Kurulum

### 1. Ortam Değişkenleri

`.env` dosyasını düzenle:

```env
OPENAI_API_KEY=sk-...
GITHUB_TOKEN=ghp_...  # Opsiyonel
```

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate         # Windows
pip install -r requirements.txt

# Knowledge base oluştur (OPENAI_API_KEY gerekli)
python scripts/build_knowledge_base.py

# Backend'i başlat
uvicorn main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

---

## Özellikler

| Özellik | Açıklama |
|---|---|
| **RAG Pipeline** | knowledge.json + GitHub README + CV PDF → ChromaDB |
| **3D Küre** | Three.js vertex displacement (FFT reaktif) |
| **Ses Sistemi** | Tone.js procedural 4-stem ambient müzik |
| **Kaynak Kartlar** | RAG metadata'sından gerçek proje kartları |
| **Typing Efekt** | 28ms/karakter karakter karakter yazı animasyonu |
| **Stem Katmanları** | pad → perc → arp → bass (konuşma state'ine göre) |
| **Mobil Fallback** | 768px altında uyarı ekranı |

---

## API Endpoints

```
GET  /health   → { "status": "ok" }
POST /chat     → { "answer", "sources", "stem_hint" }
```

---

## Deployment

**Frontend → Vercel:**
```bash
cd frontend
vercel --prod
```

**Backend → Railway:**
1. Railway'de yeni proje oluştur → GitHub repo bağla
2. `backend/` klasörünü root olarak belirt
3. Environment variables: `OPENAI_API_KEY`, `GITHUB_TOKEN`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. `frontend/src/config.js`'te `VITE_API_URL` ortam değişkenini güncelle

---

## Knowledge Base Güncelleme

```bash
cd backend
python scripts/build_knowledge_base.py
```

Script otomatik olarak:
- `data/knowledge.json` okur
- GitHub README'lerini çeker (GITHUB_TOKEN varsa)
- `data/cv.pdf` parse eder (varsa)
- ChromaDB'yi yeniden oluşturur

---

## Teknoloji Yığını

**Frontend:** React 18 · Vite · Three.js · @react-three/fiber · @react-three/drei · Tone.js · Framer Motion · Zustand

**Backend:** FastAPI · LangChain · ChromaDB · OpenAI API · PyMuPDF · PyGithub

**Deployment:** Vercel (frontend) · Railway (backend)
