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
    │   ├── knowledge.json   # RAG knowledge base kaynağı (tek doğruluk kaynağı)
    │   └── cv.pdf           # Embedding kaynağı
    ├── rag/
    │   ├── textnorm.py      # Türkçe'ye duyarlı normalizasyon (İ/ı, ş/s…), BM25 terimleri
    │   ├── knowledge.py     # knowledge.json → kayıt dokümanları, profil özeti, varlıklar, teknoloji haritası
    │   ├── embeddings.py    # sentence-transformers sarmalayıcı (e5/Qwen3 sorgu önekleri)
    │   ├── index.py         # Chroma + BM25 hibrit arama, parmak izi ile otomatik tazelik
    │   └── pipeline.py      # soru analizi → bağlam seçimi → prompt → Groq (yedekli) → temiz cevap
    ├── eval/
    │   ├── golden_set.json  # regresyon test soruları (beklenen kayıtlar + olgular)
    │   └── run_eval.py      # retrieval (çevrimdışı) ve uçtan uca (--e2e) değerlendirme
    ├── main.py              # FastAPI giriş noktası, /chat endpoint burada
    ├── config.py            # Ortam değişkenleri, RAG ayarları ve SYSTEM_PROMPT
    └── build_knowledge_base.py  # İndeksi kurar/inceler (--force, --show)
```

### RAG akışı (backend/rag)

1. **Profil özeti** — knowledge.json'dan otomatik üretilir, her istekte prompt'a girer (tüm projeler, roller, eğitim, iletişim). Toplu sorular ("tüm projelerin?") retrieval'a bırakılmaz.
2. **Sabitleme** — soruda adı/alias'ı geçen proje/şirket/okul, niyet kalıpları (iletişim, diller, "şu an nerede…") ve takip sorularında önceki turun varlıkları doğrudan bağlama eklenir.
3. **Hibrit arama** — anlamsal (Chroma) + BM25, RRF ile birleştirilir; alaka kapısı alan dışı sorularda kayıt seçmez.
4. **Teknoloji haritası** — "X kullandın mı?" sorularında X'i kullanan proje/roller deterministik olarak verilir (uydurmayı engeller).
5. **Groq zinciri** — `CHAT_MODEL` başarısız olursa (model kaldırıldı / 429 / zaman aşımı) `CHAT_MODEL_FALLBACKS` sırayla denenir. Çıktıdan Markdown ve `<think>` temizlenir.
6. **Tazelik** — indeks, dokümanlar + embedding modelinden hesaplanan parmak iziyle saklanır; knowledge.json değişince ilk istekte kendini yeniden kurar.

---

## Tech Stack

| Katman | Teknoloji |
|---|---|
| Frontend | React, Vite, JavaScript, CSS Modules |
| 3D / WebGL | Three.js (systems/ altında kapsüllü) |
| State | Zustand |
| Backend | Python, FastAPI, Uvicorn |
| AI / RAG | LangChain, ChromaDB + BM25 hibrit arama, Groq API (qwen/qwen3.8-27b → openai/gpt-oss-120b → openai/gpt-oss-20b yedek zinciri) |
| Embedding | sentence-transformers (`LOCAL_EMBEDDING_MODEL`, config.py) |

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
      "aliases": ["string"],          // opsiyonel — soruda geçince bu kaydı bağlama sabitler
      "short_description": "string",
      "long_description": "string",
      "stack": ["string"],
      "tags": ["string"],
      "achievement": "string",        // opsiyonel — ödül/derece (profil özetinde listelenir)
      "github": "url",
      "url": "url"                    // opsiyonel — canlı bağlantı
    }
  ],
  "experience": [
    {
      "company": "string",
      "aliases": ["string"],          // opsiyonel
      "position": "string",
      "date": "string",               // "Günümüz"/"Devam" içeriyorsa güncel rol sayılır
      "description": "string"
    }
  ],
  "education": [{ "school": "", "aliases": [], "degree": "", "field": "", "period": "", "description": "" }],
  "certifications": ["string"],
  "languages": ["string"],
  "contact": { "email": "", "linkedin": "", "github": "", "medium": "", "youtube": "" },
  "faq": [{ "q": "string", "a": "string" }]   // opsiyonel — sık sorulan sorulara kendi cevapların
}
```

- Yeni proje/şirket eklerken kısa ve **ayırt edici** alias'lar ekle (ör. "tekstil kusur" → SFDDS). Birden çok kayda uyan genel kelimeleri ("proje", "oyun") alias yapma.
- Değişiklikten sonra: `python eval/run_eval.py` (retrieval, ücretsiz) — gerekirse `--e2e` ile LLM cevaplarını da kontrol et.

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
CHAT_MODEL=                # opsiyonel, varsayılan qwen/qwen3.8-27b
CHAT_MODEL_FALLBACKS=      # opsiyonel, virgülle ayrılmış yedek modeller
LOCAL_EMBEDDING_MODEL=     # opsiyonel, değişince indeks otomatik yeniden kurulur
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
- ChromaDB elle yeniden kurulmak zorunda değil: knowledge.json, doküman üretim mantığı veya embedding modeli değişince backend ilk istekte indeksi kendisi yeniler. Zorla kurmak/incelemek için `python build_knowledge_base.py --force` / `--show`.
- Groq limitleri dardır (qwen3.8-27b: 8K TPM, 200K TPD); prompt'un sabit kısmı (kurallar + profil) başta, değişken kısmı sonda tutulur — bu sıralamayı bozma (gpt-oss modellerinde önbellek isabeti sağlar).
- 3D animasyonların renk/hız değişkenleri AI durumuna (konuşma, bekleme vb.) göre dinamik — Zustand store üzerinden yönetiliyor.