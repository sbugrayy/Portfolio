#!/usr/bin/env python3
"""
build_knowledge_base.py — ChromaDB bilgi tabanı oluşturma scripti

Çalıştır: python scripts/build_knowledge_base.py
Gereksinim: .env dosyasında OPENAI_API_KEY tanımlı olmalı.
"""

import json
import os
import re
import sys
import shutil

# backend/ klasörünü path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_chroma import Chroma

from config import (
    OPENAI_API_KEY, OPENAI_BASE_URL, GITHUB_TOKEN, GITHUB_REPOS,
    CV_PDF_PATH, KNOWLEDGE_JSON_PATH, CHROMA_PERSIST_DIR,
    CHROMA_COLLECTION_NAME, EMBEDDING_MODEL, EMBEDDING_PROVIDER,
    LOCAL_EMBEDDING_MODEL, CHUNK_SIZE, CHUNK_OVERLAP,
)


def get_embeddings():
    """EMBEDDING_PROVIDER'a göre doğru embedding fonksiyonunu döndürür."""
    if EMBEDDING_PROVIDER == "local":
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            from langchain_community.embeddings import HuggingFaceEmbeddings
        print(f"  ℹ️  Yerel embedding modeli kullanılıyor: {LOCAL_EMBEDDING_MODEL}")
        return HuggingFaceEmbeddings(
            model_name=LOCAL_EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    else:
        from langchain_openai import OpenAIEmbeddings
        print(f"  ℹ️  OpenAI embedding kullanılıyor: {EMBEDDING_MODEL}")
        kwargs = {}
        if OPENAI_BASE_URL:
            kwargs["openai_api_base"] = OPENAI_BASE_URL
        return OpenAIEmbeddings(
            model=EMBEDDING_MODEL,
            openai_api_key=OPENAI_API_KEY,
            **kwargs,
        )


def clean_markdown(text: str) -> str:
    """Temel Markdown işaretlerini temizler."""
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)             # Resimler
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Linkler
    text = re.sub(r'#{1,6}\s+', '', text)                  # Başlıklar
    text = re.sub(r'\*{1,2}([^*]+)\*{1,2}', r'\1', text)  # Bold/italic
    text = re.sub(r'`{1,3}[^`]*`{1,3}', '', text)         # Code
    text = re.sub(r'\n{3,}', '\n\n', text)                 # Fazla boşluk
    return text.strip()


