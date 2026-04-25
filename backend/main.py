"""
main.py — FastAPI AI Avatar Backend
POST /chat endpoint: RAG pipeline ile cevap üretir.
"""

import logging
import sys
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Yalnızca hata logu — kullanıcı sorguları asla loglanmaz
logging.basicConfig(level=logging.ERROR, stream=sys.stderr)
logger = logging.getLogger(__name__)

from config import (
    GROQ_API_KEY, CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME,
    LOCAL_EMBEDDING_MODEL, CHAT_MODEL, TOP_K_RESULTS, MMR_FETCH_K,
    MAX_HISTORY_TURNS, SYSTEM_PROMPT, ALLOWED_ORIGINS,
)

# ── FastAPI ──────────────────────────────────────────────────────────
app = FastAPI(
    title="AI Avatar Backend",
    description="Buğra'nın dijital klonu API'si",
    docs_url=None,   # Swagger UI kapalı (güvenlik)
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── LangChain + ChromaDB başlatma ────────────────────────────────────
try:
    from langchain_groq import ChatGroq
    from langchain_chroma import Chroma

    # Embedding: local (sentence-transformers)
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError:
        from langchain_community.embeddings import HuggingFaceEmbeddings
    _embeddings = HuggingFaceEmbeddings(
        model_name=LOCAL_EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    _vectorstore = Chroma(
        collection_name=CHROMA_COLLECTION_NAME,
        embedding_function=_embeddings,
        persist_directory=CHROMA_PERSIST_DIR,
    )

    _llm = ChatGroq(
        model=CHAT_MODEL,
        groq_api_key=GROQ_API_KEY,
        temperature=0.5,
        max_tokens=600,
    )
except Exception as _init_err:
    logger.error("Başlatma hatası: %s", _init_err)
    _vectorstore = None
    _llm = None


# ── Pydantic şemaları ────────────────────────────────────────────────
class HistoryMessage(BaseModel):
    role: str   # 'user' | 'assistant'
    content: str


class ChatRequest(BaseModel):
    query: str
    history: list[HistoryMessage] = []


class SourceInfo(BaseModel):
    project_name: Optional[str] = None
    source_type: str
    github: Optional[str] = None
    tags: list[str] = []


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceInfo]
    stem_hint: str  # 'bass' | 'arp' | 'pad'


# ── Yardımcı fonksiyonlar ────────────────────────────────────────────
def _parse_tags(raw) -> list[str]:
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str) and raw:
        return [t.strip() for t in raw.split(",") if t.strip()]
    return []


def _determine_stem_hint(sources: list[SourceInfo]) -> str:
    """Kaynak listesine göre ses stem ipucu belirler."""
    if not sources:
        return "pad"
    if any(s.project_name for s in sources):
        return "bass"
    return "arp"


# ── Endpoint'ler ─────────────────────────────────────────────────────
@app.get("/health")
async def health():
    """Backend sağlık kontrolü."""
    return {"status": "ok", "vectorstore": _vectorstore is not None}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Ana RAG chat endpoint'i. Kullanıcı sorgularını loglamaz."""
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Sorgu boş olamaz")

    if _vectorstore is None or _llm is None:
        raise HTTPException(
            status_code=503,
            detail="Servis hazır değil. build_knowledge_base.py çalıştırıldı mı?",
        )

    try:
        query = req.query.strip()

        # MMR: çeşitli belgeler getir (aynı kaynaktan 3 chunk gelmesini engeller)
        docs = _vectorstore.max_marginal_relevance_search(
            query, k=TOP_K_RESULTS, fetch_k=MMR_FETCH_K
        )

        # RAG bağlamı oluştur
        context = "\n\n".join(doc.page_content for doc in docs)

        # Mesaj listesi: system → geçmiş → şimdiki sorgu
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(context=context)},
        ]
        for h in req.history[-(MAX_HISTORY_TURNS * 2):]:
            messages.append({"role": h.role, "content": h.content})
        messages.append({"role": "user", "content": query})

        response = _llm.invoke(messages)
        answer: str = response.content

        # Kaynak metadata'sı (duplicate'siz)
        sources: list[SourceInfo] = []
        seen: set[str] = set()
        for doc in docs:
            meta = doc.metadata
            project_name = meta.get("project_name") or None
            source_type = meta.get("source", "json")
            github = meta.get("github") or None
            tags = _parse_tags(meta.get("tags", ""))

            key = f"{project_name}|{source_type}"
            if key not in seen:
                seen.add(key)
                sources.append(SourceInfo(
                    project_name=project_name,
                    source_type=source_type,
                    github=github,
                    tags=tags,
                ))

        return ChatResponse(
            answer=answer,
            sources=sources,
            stem_hint=_determine_stem_hint(sources),
        )

    except Exception as exc:
        logger.error("Chat endpoint hatası: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Bir hata oluştu, lütfen tekrar deneyin")
