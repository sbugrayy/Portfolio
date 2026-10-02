"""
textnorm.py — Türkçe'ye duyarlı metin normalizasyonu.

BM25, varlık eşleme ve dil tespiti aynı normalizasyonu kullanır; böylece
"Sağlıkla", "SAĞLIKLA" ve "saglikla" aynı token'a düşer.

Dikkat: Python'da "İ".lower() → "i̇" (i + birleşik nokta) ve "I".lower() → "i"
(Türkçe'de "ı" olmalı). Bu yüzden küçük harfe çevirmeden ÖNCE Türkçe büyük
harfler elle eşlenir.
"""

import re
import unicodedata

_TR_UPPER = str.maketrans({"İ": "i", "I": "ı"})
_ASCII_FOLD = str.maketrans({
    "ı": "i", "ş": "s", "ğ": "g", "ç": "c", "ö": "o", "ü": "u",
    "â": "a", "î": "i", "û": "u",
})

# c#, c++, .net, node.js, yolov11, phi-4-mini gibi teknik terimleri korur
_TOKEN_RE = re.compile(r"[a-z0-9]+[#+]*")

STOPWORDS = frozenset("""
ve veya ile ya da de ki mi mu bu su o bir biraz icin gibi kadar daha en cok az ise
ne neler nedir nasil hangi hangisi neden nicin nerede kim kimin kac
var yok mi misin musun miydi oldu olan olarak olur
sen senin sana seni ben benim bana beni biz bizim siz
peki acaba hakkinda anlat anlatir anlatabilir misin soyle soyler bahset
the a an and or of to in on at for with by from as about into
is are was were be been being do does did have has had can could would should will
you your yours i me my we our it its this that these those there
what which who whom whose how why where when tell please
""".split())


def fold(text: str) -> str:
    """Türkçe doğru küçük harf + ASCII katlama: 'İKA Kontrol' → 'ika kontrol'."""
    text = text.translate(_TR_UPPER).lower().translate(_ASCII_FOLD)
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def tokens(text: str, drop_stopwords: bool = True) -> list[str]:
    """Katlanmış token listesi (stopword'ler opsiyonel olarak çıkarılır)."""
    toks = _TOKEN_RE.findall(fold(text))
    if drop_stopwords:
        toks = [t for t in toks if t not in STOPWORDS]
    return toks


def stem(token: str, prefix_len: int = 5) -> str:
    """Eklemeli Türkçe için kaba kök: ilk N karakter ('projelerin' → 'proje')."""
    return token if len(token) <= prefix_len or token[-1].isdigit() else token[:prefix_len]


# Kesme işaretinden sonra kalan ek parçaları ("Microsoft'ta" → "ta")
_SUFFIX_FRAGMENTS = frozenset(
    "ta te da de dan den tan ten in un nin nun yi yu ye ya na ne ni nu la le yla yle "
    "nda nde ndan nden ki li lu lik luk dir dur tir tur".split()
)
# Neredeyse her kayıtta geçen / her soruda sorulan kelimelerin kökleri. BM25'te
# gürültüden başka bir şey üretmezler ("deneyimin var mı?" → en kısa deneyim
# kaydı 1. sıraya çıkar); bu niyetleri anlamsal arama ve profil özeti karşılar.
_GENERIC_STEMS = frozenset(
    "proje deney exper calis yapti yapiy yapar yapab yapmi kulla used using work worke "
    "tekno techn hakki anlat nedir neler biliy bilgi olara".split()
)
# Doküman satır başı etiketleri ("Proje: ", "Teknolojiler: ") BM25'e girmez
_LABEL_RE = re.compile(r"(?m)^[^\n:]{2,40}:\s")


def bm25_terms(text: str, is_document: bool = False) -> list[str]:
    """BM25 terimleri: tam token + (farklıysa) önek kökü; ek parçaları ve jenerik kökler hariç."""
    if is_document:
        text = _LABEL_RE.sub("", text)
    out: list[str] = []
    for tok in tokens(text):
        if (len(tok) < 2 and not tok.isdigit()) or tok in _SUFFIX_FRAGMENTS:
            continue
        st = stem(tok)
        if st in _GENERIC_STEMS or tok in _GENERIC_STEMS:
            continue
        out.append(tok)
        if st != tok:
            out.append("~" + st)
    return out


def contains_phrase(folded_text: str, folded_phrase: str) -> bool:
    """Katlanmış metinde kelime başından başlayan ifade araması.

    5+ karakterlik ifadelerde ek almış hâller de eşleşir ('sfddsde', 'misyada');
    kısa ifadeler ('mri', 'hsd') yanlış pozitif olmasın diye tam kelime ister.
    """
    if not folded_phrase:
        return False
    tail = "" if len(folded_phrase) >= 5 else r"(?![a-z0-9])"
    pattern = r"(?<![a-z0-9])" + re.escape(folded_phrase) + tail
    return re.search(pattern, folded_text) is not None
