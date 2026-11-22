r"""
🧪 test_master.py — MASTER SYSTEM TEST BATTERY (sab kuch ek hi jagah)

Kya kya check hota hai (nahee ho to FAIL report):
  1. 🛡️ net_guard firewall: AI-API block, Qadiani-site block, local-AI block,
     whitelist allow, unknown-host deny (deny-by-default)
  2. 📚 7 Sahih hadith corpus files maujood + counts hadith_master.json se match
  3. 🕌 Qadiani/forbidden words scan: quran translations (308) + hadith jsons
     + corpus_big + masters — HITS = 0 hona chahiye
  4. 🪄 Template-check: chat jawab me koi canned opener NAHI
  5. 💬 Chat smoke: "salam", "Allah kahan hai" (Islamic → books/yaad se cited),
     "photosynthesis kya hai" (live-research path), qadiani sawal → internet NAHI
  6. 💓 hub heartbeat (subsystems sab OK?)

Run:
  python scripts\test_master.py            # sab tests
  python scripts\test_master.py --quick    # scan chhote (corpus-only)
"""
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from harvest import net_guard            # noqa: E402
from harvest.source_policy import (      # noqa: E402
    FORBIDDEN_RX, scan_files, text_forbidden)
from core import hub                     # noqa: E402
from model import generate               # noqa: E402

BIG = os.path.join(ROOT, "data", "corpus_big")
MASTER = os.path.join(ROOT, "data", "hadith_master.json")

BOOKS = ["bukhari", "muslim", "malik", "abudawud", "tirmidhi", "nasai",
         "ibnmajah"]

# ❌ purane canned openers — in ka jawab me hona FORAN MANA (template qanoon)
_TEMPLATE_RX = re.compile(
    r"(?i)achha sawal!|meri yaad se:|main aise samajhta hoon:"
    r"|dekho, mere ilm me hai:|mere dimagh ka note:|sochne par aisa aata hai:"
    r"|mere library ka ilm kehta hai:")

R = []          # (naam, ok, note)


def rec(name, ok, note=""):
    R.append((name, bool(ok), note))
    print("%s %-46s %s" % ("✅" if ok else "❌", name, note), flush=True)


# ----------------------------------------------------------------------
def t_net_guard():
    tests = [
        ("https://raw.githubusercontent.com/fawazahmed0/hadith-api/1/eng.json",
         True, "whitelist allow"),
        ("https://api.openai.com/v1/chat/completions",
         False, "AI-model API block"),
        ("https://alislam.org/quran", False, "qadiani site block"),
        ("https://api.aaiil.org/text", False, "aaiil (qadiani) block"),
        ("https://islamqa.info/en/answers/1", True, "islamqa allow"),
        ("https://najmalilm.example.com/a", False, "unknown host deny"),
        ("http://127.0.0.1:11434/api/tags", False, "local AI (ollama) block"),
    ]
    for url, want, label in tests:
        ok, why = net_guard.check(url)
        rec("firewall: %s" % label, ok == want, "-> %s" % why)
    rec("firewall: guard install ho saka",
        net_guard.install(), "urlopen guarded")


def t_sahih_corpus():
    try:
        with open(MASTER, encoding="utf-8") as f:
            so = json.load(f).get("sahih_only", {})
    except Exception as e:
        rec("sahih master json parha", False, str(e))
        return
    total = 0
    for b in BOOKS:
        p = os.path.join(BIG, "hadith_%s_english_sahih.txt" % b)
        if not os.path.exists(p):
            rec("sahih corpus file: %s" % b, False, "file nahi")
            continue
        kept = so.get(b, {}).get("kept", 0)
        with open(p, encoding="utf-8", errors="ignore") as f:
            n_sawal = sum(1 for ln in f if ln.startswith("Sawal:"))
        total += n_sawal
        rec("sahih corpus: %-9s" % b, n_sawal >= kept * 0.9,
            "file=%d master=%d" % (n_sawal, kept))
    rec("sahih corpus total", total >= 28000, "%d hadith (zaeef drop=%d)" % (
        total, sum(c.get("dropped", 0) for c in so.values())))


