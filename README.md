---
title: Portfolio API
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
---

# BUĞRA.AI — Digital Clone Portfolio

> "You won't read a portfolio — you'll talk to me."

A futuristic, RAG-powered AI avatar portfolio. Instead of scrolling through a static page, visitors have a real conversation with my digital clone, backed by a knowledge base built from my actual experience.

**Live:** [bugrayildirim.vercel.app](https://bugrayildirim.vercel.app)

---

## Features

| Feature | Description |
|---|---|
| **AI Avatar** | RAG pipeline answers questions as me, in first person |
| **3D Sphere** | Three.js vertex displacement, reacts to audio FFT |
| **Procedural Music** | Tone.js 4-stem ambient soundtrack, state-driven |
| **Source Cards** | Real project cards surfaced from RAG metadata |
| **Typing Effect** | 28ms/char character-by-character animation |
| **Multilingual** | Responds in Turkish or English based on input |
| **Mobile Fallback** | Graceful warning screen below 768px |

---

## Architecture

```
┌─────────────────────────────────────┐
│  Frontend — Vercel                  │
│  React + Vite + Three.js + Tone.js  │
│  bugrayildirim.vercel.app           │
└────────────────┬────────────────────┘
                 │ POST /chat
┌────────────────▼────────────────────┐
│  Backend — Hugging Face Spaces      │
│  FastAPI + LangChain + ChromaDB     │
│  bugrayildirim-portfolio-api.hf.space│
└─────────────────────────────────────┘
```

**RAG Pipeline:**
`knowledge.json` → sentence-transformers embeddings → ChromaDB → MMR retrieval → Groq (llama-3.3-70b) → streamed answer

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, JavaScript, CSS Modules |
| 3D / WebGL | Three.js, @react-three/fiber, @react-three/drei |
| Animation | Framer Motion |
| Audio | Tone.js (procedural 4-stem music) |
| State | Zustand |
| Backend | Python, FastAPI, Uvicorn |
| AI / RAG | LangChain, ChromaDB, Groq API (llama-3.3-70b-versatile) |
| Embeddings | sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2) |
| Deployment | Vercel (frontend), Hugging Face Spaces Docker (backend) |

---

## Local Development

### Prerequisites
- Node.js 18+
- Python 3.11+
- Groq API key → [console.groq.com](https://console.groq.com)

### 1. Clone & configure

```bash
git clone https://github.com/sbugrayy/Portfolio.git
cd Portfolio
```

Create `.env` in the root:
```env
GROQ_API_KEY=your_key_here
```

### 2. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
python build_knowledge_base.py   # builds ChromaDB from knowledge.json
uvicorn main:app --reload        # http://localhost:8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

---

## API

```
GET  /health  →  { "status": "ok", "vectorstore": true }
POST /chat    →  { "answer": string, "sources": [...], "stem_hint": string }
```

**Request body:**
```json
{
  "query": "What projects have you built?",
  "history": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ]
}
```

---

## Knowledge Base

Edit `backend/data/knowledge.json` and rebuild:

```bash
cd backend
python build_knowledge_base.py
```

The script indexes: biography, skills, projects, experience, education, and certifications as separate ChromaDB documents for precise MMR retrieval.

---

## License

MIT
