"""
pipeline.py — Soru → analiz → bağlam seçimi → prompt → LLM → temiz cevap + kaynak kartları.

Bağlam üç katmandan kurulur:
  1. Profil özeti   — her istekte; toplu soruları ("tüm projelerin?") garanti eder.
  2. Sabitlenen kayıtlar — soruda (veya takip sorusunda önceki turda) adı geçen
                       proje/şirket/okul; embedding kalitesinden bağımsızdır.
  3. Hibrit arama   — anlamsal + BM25 (RRF), alaka eşiğinden geçenler.
Teknoloji soruları ("Flutter ile ne yaptın?") için deterministik teknoloji→kullanım
notları eklenir; bu sayede model kullanmadığım bir teknoloji için proje uyduramaz.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import date

from langchain_core.documents import Document

from .index import Hit, KnowledgeIndex, KnowledgeSnapshot
from .knowledge import Entity, TechUsage, describe_tech, match_entities, match_techs
from .textnorm import fold, tokens

logger = logging.getLogger(__name__)

_TR_MONTHS = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
              "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
_LANG_NAMES = {"tr": "Türkçe", "en": "English (İngilizce)"}
_TYPE_LABELS = {
    "about": "hakkımda", "skills": "beceriler", "project": "proje", "experience": "deneyim",
    "education": "eğitim", "certifications": "sertifikalar", "languages": "diller",
    "contact": "iletişim", "faq": "sık sorulan",
}

# ── Dil / niyet sezgileri (katlanmış token'lar üzerinde) ─────────────
_TR_CHARS = re.compile(r"[çğıöşüÇĞİÖŞÜ]")
_TR_HINTS = frozenset("""
ne neler nedir nelerdir nasil hangi hangisi neden nicin nerede nereden kim kimsin kac
mi mu misin musun miydi var yok sen senin sana seni ben benim bana biraz anlat hakkinda
peki ve ile bir bu icin degil olarak merhaba selam tesekkurler tesekkur sagol proje
projen projelerin projeler projesi deneyim deneyimin calistin yaptin kullandin okuyorsun
universite iletisim ulasabilirim evet hayir tamam naber nasilsin gibi daha cok su an suan
nerde nerdesin calisiyorsun calisiyosun napiyorsun yapiyosun biliyosun misiniz musunuz
""".split())
_EN_HINTS = frozenset("""
what which how why where who when tell about your you are is do does did have has the and
project projects experience can could would me please work worked hi hello thanks thank
yes describe explain list skills contact reach built build used use any of in with for
from to
""".split())
_SMALLTALK = frozenset("""
merhaba merhabalar selam selamlar slm mrb hey hi hello hola naber nasilsin nasilsiniz iyi
misin gunaydin aksamlar gunler geceler tesekkurler tesekkur ederim sagol sag ol eyvallah
thanks thank you thx gorusuruz bye goodbye hosca kal tamam super harika cok guzel great
cool nice how are ok okay bugra dostum kanka hos buldum memnun oldum to meet too
""".split())
_ANAPHORA = frozenset("""
bu bunu bunda bunun buna bundan o onu onda onun ona ondan orada orda orasi oradaki su sunu
peki ya ayni it its that this there they them those these also more detail details daha
detay detayli fazla
""".split())
# Çoğul gönderim ("bunlardan hangileri…?") → önceki cevaptaki tüm varlıklar taşınır
_PLURAL_ANAPHORA = frozenset("""
bunlar bunlardan bunlarin bunlari bunlarda onlar onlardan onlarin onlari onlarda hangileri
hangisi hangisinde these those them they
""".split())


# Niyeti belli soruları embedding'e bırakmadan ilgili kayda sabitler (katlanmış metinde aranır).
# (desen, kayıt anahtarı, istisna deseni) — "@current" = devam eden ilk deneyim kaydı.
_INTENT_PINS: list[tuple[re.Pattern, str, re.Pattern | None]] = [
    (re.compile(r"kendin(i|den|le)|kimsin|tanit|introduce|yourself|who are you|guclu yon|"
                r"strong|strength|neden seni|why should|why hire|ise almali|uzmanlik|expertise|"
                r"specializ|zayif yon|weakness"), "about", None),
    (re.compile(r"iletisim|ulasabil|ulasayim|sana ulas|size ulas|e-?posta|mail|linkedin|"
                r"telefon|numaran|phone|contact|reach you|sosyal medya|social media|youtube|"
                r"medium hesab|github hesab|github profil|github adres|your github"), "contact", None),
    (re.compile(r"\bdil(ler|leri|lerin|in|i)?\b|ingilizce|english level|languages? do you|"
                r"speak|yabanci dil"), "languages", re.compile(r"programla|programming|kodla|coding")),
    (re.compile(r"sertifika|certific|katilim belge"), "certifications", None),
    (re.compile(r"\bsu ?an\b|\bsimdi\b|halen|currently|current (job|role|position)|right now|"
                r"nerede calis|nerde calis|where do you work|where are you working"), "@current", None),
]


# Toplu sorular ("hangi projelerin var?", "which companies…") — cevabın tamamı profil özetinde;
# arama burada yalnızca alakasız "hub" kayıtlar (beceri listeleri vb.) getirir.
_AGG_QUANT = re.compile(r"\b(hangi|hangileri|neler|nelerdir|tum|tumu|butun|kac|toplam|nerelerde|"
                        r"list|all|which|what|how many|so far)\b")
_AGG_NOUN = re.compile(r"\b(proje|project|oyun|game|sirket|compan|deneyim|experience|rol|role|"
                       r"odul|award|derece|yarisma|competition|hackathon|calistin|worked)")


def is_aggregate(folded_query: str) -> bool:
    return bool(_AGG_QUANT.search(folded_query) and _AGG_NOUN.search(folded_query))


def intent_pins(folded_query: str) -> list[str]:
    keys = []
    for pattern, key, exclude in _INTENT_PINS:
        if pattern.search(folded_query) and not (exclude and exclude.search(folded_query)):
            keys.append(key)
    return keys


def detect_language(text: str, fallback: str = "tr") -> str:
    if _TR_CHARS.search(text):
        return "tr"
    toks = tokens(text, drop_stopwords=False)
    tr = sum(t in _TR_HINTS for t in toks)
    en = sum(t in _EN_HINTS for t in toks)
    if tr != en:
        return "tr" if tr > en else "en"
    return fallback if fallback in _LANG_NAMES else "tr"


def is_smalltalk(text: str) -> bool:
    toks = tokens(text, drop_stopwords=False)
    return 0 < len(toks) <= 6 and all(t in _SMALLTALK for t in toks)


def turkish_date(d: date) -> str:
    return f"{d.day} {_TR_MONTHS[d.month - 1]} {d.year}"


# ── Çıktı temizliği ──────────────────────────────────────────────────
_THINK_RE = re.compile(r"<think>.*?</think>", re.S | re.I)
_PHONE_RE = re.compile(r"(?:\+?90[\s.-]?)?\(?0?5\d{2}\)?[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}")


def clean_answer(text: str) -> str:
    """Frontend düz metin gösterdiği için Markdown ve <think> artıklarını temizler."""
    text = _THINK_RE.sub("", text or "")
    if re.search(r"<think>", text, re.I):          # kapanmamış düşünme bloğu
        text = re.split(r"<think>", text, flags=re.I)[0]
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s*", "", text)
    text = re.sub(r"(?m)^(\s*)[-*+]\s+", r"\1• ", text)
    text = re.sub(r"```[a-zA-Z]*\n?", "", text)
    text = re.sub(r"`([^`\n]+)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r"\1 (\2)", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)([^*\n]+?)(?<!\s)\*(?![\w*])", r"\1", text)
    text = _PHONE_RE.sub("[telefon numarası paylaşılmıyor]", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


# ── Veri yapıları ────────────────────────────────────────────────────
@dataclass
class PipelineSettings:
    system_prompt: str
    max_history_turns: int = 3
    max_search_records: int = 3       # aramadan gelen en fazla kayıt
    max_search_records_anchored: int = 2   # soru zaten sabitlenmiş kayıt içeriyorsa
    max_pinned_records: int = 4       # ada göre sabitlenen en fazla kayıt
    max_context_chars: int = 6000     # <detaylar> için yaklaşık karakter bütçesi
    dense_ood_threshold: float = 0.0  # en iyi anlamsal skor bunun altındaysa ve BM25 yoksa: alan dışı
    dense_margin: float = 1.0         # BM25 eşleşmesi olmayan aday en iyi skordan en fazla bu kadar düşük olabilir
    dense_margin_anchored: float = 0.05
    tech_pin_max_usages: int = 2      # teknolojiyi ≤ N proje kullanıyorsa o projeleri de sabitle
    max_source_cards: int = 4


@dataclass
class ContextRecord:
    doc: Document
    reason: str                       # "ad" | "takip" | "teknoloji" | "arama"
    hit: Hit | None = None

    @property
    def key(self) -> str:
        return self.doc.metadata["record_key"]


@dataclass
class PreparedTurn:
    query: str
    language: str
    smalltalk: bool
    followup: bool
    retrieval_query: str
    pinned: list[Entity]
    techs: list[TechUsage]
    records: list[ContextRecord]
    messages: list[dict]
    snapshot: KnowledgeSnapshot
    hits: list[Hit] = field(default_factory=list)
    aggregate: bool = False

    @property
    def record_keys(self) -> list[str]:
        return [r.key for r in self.records]


# ── Pipeline ─────────────────────────────────────────────────────────
class ChatPipeline:
    def __init__(self, index: KnowledgeIndex, settings: PipelineSettings, llm_chain=None):
        self.index = index
        self.s = settings
        self.llm_chain = llm_chain      # generate(messages) -> (text, model)

    # 1) Soru analizi + bağlam seçimi (LLM çağrısı yok; değerlendirmede tek başına kullanılır)
    def prepare(self, query: str, history: list[dict], ui_lang: str | None = None,
                today: date | None = None) -> PreparedTurn:
        snap = self.index.snapshot()
        query = query.strip()[:1000]
        history = [h for h in history if h.get("role") in ("user", "assistant")
                   and (h.get("content") or "").strip()]
        history = history[-(self.s.max_history_turns * 2):]

        language = detect_language(query, fallback=ui_lang or "tr")
        smalltalk = is_smalltalk(query)
        q_fold = fold(query)

        pinned = match_entities(q_fold, snap.entities)
        techs = [] if smalltalk else match_techs(q_fold, snap.tech_usage)
        intents = [] if smalltalk else intent_pins(q_fold)
        followup = False
        retrieval_query = query
        all_toks = set(tokens(query, drop_stopwords=False))
        plural = bool(all_toks & _PLURAL_ANAPHORA)
        aggregate = not (smalltalk or pinned or techs or plural) and is_aggregate(q_fold)

        # Takip sorusu: sorunun kendi çıpası (varlık/teknoloji/niyet/toplu soru) yoksa önceki
        # turdan taşı. Çıpası olan kısa soru ("Docker kullandın mı?") yeni konudur.
        if not (pinned or techs or intents or smalltalk or aggregate) and history:
            content_toks = tokens(query)
            if all_toks & (_ANAPHORA | _PLURAL_ANAPHORA) or len(content_toks) <= 4:
                prev_user = next((h["content"] for h in reversed(history) if h["role"] == "user"), "")
                prev_bot = next((h["content"] for h in reversed(history) if h["role"] == "assistant"), "")
                carried = match_entities(fold(prev_user), snap.entities)
                if not carried:
                    bot_entities = match_entities(fold(prev_bot), snap.entities)
                    if plural or len(bot_entities) <= 2:
                        carried = bot_entities
                if carried or prev_user:
                    followup = True
                    pinned = carried[: (self.s.max_pinned_records if plural else 2)]
                    retrieval_query = f"{prev_user}\n{query}".strip()

        records: list[ContextRecord] = []
        seen: set[str] = set()

        def add(doc: Document | None, reason: str, hit: Hit | None = None) -> None:
            if doc is not None and doc.metadata["record_key"] not in seen:
                seen.add(doc.metadata["record_key"])
                records.append(ContextRecord(doc, reason, hit))

        for ent in pinned[: self.s.max_pinned_records]:
            add(snap.by_key.get(ent.record_key), "takip" if followup else "ad")

        if not smalltalk:
            for key in intents:
                if key == "@current":
                    key = next((d.metadata["record_key"] for d in snap.docs
                                if d.metadata["source_type"] == "experience"
                                and "halen devam" in d.page_content), "")
                add(snap.by_key.get(key), "niyet")

        for tech in techs:
            if 0 < len(tech.projects) <= self.s.tech_pin_max_usages:
                for name in tech.projects:
                    add(snap.by_key.get(f"project:{name}"), "teknoloji")

        hits: list[Hit] = []
        if not (smalltalk or aggregate):
            hits = self.index.hybrid_search(retrieval_query, snap)
            anchored = bool(records)
            limit = self.s.max_search_records_anchored if anchored else self.s.max_search_records
            for hit in self._gate(hits, anchored):
                if sum(r.reason == "arama" for r in records) >= limit:
                    break
                add(hit.doc, "arama", hit)
            if not records:
                # Değerlendirme/genel sorularda ("neden seni seçelim?") en zengin özet kayıt
                add(snap.by_key.get("about"), "varsayılan")

        records = self._fit_budget(records)
        messages = self._build_messages(query, history, language, smalltalk, aggregate, techs,
                                        records, snap, today or date.today())
        return PreparedTurn(query, language, smalltalk, followup, retrieval_query, pinned,
                            techs, records, messages, snap, hits, aggregate)

    def _gate(self, hits: list[Hit], anchored: bool) -> list[Hit]:
        """Alaka kapısı: alan dışı sorularda hiç kayıt seçme, zayıf adayları ele.

        anchored: soru zaten ada/teknolojiye göre sabitlenmiş kayıt içeriyorsa
        arama yalnızca güçlü adaylarla tamamlar (gürültü bağlamı modeli dağıtır).
        """
        if not hits:
            return []
        top_dense = max(h.dense for h in hits)
        top_bm25 = max(h.bm25 for h in hits)
        if not anchored and top_bm25 <= 0 and top_dense < self.s.dense_ood_threshold:
            return []
        margin = self.s.dense_margin_anchored if anchored else self.s.dense_margin
        floor = top_dense - margin
        lexical_floor = top_bm25 * 0.25
        return [h for h in hits
                if (h.bm25_rank is not None and h.bm25 >= lexical_floor) or h.dense >= floor]

    def _fit_budget(self, records: list[ContextRecord]) -> list[ContextRecord]:
        kept, used = [], 0
        for r in records:
            size = len(r.doc.page_content)
            if kept and used + size > self.s.max_context_chars:
                continue
            kept.append(r)
            used += size
        return kept

    def _build_messages(self, query, history, language, smalltalk, aggregate, techs, records,
                        snap, today) -> list[dict]:
        blocks = []
        for i, r in enumerate(records, 1):
            m = r.doc.metadata
            blocks.append(f'<bilgi no="{i}" tür="{_TYPE_LABELS.get(m["source_type"], m["source_type"])}" '
                          f'başlık="{m.get("title", "")}">\n{r.doc.page_content}\n</bilgi>')
        if techs:
            blocks.append("<teknoloji_kullanımı>\n"
                          + "\n".join(describe_tech(t) for t in techs)
                          + "\n</teknoloji_kullanımı>")
        if aggregate:
            blocks.append("(Toplu bir soru: cevabı <profil>'deki ilgili listenin tamamından kur; "
                          "toplam sayıyı ve her öğeyi kısa bir somut detayla ver.)")
        if smalltalk:
            blocks.append("(Bu mesaj bir selamlaşma/nezaket ifadesi: kısa ve sıcak karşılık ver; "
                          "gerekiyorsa kendini tek cümleyle tanıt ve neler sorulabileceğini öner.)")
        elif not blocks:
            blocks.append("(Bu soruyla doğrudan eşleşen ek bilgi yok. Yalnızca <profil>'deki bilgileri "
                          "kullan; orada da yoksa bilmediğini dürüstçe söyle.)")

        system = self.s.system_prompt.format(
            today=turkish_date(today),
            answer_language=_LANG_NAMES.get(language, "Türkçe"),
            profile=snap.digest,
            details="\n\n".join(blocks),
        )
        messages = [{"role": "system", "content": system}]
        for h in history:
            limit = 900 if h["role"] == "assistant" else 500
            messages.append({"role": h["role"], "content": h["content"][:limit]})
        messages.append({"role": "user", "content": query})
        return messages

    # 2) Uçtan uca cevap
    def answer(self, query: str, history: list[dict], ui_lang: str | None = None) -> dict:
        prepared = self.prepare(query, history, ui_lang)
        raw, model = self.llm_chain.generate(prepared.messages)
        answer = clean_answer(raw)
        sources = self.sources_for(answer, prepared)
        if sources:
            stem = "bass"
        elif prepared.records:
            stem = "arp"
        else:
            stem = "pad"
        return {"answer": answer, "sources": sources, "stem_hint": stem,
                "model": model, "prepared": prepared}

    def sources_for(self, answer: str, prepared: PreparedTurn) -> list[dict]:
        """Kaynak kartları: cevapta adı geçen (veya soruda açıkça sorulan) projeler."""
        snap = prepared.snapshot
        keys = [e.record_key for e in match_entities(fold(answer), snap.entities)
                if e.kind == "project"]
        for ent in prepared.pinned:
            if ent.kind == "project" and ent.record_key not in keys:
                keys.append(ent.record_key)
        cards = []
        for key in keys[: self.s.max_source_cards]:
            meta = snap.by_key[key].metadata
            cards.append({
                "project_name": meta.get("project_name"),
                "source_type": "project",
                "github": meta.get("github") or None,
                "tags": [t.strip() for t in meta.get("tags", "").split(",") if t.strip()],
            })
        return cards


# ── LLM zinciri (birincil model + yedekler) ──────────────────────────
class GroqChain:
    """Sırayla modelleri dener: model kaldırılırsa (model_not_found), oran sınırına
    takılırsa (429) veya zaman aşımı olursa bir sonrakine geçer. Groq'ta oran
    sınırları model başınadır; yedek model bu yüzden gerçek bir B planıdır."""

    def __init__(self, api_key: str, models: list[str], temperature: float, max_tokens: int,
                 model_options: dict[str, dict] | None = None, timeout: float = 30.0):
        self.api_key = api_key
        self.models = [m for i, m in enumerate(models) if m and m not in models[:i]]
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.model_options = model_options or {}
        self.timeout = timeout
        self._clients: dict = {}

    def _client(self, model: str):
        if model not in self._clients:
            from langchain_groq import ChatGroq
            kwargs = dict(model=model, groq_api_key=self.api_key, temperature=self.temperature,
                          max_tokens=self.max_tokens, max_retries=1, timeout=self.timeout)
            kwargs.update(self.model_options.get(model, {}))   # model özel ayarlar öncelikli
            self._clients[model] = ChatGroq(**kwargs)
        return self._clients[model]

    def generate(self, messages: list[dict]) -> tuple[str, str]:
        last_exc: Exception | None = None
        for model in self.models:
            try:
                text = clean_answer(self._client(model).invoke(messages).content)
                if text:
                    return text, model
                last_exc = RuntimeError("boş cevap")
            except Exception as exc:  # noqa: BLE001 — bir sonraki modeli dene
                last_exc = exc
            # Kullanıcı içeriği loglanmaz; yalnızca model ve hata türü
            logger.error("LLM başarısız (%s): %s", model, type(last_exc).__name__)
            if type(last_exc).__name__ == "AuthenticationError":
                break   # geçersiz anahtar tüm modellerde aynı sonucu verir
        raise RuntimeError("Hiçbir LLM modeli cevap üretemedi") from last_exc