def t_forbidden_scan(quick=False):
    zones = [
        ("data/corpus_big", os.path.join(ROOT, "data", "corpus_big"), ".txt"),
        ("knowledge/hadith", os.path.join(ROOT, "knowledge", "hadith"),
         ".json"),
    ]
    if not quick:
        zones.append(("quran/translations",
                      os.path.join(ROOT, "knowledge", "quran", "translations"),
                      ".json"))
    for zname, folder, ext in zones:
        rep = scan_files(folder, ext)
        rec("qadiani-scan: %s (%d files)" % (zname, rep["scanned"]),
            not rep["hits"], ("HITS: %s" % rep["hits"]) if rep["hits"]
            else "0 forbidden")
    # data masters bhi
    hits = {}
    for fn in ("data/quran_master.json", "data/bukhari_master.json",
               "data/hadith_master.json", "data/model_card.json"):
        p = os.path.join(ROOT, fn)
        if os.path.exists(p):
            with open(p, encoding="utf-8", errors="ignore") as f:
                m = text_forbidden(f.read())
            if m:
                hits[fn] = m.group(0)
    rec("qadiani-scan: data masters", not hits,
        ("HITS: %s" % hits) if hits else "0 forbidden")


def t_chat_smoke():
    # (a) template-free mojudgi check
    rec("template: _OPENERS hata diya",
        not hasattr(generate, "_OPENERS"), "generate.py me nahi hai")

    out1, m1 = generate.chat_once("salam", meta=True)
    rec("chat: 'salam' jawab diya", bool(out1), m1.get("source", "?"))
    rec("chat: 'salam' template-free", not _TEMPLATE_RX.search(out1 or ""))

    out2, m2 = generate.chat_once("Allah kahan hai", meta=True)
    src2 = m2.get("source", "?")
    rec("chat: 'Allah kahan hai' (Islamic)", bool(out2),
        "source=%s | %s" % (src2, (out2 or "")[:70]))
    rec("chat: Islamic jawab yaad/books se (live nahi)",
        src2 != "live-research", "sacred sawal sirf books se")

    out3, m3 = generate.chat_once("photosynthesis kya hai", meta=True)
    src3 = m3.get("source", "?")
    rec("chat: gair-Islamic sawal research path", bool(out3),
        "source=%s | %s" % (src3, (out3 or "")[:70]))

    is_sacred_q = _is_sacred_true("mirza ghulam kaun tha")
    rec("chat: qadiani sawal bhi books-guard me", is_sacred_q,
        "internet NAHI — verify hi hoga")

    out4, m4 = generate.chat_once("hadith batao", meta=True)
    src4 = m4.get("source", "?")
    fab4 = generate._FAB_RX.search(out4 or "")
    if src4 == "khud-soch":
        rec("chat: 'hadith batao' khud-soch me NAKLI citation NAHI",
            not fab4, ("gali-mila: %s" % fab4.group(0)) if fab4
            else (out4 or "")[:60])
    else:
        rec("chat: 'hadith batao' yaad (asli kitab copy) se", bool(out4),
            "source=%s" % src4)


def _is_sacred_true(prompt):
    try:
        from model.live_research import is_sacred
        return is_sacred(prompt)
    except Exception:
        return False


def t_hub():
    try:
        hb = hub.heartbeat_check()
        bad = [k for k, v in hb.items() if not v]
        rec("hub heartbeat", not bad,
            "sab OK" if not bad else "fail: %s" % bad)
        st = hub.status()
        ng = st.get("net_guard", {})
        hs = st.get("hadith_sahih_only", {})
        rec("hub: net_guard + sahih report dikhta hai",
            "mode" in ng and "total_kept" in hs,
            "kept=%s" % hs.get("total_kept", "?"))
    except Exception as e:
        rec("hub heartbeat", False, str(e))


def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    print("=" * 64, flush=True)
    print("🧪 HMHS MASTER TEST BATTERY", flush=True)
    print("=" * 64, flush=True)
    t_net_guard()
    t_sahih_corpus()
    t_forbidden_scan(quick=quick)
    t_chat_smoke()
    t_hub()
    fails = [n for n, ok, _ in R if not ok]
    print("=" * 64, flush=True)
    print("🏁 %d/%d PASS%s | %.1fs" % (
        len(R) - len(fails), len(R),
        (" | FAIL: %s" % ", ".join(fails)) if fails else "",
        time.time() - t0), flush=True)
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
