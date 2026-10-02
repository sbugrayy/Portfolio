"""
run_eval.py — BUĞRA.AI regresyon değerlendirmesi.

knowledge.json'u, prompt'u veya retrieval ayarlarını değiştirdikten sonra çalıştır:

    python eval/run_eval.py                    # retrieval (çevrimdışı, ücretsiz, ~10 sn)
    python eval/run_eval.py --e2e              # + gerçek LLM cevapları ve kural kontrolleri
    python eval/run_eval.py --e2e --only proj  # yalnızca id'si/kategorisi 'proj' içerenler
    python eval/run_eval.py --e2e --delay 3    # istekler arası bekleme (oran sınırı için)

Altın set (eval/golden_set.json) şeması:
    {"id", "category", "lang": "tr"|"en", "history": [{"role","content"}], "query",
     "gold_records": ["project:SFDDS", ...],          # bağlamda olması beklenen kayıtlar
     "must_include_any": [["SFDDS"], ["YOLOv7","YOLOv11"]],  # her grup: en az biri geçmeli
     "must_not_include": ["KOSTÜ"]}                   # hiçbiri geçmemeli
"""

import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict

BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BACKEND)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from rag.textnorm import fold, tokens  # noqa: E402

GOLDEN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "golden_set.json")

# Kullanıcıya sızmaması gereken iç terimler (katlanmış hâlde aranır)
LEAK_PATTERNS = [
    "baglamda", "baglama gore", "baglamdaki", "verilen bilgi", "bana verilen", "profilimde",
    "profil ozet", "detaylarda", "<bilgi", "<profil", "<detay", "sistem talimat",
    "in the context", "provided context", "according to the context", "system prompt",
]
_MARKDOWN_RE = re.compile(r"\*\*|__|^#{1,6}\s|```|^\s*[-*]\s", re.M)
_PHONE_RE = re.compile(r"(?:\+?90[\s.-]?)?\(?0?5\d{2}\)?[\s.-]?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}")
_TR_WORDS = set("ve bir bu icin ile olarak ben benim de da mi gibi cok daha olan oldu yaptim "
                "gelistirdim projem projelerim kullandim var yok ama hem sonra".split())
_EN_WORDS = set("the and a an is are was were i my me with for of to in on it that this "
                "have has built developed used project projects which also".split())


def answer_language(text: str) -> str:
    toks = tokens(text, drop_stopwords=False)
    tr = sum(t in _TR_WORDS for t in toks)
    en = sum(t in _EN_WORDS for t in toks)
    return "en" if en > tr else "tr"


def build_pipeline(with_llm: bool):
    import logging
    import warnings
    warnings.filterwarnings("ignore")
    logging.disable(logging.WARNING)
    import config as C
    from rag.embeddings import SentenceTransformerEmbeddings
    from rag.index import KnowledgeIndex
    from rag.pipeline import ChatPipeline, GroqChain, PipelineSettings

    index = KnowledgeIndex(C.KNOWLEDGE_JSON_PATH, C.CHROMA_PERSIST_DIR, C.CHROMA_COLLECTION_NAME,
                           SentenceTransformerEmbeddings(C.LOCAL_EMBEDDING_MODEL),
                           C.LOCAL_EMBEDDING_MODEL)
    chain = None
    if with_llm:
        chain = GroqChain(C.GROQ_API_KEY, [C.CHAT_MODEL, *C.CHAT_MODEL_FALLBACKS],
                          C.LLM_TEMPERATURE, C.LLM_MAX_TOKENS, C.LLM_MODEL_OPTIONS)
    settings = PipelineSettings(
        system_prompt=C.SYSTEM_PROMPT, max_history_turns=C.MAX_HISTORY_TURNS,
        max_search_records=C.MAX_SEARCH_RECORDS, max_pinned_records=C.MAX_PINNED_RECORDS,
        dense_ood_threshold=C.DENSE_OOD_THRESHOLD, dense_margin=C.DENSE_MARGIN,
    )
    return ChatPipeline(index, settings, chain)


_NUMBER_RE = re.compile(r"\d+(?:[.,]\d+)?")


def unsupported_numbers(answer: str, messages: list[dict]) -> list[str]:
    """Cevaptaki iki+ haneli/ondalıklı sayılardan modele verilen metinde geçmeyenler
    (uydurma metrik/tarih sinyali: '%95 doğruluk', '2019'da başladım')."""
    source = " ".join(m["content"] for m in messages)
    found = []
    for num in _NUMBER_RE.findall(answer):
        if (len(num) >= 2 or "." in num or "," in num) and num not in source \
                and num.replace(",", ".") not in source and num not in found:
            found.append(num)
    return found


