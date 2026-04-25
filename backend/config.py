# Uvicorn reload tetikleyici
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'), override=True)

# Groq API anahtarı (.env dosyasından okunur, asla loga yazılmaz)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


# knowledge.json dosyasının yolu
KNOWLEDGE_JSON_PATH = os.path.join(os.path.dirname(__file__), "data", "knowledge.json")

# ChromaDB kalıcı depolama dizini (git'e ekleme!)
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "data", "chroma_db")

# ChromaDB koleksiyon adı
CHROMA_COLLECTION_NAME = "bugra_knowledge"

# OpenAI embedding modeli (sadece EMBEDDING_PROVIDER=openai olduğunda kullanılır)
EMBEDDING_MODEL = "text-embedding-3-small"

# Embedding sağlayıcısı: 'openai' veya 'local'
# 'local' seçilirse sentence-transformers kullanılır (internet gerekmez)
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "local")

# Yerel embedding modeli (EMBEDDING_PROVIDER=local olduğunda)
LOCAL_EMBEDDING_MODEL = os.getenv("LOCAL_EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Chat modeli (Groq üzerinden)
CHAT_MODEL = os.getenv("CHAT_MODEL", "llama-3.3-70b-versatile")

# Her chunk'ın maksimum karakter boyutu
CHUNK_SIZE = 600

# Chunk'lar arasındaki örtüşme miktarı (karakter)
CHUNK_OVERLAP = 120

# RAG'ın getireceği maksimum benzer belge sayısı
TOP_K_RESULTS = 4

# MMR arama için aday havuzu (TOP_K_RESULTS'tan büyük olmalı)
MMR_FETCH_K = 12

# Konuşma geçmişinden LLM'e iletilecek tur sayısı (1 tur = 1 kullanıcı + 1 asistan mesajı)
MAX_HISTORY_TURNS = 3

# İzin verilen CORS origin'leri
ALLOWED_ORIGINS = [
    "http://localhost:5173",   # Vite dev server
    "http://localhost:4173",   # Vite preview
    "https://bugrayildirim.vercel.app",
]

# LLM sistem prompt şablonu
SYSTEM_PROMPT = """Buğra Yıldırım'ın dijital klonusun. Buğra, Balıkesir Üniversitesi Bilgisayar Mühendisliği öğrencisi; yapay zeka, derin öğrenme ve yazılım geliştirme alanlarında aktif çalışan bir mühendistir.

Aşağıdaki bağlamı ve sohbet geçmişini kullanarak soruları Buğra'nın ağzından, birinci şahıs olarak yanıtla. Sorunun diline (Türkçe veya İngilizce) göre cevap ver.

Kurallar:
- Bağlamda olmayan bilgileri uydurmak yerine "Bu konuda elimde bilgi yok, bana doğrudan sorabilirsin" de.
- Kısa ve öz ol (2–5 cümle); teknik derinlik gerektiren sorularda biraz daha ayrıntılı açıkla.
- Kibarca, meraklı ve samimi bir ton kullan — gerçek bir insanla sohbet ediyormuş hissini yansıt.
- Sohbet geçmişindeki bağlamı hatırla ve tutarlı yanıt ver.
- Unvan ve pozisyon isimlerini bağlamdan olduğu gibi kullan, parafraz yapma (örn. "Kampüs Elçisi" → "Büyükelçisi" yazma).
- İletişim için e-posta adresimi (bugrayil351@gmail.com) ve LinkedIn profilimi (https://www.linkedin.com/in/bugra-yildirim) paylaşabilirsin. Telefon numaramı asla paylaşma.

Bağlam:
{context}"""
