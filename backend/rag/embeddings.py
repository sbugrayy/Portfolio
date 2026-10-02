"""
embeddings.py — sentence-transformers için prompt/prefix farkındalıklı embedding sarmalayıcı.

Asimetrik retrieval modelleri sorgu ve dokümanı farklı önekle bekler
(e5: "query: " / "passage: ", Qwen3-Embedding: sorgu için talimat). Öneki
unutmak isabeti ciddi düşürür; bu yüzden ayarlar model adına göre otomatik seçilir.
"""

from langchain_core.embeddings import Embeddings

# Bilinen modeller için sorgu/doküman önekleri
EMBEDDING_PRESETS: dict[str, dict] = {
    "intfloat/multilingual-e5-small": {"query_prompt": "query: ", "doc_prompt": "passage: "},
    "intfloat/multilingual-e5-base": {"query_prompt": "query: ", "doc_prompt": "passage: "},
    "intfloat/multilingual-e5-large": {"query_prompt": "query: ", "doc_prompt": "passage: "},
    "Qwen/Qwen3-Embedding-0.6B": {
        "query_prompt": "Instruct: Given a visitor's question about a software engineer's "
                        "portfolio, retrieve the portfolio entry that answers it\nQuery: ",
    },
    "BAAI/bge-m3": {},
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2": {},
}


class SentenceTransformerEmbeddings(Embeddings):
    def __init__(self, model_name: str, max_seq_length: int = 512, device: str = "cpu"):
        from sentence_transformers import SentenceTransformer

        preset = EMBEDDING_PRESETS.get(model_name, {})
        self.model_name = model_name
        self.query_prompt = preset.get("query_prompt")
        self.doc_prompt = preset.get("doc_prompt")
        self.model = SentenceTransformer(model_name, device=device)
        # Uzun bağlamlı modellerde (bge-m3: 8192) CPU maliyetini sınırla
        if self.model.max_seq_length and self.model.max_seq_length > max_seq_length:
            self.model.max_seq_length = max_seq_length

    def _encode(self, texts: list[str], prompt: str | None) -> list[list[float]]:
        vectors = self.model.encode(
            texts, prompt=prompt, normalize_embeddings=True,
            batch_size=16, show_progress_bar=False,
        )
        return vectors.tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._encode(list(texts), self.doc_prompt)

    def embed_query(self, text: str) -> list[float]:
        return self._encode([text], self.query_prompt)[0]
