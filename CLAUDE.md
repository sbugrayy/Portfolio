# Portfolyo Projesi — Claude Referans Belgesi

Buğra'nın kişisel portfolyo sitesi. React/Vite frontend + FastAPI backend kombinasyonu. Backend'de RAG tabanlı bir AI avatar (dijital klon) çalışır; kullanıcılar Buğra'nın klonuyla sohbet edebilir.

---

## Klasör Yapısı

```
portfolyo/
├── frontend/
│   └── src/
│       ├── assets/          # Görseller, fontlar, statik dosyalar
│       ├── components/      # React bileşenleri (PascalCase.jsx)
│       ├── store/           # Zustand state yönetimi
│       ├── styles/          # Global CSS ve CSS Modules (.module.css)
│       └── systems/         # WebGL / Three.js sistemleri (Hyperspeed, EvilEye vb.)
└── backend/
    ├── data/
    │   ├── knowledge.json   # RAG knowledge base kaynağı
    │   └── cv.pdf           # Embedding kaynağı
    ├── main.py              # FastAPI giriş noktası, /chat endpoint burada
    ├── config.py            # Ortam değişkenleri ve RAG ayarları
    └── build_knowledge_base.py  # ChromaDB vektör DB oluşturma scripti
```

---

## Tech Stack

| Katman | Teknoloji |
|---|---|
| Frontend | React, Vite, JavaScript, CSS Modules |
| 3D / WebGL | Three.js (systems/ altında kapsüllü) |
| State | Zustand |
| Backend | Python, FastAPI, Uvicorn |
| AI / RAG | LangChain, ChromaDB, Groq API (llama-3.3-70b-versatile) |
| Embedding | sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2) |

---

## knowledge.json Şeması

`backend/data/knowledge.json` — RAG sisteminin birincil kaynağı.

```json
{
  "about": "string — kısa biyografi",
  "skills": {
    "<kategori>": ["string", "..."]
  },
  "projects": [
    {
      "name": "string",
      "short_description": "string",
      "long_description": "string",
      "stack": ["string"],
      "tags": ["string"],
      "github": "url"
    }
  ],
  "experience": [
    {
      "company": "string",
      "position": "string",
      "date": "string",
      "description": "string"
    }
  ],
  "education": { },
  "contact": { }
}
```

---

## Kod Kuralları

- **Bileşen isimleri:** PascalCase — `ProjectCard.jsx`, `ChatWindow.jsx`
- **CSS:** Her bileşenin kendi `.module.css` dosyası, global stiller `styles/` altında
- **WebGL sistemleri:** `systems/` dışına taşıma, bileşenlerle karıştırma
- **State:** Yeni global state için Zustand store'u genişlet, local state için `useState` yeterli
- **Backend değişiklikleri:** `/chat` endpoint mantığını değiştirmeden önce sor

---

## Ortam Değişkenleri (`.env`)

```
GROQ_API_KEY=
GITHUB_TOKEN=
```

---

## Geliştirme Ortamı

```bash
# Backend (port 8000)
cd backend
.\venv\Scripts\activate
uvicorn main:app --reload

# Frontend (port 5173)
cd frontend
npm run dev
```

---

## Önemli Notlar

- AI avatar **birinci şahıs** konuşur: "Ben Buğra..." — sistem prompt'u bu şekilde kurulu, değiştirme.
- ChromaDB'yi yeniden oluşturmak gerekirse `build_knowledge_base.py` çalıştır.
- 3D animasyonların renk/hız değişkenleri AI durumuna (konuşma, bekleme vb.) göre dinamik — Zustand store üzerinden yönetiliyor.