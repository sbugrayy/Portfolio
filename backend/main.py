"""
main.py — FastAPI AI Avatar Backend
POST /chat endpoint: RAG pipeline ile cevap üretir (bkz. rag/pipeline.py).
"""

import logging
import sys
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Yalnızca hata logu — kullanıcı sorguları asla loglanmaz
logging.basicConfig(level=logging.ERROR, stream=sys.stderr)
logger = logging.getLogger(__name__)

from config import (
    GROQ_API_KEY, CHROMA_PERSIST_DIR, CHROMA_COLLECTION_NAME, KNOWLEDGE_JSON_PATH,
    LOCAL_EMBEDDING_MODEL, CHAT_MODEL, CHAT_MODEL_FALLBACKS, LLM_MODEL_OPTIONS,
    LLM_TEMPERATURE, LLM_MAX_TOKENS, MAX_HISTORY_TURNS, MAX_SEARCH_RECORDS,
    MAX_PINNED_RECORDS, DENSE_OOD_THRESHOLD, DENSE_MARGIN, SYSTEM_PROMPT, ALLOWED_ORIGINS,
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

# ── RAG pipeline başlatma ────────────────────────────────────────────
try:
    from rag.embeddings import SentenceTransformerEmbeddings
    from rag.index import KnowledgeIndex
    from rag.pipeline import ChatPipeline, GroqChain, PipelineSettings

    _index = KnowledgeIndex(
        kb_path=KNOWLEDGE_JSON_PATH,
        persist_dir=CHROMA_PERSIST_DIR,
        collection_name=CHROMA_COLLECTION_NAME,
        embeddings=SentenceTransformerEmbeddings(LOCAL_EMBEDDING_MODEL),
        embedding_model_name=LOCAL_EMBEDDING_MODEL,
    )
    _index.snapshot()  # İndeks eski/eksikse açılışta yeniden kurulur

    _pipeline = ChatPipeline(
        index=_index,
        settings=PipelineSettings(
            system_prompt=SYSTEM_PROMPT,
            max_history_turns=MAX_HISTORY_TURNS,
            max_search_records=MAX_SEARCH_RECORDS,
            max_pinned_records=MAX_PINNED_RECORDS,
            dense_ood_threshold=DENSE_OOD_THRESHOLD,
            dense_margin=DENSE_MARGIN,
        ),
        llm_chain=GroqChain(
            api_key=GROQ_API_KEY,
            models=[CHAT_MODEL, *CHAT_MODEL_FALLBACKS],
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
            model_options=LLM_MODEL_OPTIONS,
        ),
    )
except Exception as _init_err:
    logger.error("Başlatma hatası: %s", _init_err, exc_info=True)
    _index = None
    _pipeline = None


# ── Pydantic şemaları ────────────────────────────────────────────────
class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]   # 'system' rolüyle prompt enjeksiyonu engellenir
    content: str                         # uzun içerik pipeline'da kırpılır


class ChatRequest(BaseModel):
    query: str                           # 1000 karakterden sonrası pipeline'da kırpılır
    history: list[HistoryMessage] = Field(default=[], max_length=20)
    lang: Optional[Literal["tr", "en"]] = None   # arayüz dili (soru dili belirsizse kullanılır)


class SourceInfo(BaseModel):
    project_name: Optional[str] = None
    source_type: str
    github: Optional[str] = None
    tags: list[str] = []


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceInfo]
    stem_hint: str  # 'bass' | 'arp' | 'pad'


# ── Endpoint'ler ─────────────────────────────────────────────────────
@app.get("/health")
def health():
    """Backend sağlık kontrolü."""
    if _index is None:
        return {"status": "ok", "vectorstore": False}
    snap = _index.snapshot()
    return {
        "status": "ok",
        "vectorstore": True,
        "documents": len(snap.docs),
        "kb_fingerprint": snap.fingerprint,
        "embedding_model": LOCAL_EMBEDDING_MODEL,
        "chat_models": [CHAT_MODEL, *CHAT_MODEL_FALLBACKS],
    }


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """Ana RAG chat endpoint'i. Kullanıcı sorgularını loglamaz.

    Senkron tanımlı: FastAPI bunu thread havuzunda çalıştırır, böylece bloklayan
    embedding/LLM çağrıları diğer istekleri dondurmaz.
    """
    if not req.query or not req.query.strip():
        raise HTTPException(status_code=400, detail="Sorgu boş olamaz")

    if _pipeline is None:
        raise HTTPException(
            status_code=503,
            detail="Servis hazır değil. Backend loglarını kontrol edin.",
        )

    try:
        result = _pipeline.answer(
            req.query,
            [h.model_dump() for h in req.history],
            ui_lang=req.lang,
        )
        return ChatResponse(
            answer=result["answer"],
            sources=[SourceInfo(**s) for s in result["sources"]],
            stem_hint=result["stem_hint"],
        )
    except Exception as exc:
        logger.error("Chat endpoint hatası: %s", type(exc).__name__, exc_info=True)
        raise HTTPException(status_code=500, detail="Bir hata oluştu, lütfen tekrar deneyin")
