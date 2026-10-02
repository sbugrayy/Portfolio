"""
build_knowledge_base.py — ChromaDB bilgi indeksini kurar ve özetini yazdırır.

Normalde elle çalıştırmak gerekmez: backend her istekte knowledge.json'un
değişip değişmediğine bakar ve indeksi kendisi tazeler. Bu script Docker
build'inde embedding modelini önceden indirip indeksi imaja gömmek ve
derlenen dokümanları/profil özetini incelemek için kullanılır.

Kullanım:
    python build_knowledge_base.py           # gerekiyorsa kur
    python build_knowledge_base.py --force   # her durumda sıfırdan kur
    python build_knowledge_base.py --show    # dokümanları ve profil özetini yazdır
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    CHROMA_COLLECTION_NAME, CHROMA_PERSIST_DIR, KNOWLEDGE_JSON_PATH, LOCAL_EMBEDDING_MODEL,
)
from rag.embeddings import SentenceTransformerEmbeddings
from rag.index import KnowledgeIndex


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    force = "--force" in sys.argv
    show = "--show" in sys.argv

    print(f"Embedding modeli yükleniyor: {LOCAL_EMBEDDING_MODEL}")
    index = KnowledgeIndex(
        kb_path=KNOWLEDGE_JSON_PATH,
        persist_dir=CHROMA_PERSIST_DIR,
        collection_name=CHROMA_COLLECTION_NAME,
        embeddings=SentenceTransformerEmbeddings(LOCAL_EMBEDDING_MODEL),
        embedding_model_name=LOCAL_EMBEDDING_MODEL,
    )
    snap = index.rebuild() if force else index.snapshot()

    state = "yeniden kuruldu" if index.last_build_rebuilt else "zaten güncel"
    print(f"İndeks {state}: {len(snap.docs)} doküman, parmak izi {snap.fingerprint}")
    print(f"Konum: {CHROMA_PERSIST_DIR}")
    print(f"Varlık (proje/şirket/okul) sayısı: {len(snap.entities)}, "
          f"teknoloji sayısı: {len(snap.tech_usage)}, profil özeti: {len(snap.digest)} karakter")

    if show:
        print("\n── Profil özeti ──\n" + snap.digest)
        for doc in snap.docs:
            print(f"\n── {doc.metadata['record_key']} ({len(doc.page_content)} karakter) ──")
            print(doc.page_content)


if __name__ == "__main__":
    main()
