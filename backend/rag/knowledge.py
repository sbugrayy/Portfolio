"""
knowledge.py — knowledge.json'u RAG'in kullandığı yapılara derler.

Üretilenler (hepsi aynı knowledge.json okumasından, birbiriyle tutarlı):
  • build_documents   → kayıt başına TEK doküman. Kayıtlar asla bölünmez, böylece
                        "Etiketler: … Başarı: …" gibi başlığını kaybetmiş parça oluşmaz.
                        Her dokümanın kararlı bir record_key'i vardır ("project:SFDDS").
  • build_profile_digest → her istekte sistem prompt'una giren kompakt özet. "Tüm
                        projelerin?", "nerelerde çalıştın?" gibi toplu soruları
                        retrieval'a bırakmadan eksiksiz cevaplatır.
  • build_entities    → proje/şirket/okul adları + aliases → soruda adı geçen kaydı
                        embedding kalitesinden bağımsız olarak bağlama sabitlemek için.
  • build_tech_usage  → teknoloji → onu kullandığım proje/roller ("Flutter ile ne yaptın?").
"""

import hashlib
import json
import re
from dataclasses import dataclass, field

from langchain_core.documents import Document

from .textnorm import contains_phrase, fold

SKILL_LABELS = {
    "yapay_zeka_ML": "Yapay Zeka / Makine Öğrenmesi",
    "backend": "Back-end",
    "bulut": "Bulut",
    "oyun_gelistirme": "Oyun Geliştirme",
    "masaustu_uygulamalar": "Masaüstü Uygulamalar",
    "web_gelistirme": "Web Geliştirme",
    "mobil": "Mobil",
    "haberlesme_sistemler": "Haberleşme ve Gömülü Sistemler",
    "veri_araclar": "Veri ve Geliştirici Araçları",
    "liderlik": "Liderlik",
}

_CURRENT_MARKERS = ("gunumuz", "devam", "present", "current", "halen", "hala")

# Etiketlerde geçen ama "teknoloji" sayılmaması gereken genel kelimeler
_GENERIC_TECH = {fold(t) for t in [
    "API", "Web", "Game", "2D", "3D", "Desktop", "Database", "Mobile", "Defense",
    "Portfolio", "Hackathon", "Rocket", "Weather", "Text Editor", "Adventure",
    "Pixel Art", "Game Jam", "Hyper Casual", "Quality Control", "Textile",
    "Medical Imaging", "Budget Optimization", "Mobile Health", "Telemetry",
    "TEKNOFEST", "Google Ads", "Digital Clone", "SQL", "LLM", "NLP",
    "GitHub",  # iletişim sorusu ("GitHub'ın ne?") teknoloji sorusu sanılmasın
]}