def check_answer(case: dict, answer: str, messages: list[dict] | None = None) -> list[str]:
    """Kural tabanlı kontroller; boş liste = geçti."""
    problems = []
    if messages:
        bad_numbers = unsupported_numbers(answer, messages)
        if bad_numbers:
            problems.append(f"kaynakta olmayan sayı: {', '.join(bad_numbers)}")
    f_answer = fold(answer)
    for group in case.get("must_include_any", []):
        if not any(fold(alt) in f_answer for alt in group):
            problems.append(f"eksik: {' | '.join(group)}")
    for bad in case.get("must_not_include", []):
        if fold(bad) in f_answer:
            problems.append(f"yasak ifade: {bad}")
    for leak in LEAK_PATTERNS:
        if leak in f_answer:
            problems.append(f"iç terim sızıntısı: {leak}")
    if _MARKDOWN_RE.search(answer):
        problems.append("markdown")
    if "<think" in answer.lower():
        problems.append("think etiketi")
    if _PHONE_RE.search(answer):
        problems.append("telefon numarası")
    if case.get("lang") in ("tr", "en") and len(answer) > 40 and answer_language(answer) != case["lang"]:
        problems.append(f"dil: beklenen {case['lang']}")
    return problems


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--e2e", action="store_true", help="LLM ile uçtan uca çalıştır")
    ap.add_argument("--only", default="", help="id/kategori filtresi (alt dize)")
    ap.add_argument("--delay", type=float, default=2.0, help="LLM istekleri arası bekleme (sn)")
    ap.add_argument("--golden", default=GOLDEN_PATH)
    ap.add_argument("--out", default="", help="Cevapların yazılacağı JSONL (varsayılan: eval/last_run.jsonl)")
    args = ap.parse_args()

    with open(args.golden, encoding="utf-8") as f:
        cases = json.load(f)
    if args.only:
        cases = [c for c in cases if args.only in c["id"] or args.only in c.get("category", "")]

    pipe = build_pipeline(with_llm=args.e2e)
    out_path = args.out or os.path.join(os.path.dirname(os.path.abspath(__file__)), "last_run.jsonl")
    out = open(out_path, "w", encoding="utf-8")

    by_cat = defaultdict(lambda: {"n": 0, "hit": 0, "digest": 0, "recall": 0.0, "e2e_n": 0, "e2e_pass": 0})
    failures = []
    for i, case in enumerate(cases):
        prepared = pipe.prepare(case["query"], case.get("history", []), case.get("lang"))
        ctx = set(prepared.record_keys)
        gold = case.get("gold_records", [])
        stats = by_cat[case.get("category", "?")]
        row = {"id": case["id"], "query": case["query"], "context": prepared.record_keys}
        if gold:
            stats["n"] += 1
            found = [g for g in gold if g in ctx]
            # Toplu sorularda kaynak, her istekte prompt'ta olan profil özetidir (tüm projeler/roller)
            via_digest = prepared.aggregate and not found
            stats["hit"] += bool(found) or via_digest
            stats["digest"] += via_digest
            stats["recall"] += 1.0 if via_digest else len(found) / len(gold)
            row["retrieval_hit"] = bool(found) or via_digest
            row["via_digest"] = via_digest

        if args.e2e:
            if i:
                time.sleep(args.delay)
            messages = []
            try:
                result = pipe.answer(case["query"], case.get("history", []), case.get("lang"))
                answer, model = result["answer"], result["model"]
                messages = result["prepared"].messages
                row["sources"] = [s["project_name"] for s in result["sources"]]
            except Exception as exc:  # noqa: BLE001
                answer, model = "", f"HATA: {type(exc).__name__}: {exc}"
            problems = check_answer(case, answer, messages) if answer else ["cevap yok"]
            stats["e2e_n"] += 1
            stats["e2e_pass"] += not problems
            row.update(answer=answer, model=model, problems=problems)
            if problems:
                failures.append((case["id"], case["query"], problems, answer))
            mark = "✓" if not problems else "✗"
            print(f"{mark} {case['id']}: {case['query'][:60]}" + ("" if not problems else f"  → {problems}"))
        out.write(json.dumps(row, ensure_ascii=False) + "\n")
    out.close()

    line = "--------------------+---------------+-----------+--------+----------"
    print("\nKategori            | retrieval hit | (özetten) | recall | e2e geçti")
    print(line)
    tot = {"n": 0, "hit": 0, "digest": 0, "recall": 0.0, "e2e_n": 0, "e2e_pass": 0}
    for cat, s in sorted(by_cat.items()):
        for k in tot:
            tot[k] += s[k]
        hit = f"{s['hit']}/{s['n']}" if s["n"] else "-"
        rec = f"{s['recall'] / s['n']:.2f}" if s["n"] else "-"
        e2e = f"{s['e2e_pass']}/{s['e2e_n']}" if s["e2e_n"] else "-"
        print(f"{cat[:20]:<20}| {hit:>13} | {s['digest'] or '':>9} | {rec:>6} | {e2e:>8}")
    print(line)
    hit = f"{tot['hit']}/{tot['n']}" if tot["n"] else "-"
    rec = f"{tot['recall'] / tot['n']:.2f}" if tot["n"] else "-"
    e2e = f"{tot['e2e_pass']}/{tot['e2e_n']}" if tot["e2e_n"] else "-"
    print(f"{'TOPLAM':<20}| {hit:>13} | {tot['digest'] or '':>9} | {rec:>6} | {e2e:>8}")

    if failures:
        print(f"\nBaşarısız {len(failures)} vaka (cevaplar: {out_path}):")
        for cid, q, probs, ans in failures:
            print(f"\n✗ {cid}: {q}\n  sorunlar: {probs}\n  cevap: {ans[:300]}")


if __name__ == "__main__":
    main()