def load_knowledge_json() -> list[Document]:
    """knowledge.json dosyasından LangChain Document listesi oluşturur."""
    docs = []
    with open(KNOWLEDGE_JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Hakkımda bölümü
    if data.get("about"):
        docs.append(Document(
            page_content=f"Hakkımda: {data['about']}",
            metadata={"source": "json", "section": "about", "project_name": None, "tags": ""},
        ))

    # Yetenekler bölümü
    if data.get("skills"):
        skills = data["skills"]
        if isinstance(skills, dict):
            parts = [f"{cat}: {', '.join(items)}" for cat, items in skills.items()]
            skills_text = "Yeteneklerim — " + "; ".join(parts)
        else:
            skills_text = "Yeteneklerim: " + ", ".join(skills)
        docs.append(Document(
            page_content=skills_text,
            metadata={"source": "json", "section": "skills", "project_name": None, "tags": ""},
        ))

    # Her proje ayrı doküman
    for project in data.get("projects", []):
        lines = [f"Proje: {project['name']}"]
        if project.get("description"):
            lines.append(f"Açıklama: {project['description']}")
        if project.get("longDescription"):
            lines.append(f"Detay: {project['longDescription']}")
        if project.get("stack"):
            lines.append(f"Teknoloji: {', '.join(project['stack'])}")
        if project.get("tags"):
            lines.append(f"Etiketler: {', '.join(project['tags'])}")
        if project.get("year"):
            lines.append(f"Yıl: {project['year']}")
        if project.get("achievement"):
            lines.append(f"Başarı: {project['achievement']}")

        docs.append(Document(
            page_content="\n".join(lines),
            metadata={
                "source": "json",
                "section": "project",
                "project_name": project["name"],
                "github": project.get("github", ""),
                "tags": ",".join(project.get("tags", [])),
            },
        ))

    # Deneyimler
    for exp in data.get("experience", []):
        lines = [
            f"Deneyim: {exp.get('company', '')}",
            f"Pozisyon: {exp.get('position', '')}",
            f"Süre: {exp.get('period', '')}",
        ]
        if exp.get("description"):
            lines.append(f"Açıklama: {exp['description']}")
        docs.append(Document(
            page_content="\n".join(lines),
            metadata={"source": "json", "section": "experience", "project_name": None, "tags": ""},
        ))

    # Eğitim
    edu = data.get("education", {})
    if edu:
        edu_text = (
            f"Eğitim: {edu.get('school', '')}\n"
            f"Bölüm: {edu.get('degree', '')}\n"
            f"Dönem: {edu.get('period', '')}\n"
            f"Açıklama: {edu.get('description', '')}"
        )
        docs.append(Document(
            page_content=edu_text,
            metadata={"source": "json", "section": "education", "project_name": None, "tags": ""},
        ))

    print(f"✓ knowledge.json → {len(docs)} doküman yüklendi")
    return docs


def load_github_readmes() -> list[Document]:
    """GitHub repo README'lerini çeker ve doküman oluşturur."""
    if not GITHUB_TOKEN:
        print("⚠  GITHUB_TOKEN bulunamadı — GitHub README'leri atlanıyor")
        return []

    try:
        from github import Github
    except ImportError:
        print("⚠  PyGithub kurulu değil — GitHub README'leri atlanıyor")
        return []

    from github import Auth
    g = Github(auth=Auth.Token(GITHUB_TOKEN))
    docs = []

    for repo_name in GITHUB_REPOS:
        try:
            repo = g.get_repo(repo_name)
            readme = repo.get_readme()
            raw = readme.decoded_content.decode('utf-8')
            content = clean_markdown(raw)

            if len(content) < 50:
                continue

            docs.append(Document(
                page_content=f"GitHub Repo ({repo.name}):\n{content[:2500]}",
                metadata={
                    "source": "github",
                    "section": "readme",
                    "project_name": repo.name,
                    "github": repo.html_url,
                    "tags": "",
                },
            ))
            print(f"  ✓ {repo_name}")
        except Exception as exc:
            print(f"  ⚠  {repo_name} → {exc}")

    print(f"✓ GitHub → {len(docs)} doküman yüklendi")
    return docs


def load_cv_pdf() -> list[Document]:
    """CV PDF dosyasını parse ederek doküman oluşturur (opsiyonel)."""
    if not os.path.exists(CV_PDF_PATH):
        print(f"⚠  CV PDF bulunamadı ({CV_PDF_PATH}) — atlanıyor")
        return []

    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("⚠  PyMuPDF kurulu değil — CV PDF atlanıyor")
        return []

    try:
        doc = fitz.open(CV_PDF_PATH)
        full_text = "\n".join(page.get_text() for page in doc)
        doc.close()

        if not full_text.strip():
            return []

        print(f"✓ CV PDF → {len(full_text)} karakter")
        return [Document(
            page_content=full_text,
            metadata={"source": "pdf", "section": "cv", "project_name": None, "tags": ""},
        )]
    except Exception as exc:
        print(f"⚠  CV PDF hatası: {exc}")
        return []


def build_vectorstore(all_docs: list[Document]) -> None:
    """Dokümanları chunk'lara böler, embed eder ve ChromaDB'ye yazar."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
    )
    chunks = splitter.split_documents(all_docs)
    print(f"✓ Toplam {len(chunks)} chunk oluşturuldu")

    # Mevcut ChromaDB'yi sıfırla (uvicorn açıksa kilitli olabilir — atlanır)
    if os.path.exists(CHROMA_PERSIST_DIR):
        try:
            shutil.rmtree(CHROMA_PERSIST_DIR)
            print(f"✓ Mevcut ChromaDB silindi")
        except PermissionError:
            print("⚠  ChromaDB dosyası kilitli (uvicorn çalışıyor olabilir).")
            print("   Mevcut koleksiyonun üzerine yazılıyor...")
    os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)

    embeddings = get_embeddings()

    print("⏳ Embedding işlemi başlıyor (OpenAI API'ye istek atılıyor)...")
    BATCH = 50  # Rate limit için 50'lik gruplar
    vectorstore = None

    for i in range(0, len(chunks), BATCH):
        batch = chunks[i:i + BATCH]
        if vectorstore is None:
            vectorstore = Chroma.from_documents(
                documents=batch,
                embedding=embeddings,
                collection_name=CHROMA_COLLECTION_NAME,
                persist_directory=CHROMA_PERSIST_DIR,
            )
        else:
            vectorstore.add_documents(batch)
        print(f"  Batch {i // BATCH + 1}/{(len(chunks) - 1) // BATCH + 1} ✓")

    print(f"\n🎉 ChromaDB başarıyla oluşturuldu!")
    print(f"   Konum  : {CHROMA_PERSIST_DIR}")
    print(f"   Chunk  : {len(chunks)}")
    print(f"   Doküman: {len(all_docs)}")


if __name__ == "__main__":
    print("=" * 55)
    print("  Buğra AI Avatar — Knowledge Base Builder")
    print("=" * 55)

    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY bulunamadı! .env dosyasını kontrol et.")
        sys.exit(1)

    all_docs: list[Document] = []
    all_docs.extend(load_knowledge_json())
    all_docs.extend(load_github_readmes())
    all_docs.extend(load_cv_pdf())

    if not all_docs:
        print("❌ Hiç doküman yüklenemedi!")
        sys.exit(1)

    print(f"\n📚 Toplam {len(all_docs)} doküman → ChromaDB oluşturuluyor...\n")
    build_vectorstore(all_docs)
