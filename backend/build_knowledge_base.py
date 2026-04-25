"""
build_knowledge_base.py — ChromaDB vektör veritabanı oluşturma scripti.

Her knowledge.json kaydı (proje, deneyim, eğitim vb.) ayrı bir Document
olarak indexlenir. Bu sayede MMR araması daha çeşitli ve isabetli sonuçlar döndürür.
"""

import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(__file__))

from config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIR,
    KNOWLEDGE_JSON_PATH,
    LOCAL_EMBEDDING_MODEL,
)

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings


def load_knowledge(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def build_documents(knowledge: dict) -> list[Document]:
    docs: list[Document] = []

    # 1. Hakkında
    if knowledge.get("about"):
        docs.append(Document(
            page_content=f"Hakkında: {knowledge['about']}",
            metadata={"source": "about", "source_type": "about"},
        ))

    # 2. Beceriler — her kategori ayrı belge
    for category, items in knowledge.get("skills", {}).items():
        docs.append(Document(
            page_content=f"Beceri kategorisi: {category}\nBeceriler: {', '.join(items)}",
            metadata={"source": "skills", "source_type": "skills", "category": category},
        ))

    # 3. Projeler — her proje ayrı belge
    for project in knowledge.get("projects", []):
        parts = [
            f"Proje: {project['name']}",
            f"Kısa açıklama: {project.get('short_description', '')}",
            f"Detaylı açıklama: {project.get('long_description', '')}",
            f"Teknoloji yığını: {', '.join(project.get('stack', []))}",
            f"Etiketler: {', '.join(project.get('tags', []))}",
        ]
        if project.get("achievement"):
            parts.append(f"Başarı / Ödül: {project['achievement']}")
        if project.get("github"):
            parts.append(f"GitHub: {project['github']}")
        if project.get("url"):
            parts.append(f"URL: {project['url']}")

        docs.append(Document(
            page_content="\n".join(parts),
            metadata={
                "source": "project",
                "source_type": "project",
                "project_name": project["name"],
                "github": project.get("github", ""),
                "tags": ", ".join(project.get("tags", [])),
            },
        ))

    # 4. Deneyim — her kayıt ayrı belge
    for exp in knowledge.get("experience", []):
        content = (
            f"İş deneyimi — {exp['company']}\n"
            f"Pozisyon: {exp['position']}\n"
            f"Tarih: {exp['date']}\n"
            f"Açıklama: {exp['description']}"
        )
        docs.append(Document(
            page_content=content,
            metadata={
                "source": "experience",
                "source_type": "experience",
                "company": exp.get("company", ""),
                "position": exp.get("position", ""),
            },
        ))

    # 5. Eğitim — her kayıt ayrı belge
    for edu in knowledge.get("education", []) if isinstance(knowledge.get("education"), list) else []:
        content = (
            f"Eğitim — {edu.get('school', '')}\n"
            f"Derece: {edu.get('degree', '')} — {edu.get('field', '')}\n"
            f"Dönem: {edu.get('period', '')}\n"
            f"Açıklama: {edu.get('description', '')}"
        )
        docs.append(Document(
            page_content=content,
            metadata={"source": "education", "source_type": "education"},
        ))

    # 6. Sertifikalar — tek belge
    certs = knowledge.get("certifications", [])
    if certs:
        docs.append(Document(
            page_content="Sertifikalar ve ödüller:\n" + "\n".join(f"- {c}" for c in certs),
            metadata={"source": "certifications", "source_type": "certifications"},
        ))

    # 7. Konu özetleri — sıkça sorulan konular için odaklı belgeler
    # Huawei özeti: tüm HSD rolleri + Huawei sertifikaları tek chunk'ta
    huawei_exps = [
        e for e in knowledge.get("experience", [])
        if "HSD" in e.get("company", "") or "HUAWEI" in e.get("company", "")
    ]
    huawei_certs = [
        c for c in certs
        if any(kw in c for kw in ["Huawei", "HCCDA", "HCSD"])
    ]
    if huawei_exps or huawei_certs:
        roles = "\n".join(
            f"- {e['position']} ({e['date']})" for e in huawei_exps
        )
        cert_list = ", ".join(huawei_certs) if huawei_certs else "—"
        docs.append(Document(
            page_content=(
                "Huawei ekosistemindeki rollerim ve sertifikalarım:\n"
                f"Roller:\n{roles}\n"
                f"Huawei sertifikalarım: {cert_list}"
            ),
            metadata={"source": "topic_summary", "source_type": "topic_summary", "topic": "huawei"},
        ))

    return docs


def split_if_large(docs: list[Document], chunk_size: int, chunk_overlap: int) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " "],
    )
    result: list[Document] = []
    for doc in docs:
        if len(doc.page_content) > chunk_size:
            result.extend(splitter.split_documents([doc]))
        else:
            result.append(doc)
    return result


def main() -> None:
    print("Knowledge base yükleniyor...")
    knowledge = load_knowledge(KNOWLEDGE_JSON_PATH)

    print("Dokümanlar oluşturuluyor...")
    docs = build_documents(knowledge)
    print(f"  Ham doküman sayısı: {len(docs)}")

    docs = split_if_large(docs, CHUNK_SIZE, CHUNK_OVERLAP)
    print(f"  Chunk sonrası toplam: {len(docs)} doküman")

    if os.path.exists(CHROMA_PERSIST_DIR):
        print(f"Mevcut ChromaDB siliniyor: {CHROMA_PERSIST_DIR}")
        try:
            shutil.rmtree(CHROMA_PERSIST_DIR)
        except PermissionError:
            print(
                "\nHATA: ChromaDB dosyası başka bir işlem tarafından kullanılıyor.\n"
                "Uvicorn/backend sunucusunu durdurup tekrar çalıştır.\n"
            )
            sys.exit(1)

    print(f"Embedding modeli yükleniyor: {LOCAL_EMBEDDING_MODEL}")
    embeddings = HuggingFaceEmbeddings(
        model_name=LOCAL_EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    print("ChromaDB oluşturuluyor...")
    vectorstore = Chroma.from_documents(
        documents=docs,
        embedding=embeddings,
        collection_name=CHROMA_COLLECTION_NAME,
        persist_directory=CHROMA_PERSIST_DIR,
    )

    count = vectorstore._collection.count()
    print(f"\nTamamlandi! {count} doküman indexlendi.")
    print(f"Konum: {CHROMA_PERSIST_DIR}")


if __name__ == "__main__":
    main()
