"""
index.py — Bilgi indeksi: Chroma (anlamsal) + BM25 (anahtar kelime) + otomatik tazelik.

Tazelik garantisi: Chroma koleksiyonunun metadata'sında, dokümanlardan ve
embedding modelinden hesaplanan bir parmak izi tutulur. knowledge.json'un
mtime'ı her istekte kontrol edilir; içerik, builder mantığı veya model
değiştiyse koleksiyon yeniden kurulur. Elle build_knowledge_base.py çalıştırmayı
unutmak artık eski bilgiyle cevap vermeye yol açmaz.
"""

import logging
import math
import os
import threading
from collections import Counter
from dataclasses import dataclass

from langchain_core.documents import Document

from .knowledge import (
    Entity, TechUsage, build_documents, build_entities, build_profile_digest,
    build_tech_usage, documents_fingerprint, load_knowledge,
)
from .textnorm import bm25_terms

logger = logging.getLogger(__name__)

RRF_K = 60


class BM25:
    """Küçük korpus için bağımlılıksız Okapi BM25."""

    def __init__(self, corpus_terms: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.tfs = [Counter(terms) for terms in corpus_terms]
        self.lens = [len(terms) for terms in corpus_terms]
        self.avgdl = (sum(self.lens) / len(self.lens)) if self.lens else 1.0
        n = len(corpus_terms)
        df = Counter(term for terms in corpus_terms for term in set(terms))
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def scores(self, query_terms: list[str]) -> list[float]:
        terms = set(query_terms)
        out = []
        for tf, dl in zip(self.tfs, self.lens):
            s = 0.0
            for t in terms:
                f = tf.get(t)
                if f:
                    norm = self.k1 * (1 - self.b + self.b * dl / self.avgdl)
                    s += self.idf[t] * f * (self.k1 + 1) / (f + norm)
            out.append(s)
        return out


@dataclass
class Hit:
    doc: Document
    rrf: float
    dense: float              # kosinüs benzerliği (0–1)
    bm25: float
    dense_rank: int
    bm25_rank: int | None     # BM25 eşleşmesi yoksa None

    @property
    def key(self) -> str:
        return self.doc.metadata["record_key"]


@dataclass
class KnowledgeSnapshot:
    fingerprint: str
    kb: dict
    docs: list[Document]
    by_key: dict[str, Document]
    entities: list[Entity]
    tech_usage: dict[str, TechUsage]
    digest: str
    bm25: BM25


class KnowledgeIndex:
    def __init__(self, kb_path: str, persist_dir: str, collection_name: str,
                 embeddings, embedding_model_name: str):
        self.kb_path = kb_path
        self.persist_dir = persist_dir
        self.collection_name = collection_name
        self.embeddings = embeddings
        self.embedding_model_name = embedding_model_name
        self._lock = threading.Lock()
        self._store = None
        self._snapshot: KnowledgeSnapshot | None = None
        self._kb_mtime: int | None = None
        self.last_build_rebuilt = False

    # ── Tazelik ──────────────────────────────────────────────────────
    def snapshot(self) -> KnowledgeSnapshot:
        """Güncel snapshot; knowledge.json değiştiyse önce indeksi tazeler."""
        mtime = os.stat(self.kb_path).st_mtime_ns
        if self._snapshot is None or mtime != self._kb_mtime:
            with self._lock:
                if self._snapshot is None or mtime != self._kb_mtime:
                    self._load(mtime, force=False)
        return self._snapshot

    def rebuild(self) -> KnowledgeSnapshot:
        with self._lock:
            self._load(os.stat(self.kb_path).st_mtime_ns, force=True)
        return self._snapshot

    def _open_store(self, metadata: dict | None = None):
        from langchain_chroma import Chroma
        return Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_dir,
            collection_metadata=metadata,
        )

    def _load(self, mtime: int, force: bool) -> None:
        kb = load_knowledge(self.kb_path)
        docs = build_documents(kb)
        fingerprint = documents_fingerprint(docs, self.embedding_model_name)

        store = self._store or self._open_store()
        stored = store._collection.metadata or {}
        stale = (force or stored.get("kb_fingerprint") != fingerprint
                 or store._collection.count() != len(docs))
        if stale:
            store.delete_collection()
            store = self._open_store({"hnsw:space": "cosine", "kb_fingerprint": fingerprint})
            store.add_documents(docs, ids=[d.metadata["record_key"] for d in docs])
            logger.warning("Bilgi indeksi yeniden kuruldu (%d doküman, %s)", len(docs), fingerprint)
        self.last_build_rebuilt = stale

        self._store = store
        self._snapshot = KnowledgeSnapshot(
            fingerprint=fingerprint,
            kb=kb,
            docs=docs,
            by_key={d.metadata["record_key"]: d for d in docs},
            entities=build_entities(kb),
            tech_usage=build_tech_usage(kb),
            digest=build_profile_digest(kb),
            bm25=BM25([bm25_terms(d.page_content, is_document=True) for d in docs]),
        )
        self._kb_mtime = mtime

    # ── Arama ────────────────────────────────────────────────────────
    def dense_scores(self, query: str, n: int) -> dict[str, float]:
        with self._lock:
            results = self._store.similarity_search_with_score(query, k=n)
        # cosine uzayında Chroma mesafesi = 1 - kosinüs benzerliği
        return {doc.metadata["record_key"]: 1.0 - dist for doc, dist in results}

    def hybrid_search(self, query: str, snap: KnowledgeSnapshot) -> list[Hit]:
        """Anlamsal + BM25 sıralamalarını Reciprocal Rank Fusion ile birleştirir."""
        keys = [d.metadata["record_key"] for d in snap.docs]
        dense = self.dense_scores(query, n=len(keys))
        dense_rank = {k: i + 1 for i, k in enumerate(sorted(dense, key=dense.get, reverse=True))}

        bm = dict(zip(keys, snap.bm25.scores(bm25_terms(query))))
        bm_sorted = [k for k in sorted(bm, key=bm.get, reverse=True) if bm[k] > 0]
        bm_rank = {k: i + 1 for i, k in enumerate(bm_sorted)}

        hits = []
        for key in keys:
            d_rank = dense_rank.get(key, len(keys))
            rrf = 1.0 / (RRF_K + d_rank)
            if key in bm_rank:
                rrf += 1.0 / (RRF_K + bm_rank[key])
            hits.append(Hit(snap.by_key[key], rrf, dense.get(key, 0.0), bm[key],
                            d_rank, bm_rank.get(key)))
        hits.sort(key=lambda h: h.rrf, reverse=True)
        return hits