# ── Yardımcılar ──────────────────────────────────────────────────────
def load_knowledge(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def skill_label(key: str) -> str:
    return SKILL_LABELS.get(key, key.replace("_", " ").strip().title())


def is_current(date_text: str) -> bool:
    folded = fold(date_text or "")
    return any(marker in folded for marker in _CURRENT_MARKERS)


def project_key(p: dict) -> str:
    return f"project:{p['name']}"


def experience_key(e: dict) -> str:
    return f"experience:{e['company']}|{e['position']}"


def education_key(ed: dict) -> str:
    return f"education:{ed.get('school', '')}"


def _education_list(kb: dict) -> list[dict]:
    edu = kb.get("education")
    if isinstance(edu, list):
        return edu
    return [edu] if isinstance(edu, dict) and edu else []


def _short(text: str, limit: int = 110) -> str:
    """Özet satırı için kısaltır; yalnızca cümle ya da ' — ' sınırında keser
    (virgülde kesmek "X, Y ve Z sistemi" gibi ifadelerin anlamını bozar)."""
    text = (text or "").strip()
    for sep in (". ", " — "):
        idx = text.find(sep)
        if 0 < idx <= limit:
            text = text[:idx]
            break
    if len(text) > limit:
        text = text[: text.rfind(" ", 0, limit)].rstrip(".,;") + "…"
    return text.rstrip(".")


# ── 1. Dokümanlar ────────────────────────────────────────────────────
def build_documents(kb: dict) -> list[Document]:
    docs: list[Document] = []

    def add(key: str, source_type: str, title: str, lines: list[str], **extra) -> None:
        meta = {"record_key": key, "source_type": source_type, "title": title}
        # Chroma metadata'sı yalnızca str/int/float/bool kabul eder
        meta.update({k: v for k, v in extra.items() if v not in (None, "", [])})
        docs.append(Document(page_content="\n".join(l for l in lines if l), metadata=meta))

    if kb.get("about"):
        add("about", "about", "Hakkımda", ["Hakkımda (Buğra Yıldırım)", kb["about"]])

    for category, items in (kb.get("skills") or {}).items():
        label = skill_label(category)
        add(f"skills:{category}", "skills", f"Beceriler — {label}",
            [f"Becerilerim — {label}", ", ".join(items)])

    for p in kb.get("projects", []):
        add(project_key(p), "project", p["name"], [
            f"Proje: {p['name']}",
            f"Özet: {p.get('short_description', '')}",
            f"Detay: {p.get('long_description', '')}",
            f"Teknolojiler: {', '.join(p.get('stack', []))}" if p.get("stack") else "",
            f"Etiketler: {', '.join(p.get('tags', []))}" if p.get("tags") else "",
            f"Başarı / Ödül: {p['achievement']}" if p.get("achievement") else "",
            f"GitHub: {p['github']}" if p.get("github") else "",
            f"Canlı bağlantı: {p['url']}" if p.get("url") else "",
        ], project_name=p["name"], github=p.get("github", ""),
            tags=", ".join(p.get("tags", [])), url=p.get("url", ""))

    for e in kb.get("experience", []):
        status = " (halen devam ediyor)" if is_current(e.get("date", "")) else ""
        add(experience_key(e), "experience", f"{e['company']} — {e['position']}", [
            f"Deneyim: {e['company']} — {e['position']}",
            f"Tarih: {e.get('date', '')}{status}",
            f"Açıklama: {e.get('description', '')}",
        ], company=e.get("company", ""), position=e.get("position", ""))

    for ed in _education_list(kb):
        degree = ", ".join(x for x in (ed.get("degree"), ed.get("field")) if x)
        add(education_key(ed), "education", ed.get("school", "Eğitim"), [
            f"Eğitim: {ed.get('school', '')} — {degree}",
            f"Dönem: {ed.get('period', '')}",
            f"Açıklama: {ed.get('description', '')}",
        ])

    certs = kb.get("certifications", [])
    if certs:
        add("certifications", "certifications", "Sertifikalar",
            [f"Sertifikalarım ve katılım belgelerim ({len(certs)} adet):"]
            + [f"- {c}" for c in certs])

    langs = kb.get("languages", [])
    if langs:
        add("languages", "languages", "Diller",
            ["Konuştuğum diller (yabancı dil seviyem):"] + [f"- {l}" for l in langs])

    contact = kb.get("contact") or {}
    if contact:
        add("contact", "contact", "İletişim",
            ["İletişim bilgilerim ve sosyal medya hesaplarım:"]
            + [f"- {_CONTACT_LABELS.get(k, k.title())}: {v}" for k, v in contact.items() if v])

    for i, item in enumerate(kb.get("faq", []) or []):
        if item.get("q") and item.get("a"):
            add(f"faq:{i}", "faq", item["q"], [f"Soru: {item['q']}", f"Cevabım: {item['a']}"])

    return docs


_CONTACT_LABELS = {
    "email": "E-posta", "linkedin": "LinkedIn", "github": "GitHub",
    "medium": "Medium", "youtube": "YouTube", "website": "Web sitesi",
}


def documents_fingerprint(docs: list[Document], embedding_model: str) -> str:
    """Doküman içeriği + metadata + embedding modeli → kararlı hash.

    Builder mantığı veya knowledge.json değişirse hash değişir ve indeks
    otomatik yeniden kurulur (eski indeksle cevap verme hatası bir daha olmaz).
    """
    payload = json.dumps(
        {"model": embedding_model,
         "docs": [[d.page_content, sorted(d.metadata.items())] for d in docs]},
        ensure_ascii=False, sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


# ── 2. Profil özeti (her istekte prompt'ta) ──────────────────────────
_KNOWN_LANGUAGES = ["Python", "C#", "C++", "Java", "JavaScript", "TypeScript", "Dart", "SQL",
                    "Kotlin", "Swift", "Go", "Rust", "PHP", "C"]


def _programming_languages(kb: dict) -> list[str]:
    """Beceri ve proje teknolojilerinde geçen programlama dilleri ("Arduino (C++)" → C++)."""
    terms = [t for items in (kb.get("skills") or {}).values() for t in items]
    terms += [t for p in kb.get("projects", []) for t in p.get("stack", [])]
    found = []
    for lang in _KNOWN_LANGUAGES:
        pattern = re.compile(r"(?<![\w+#])" + re.escape(lang) + r"(?![\w+#])")
        if any(pattern.search(t) for t in terms) and lang not in found:
            found.append(lang)
    return found

def build_profile_digest(kb: dict) -> str:
    lines: list[str] = ["Ad: Buğra Yıldırım"]

    edu = _education_list(kb)
    if edu:
        lines.append("Eğitim: " + "; ".join(
            f"{ed.get('school', '')} — {', '.join(x for x in (ed.get('degree'), ed.get('field')) if x)}"
            f" ({ed.get('period', '')})" for ed in edu))
        gpa = re.search(r"GANO[^0-9]*([0-9][.,][0-9]+\s*/\s*[0-9][.,][0-9]+)", json.dumps(edu, ensure_ascii=False))
        if gpa:
            lines.append(f"GANO: {gpa.group(1)}")

    exps = kb.get("experience", [])
    current = [e for e in exps if is_current(e.get("date", ""))]
    past = [e for e in exps if not is_current(e.get("date", ""))]
    fmt = lambda e: f"{e['company']} — {e['position']} ({e.get('date', '')})"
    if current:
        lines.append("Şu anki rollerim: " + "; ".join(fmt(e) for e in current))
    if past:
        lines.append("Önceki deneyimlerim: " + "; ".join(fmt(e) for e in past))

    projects = kb.get("projects", [])
    if projects:
        lines.append(f"Projelerim ({len(projects)} adet):")
        for p in projects:
            extra = f" [{p['achievement']}]" if p.get("achievement") else ""
            lines.append(f"- {p['name']}: {_short(p.get('short_description', ''))}{extra}")

    awards = [f"{p['achievement']} ({p['name']})" for p in projects
              if p.get("achievement") and re.search(r"\d\.|finalist|ödül|birinci|ikinci|üçüncü",
                                                    p["achievement"], re.I)]
    if awards:
        lines.append("Yarışma dereceleri: " + "; ".join(awards))

    skills = kb.get("skills") or {}
    langs = _programming_languages(kb)
    if langs:
        lines.append("Programlama dilleri: " + ", ".join(langs))
    if skills:
        lines.append("Beceri alanlarım: " + "; ".join(
            f"{skill_label(cat)}: {', '.join(items[:5])}{' …' if len(items) > 5 else ''}"
            for cat, items in skills.items()))

    if kb.get("languages"):
        lines.append("Diller: " + "; ".join(kb["languages"]))

    certs = kb.get("certifications", [])
    if certs:
        lines.append(f"Sertifikalar: {len(certs)} adet (ör. {', '.join(certs[:4])})")

    contact = kb.get("contact") or {}
    if contact:
        lines.append("İletişim: " + "; ".join(
            f"{_CONTACT_LABELS.get(k, k.title())} {v}" for k, v in contact.items() if v))

    return "\n".join(lines)


# ── 3. Varlıklar (ada göre kayıt sabitleme) ──────────────────────────
@dataclass
class Entity:
    record_key: str
    kind: str                       # project | experience | education
    title: str
    names: list[str] = field(default_factory=list)   # katlanmış eşleme ifadeleri

    def first_match(self, folded_text: str) -> int:
        """Metinde ilk geçtiği konum (yoksa -1)."""
        best = -1
        for name in self.names:
            if contains_phrase(folded_text, name):
                pos = folded_text.find(name)
                best = pos if best < 0 else min(best, pos)
        return best


def _name_variants(name: str) -> list[str]:
    """'Cats Bilişim (Cats Software Development)' → tam ad + parantez dışı + parantez içi."""
    variants = [name]
    inner = re.findall(r"\(([^)]+)\)", name)
    outer = re.sub(r"\s*\([^)]*\)\s*", " ", name).strip()
    if inner:
        variants.append(outer)
        variants.extend(inner)
    return variants


def build_entities(kb: dict) -> list[Entity]:
    entities: list[Entity] = []

    def make(key: str, kind: str, title: str, raw_names: list[str]) -> None:
        names = []
        for raw in raw_names:
            f = fold(raw).strip()
            if len(f) >= 2 and f not in names:
                names.append(f)
        entities.append(Entity(key, kind, title, names))

    for p in kb.get("projects", []):
        make(project_key(p), "project", p["name"], [p["name"], *p.get("aliases", [])])
    for e in kb.get("experience", []):
        make(experience_key(e), "experience", f"{e['company']} — {e['position']}",
             [*_name_variants(e["company"]), *e.get("aliases", [])])
    for ed in _education_list(kb):
        make(education_key(ed), "education", ed.get("school", ""),
             [ed.get("school", ""), *ed.get("aliases", [])])
    return entities


def match_entities(folded_text: str, entities: list[Entity]) -> list[Entity]:
    """Metinde adı geçen varlıklar, metindeki geçiş sırasına göre."""
    found = [(pos, ent) for ent in entities if (pos := ent.first_match(folded_text)) >= 0]
    return [ent for _, ent in sorted(found, key=lambda x: x[0])]


# ── 4. Teknoloji → kullanım haritası ─────────────────────────────────
@dataclass
class TechUsage:
    name: str                                   # gösterim adı (ilk görülen yazım)
    projects: list[str] = field(default_factory=list)      # proje adları
    roles: list[str] = field(default_factory=list)         # "Şirket — Pozisyon"
    skill_areas: list[str] = field(default_factory=list)   # beceri kategorisi etiketleri


def build_tech_usage(kb: dict) -> dict[str, TechUsage]:
    usage: dict[str, TechUsage] = {}

    def get(term: str) -> TechUsage | None:
        key = fold(term).strip()
        if len(key) < 2 or key in _GENERIC_TECH:
            return None
        if key not in usage:
            usage[key] = TechUsage(name=term)
        return usage[key]

    for p in kb.get("projects", []):
        for term in [*p.get("stack", []), *p.get("tags", [])]:
            if (u := get(term)) and p["name"] not in u.projects:
                u.projects.append(p["name"])
    for cat, items in (kb.get("skills") or {}).items():
        for term in items:
            if (u := get(term)) and skill_label(cat) not in u.skill_areas:
                u.skill_areas.append(skill_label(cat))

    # Deneyim açıklamalarında geçen teknolojiler (ör. Cats Bilişim → Flutter, JWT)
    for e in kb.get("experience", []):
        folded_desc = fold(f"{e.get('position', '')} {e.get('description', '')}")
        role = f"{e['company']} — {e['position']}"
        for key, u in usage.items():
            if contains_phrase(folded_desc, key) and role not in u.roles:
                u.roles.append(role)
    return usage


def match_techs(folded_text: str, usage: dict[str, TechUsage], limit: int = 3) -> list[TechUsage]:
    found = [(folded_text.find(key), len(key), u) for key, u in usage.items()
             if contains_phrase(folded_text, key)]
    # Uzun eşleşme kısa olanı kapsıyorsa (ör. "yolov11" ⊃ "yolo") ikisini de tut; sıraya göre dön
    found.sort(key=lambda x: (x[0], -x[1]))
    seen: list[TechUsage] = []
    for _, _, u in found:
        if u not in seen:
            seen.append(u)
    return seen[:limit]


def describe_tech(u: TechUsage) -> str:
    parts = []
    if u.projects:
        parts.append(f"kullandığım projeler: {', '.join(u.projects)}")
    if u.roles:
        parts.append(f"kullandığım roller: {'; '.join(u.roles)}")
    if u.skill_areas:
        parts.append(f"beceri listemde: {', '.join(u.skill_areas)}")
    if not u.projects and not u.roles:
        parts.append("bu teknolojiyle yaptığım belirli bir proje/iş detayı paylaşılmamış")
    return f"{u.name} → " + "; ".join(parts)
