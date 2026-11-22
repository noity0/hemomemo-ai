"""
🌐 LIVE KNOWLEDGE HARVEST — Hemomemo AI

Kya karta hai:
   LAGATAR (LIVE MODE) sahi Islamic knowledge internet se PARHTA hai
   (browser jaisa page-kholna — koi API nahi, koi AI-model service nahi,
    koi Ollama nahi) aur machine ki yaad (data/corpus_big/harvest_*.txt)
   me likhta jata hai.

Sakht qawaid:
  - sirf READ: pages khole jate hain, kuch bhi kahin push/POST nahi
  - net_guard firewall: whitelist-only; AI-model APIs + Qadiani/Ahmadi
    sites HARD-BLOCK (harvest/net_guard.log me har block sabit)
  - FAITH-GUARD: qadiyani/ahmadi/shia words wale content drop
  - Quran folder READ-ONLY (guard kaam karta rehta hai)
  - likhwai sirf data/corpus_big/ me
  - adat: har request ke darmiyan sukoon (site ka ehtram)
  - LIVE mode: koi 24-ghante ka auto-lock NAHI (user ke bolne par allo;
    habni / --stop se sada band hota hai)

Chalane ka tareeqa:
  python harvest\\harvester.py --tick     (ek round run)
  python harvest\\harvester.py --status   (kitna hua?)
  python harvest\\harvester.py --stop     (manually lock kar do)
"""
import hashlib
import html
import json
import os
import random
import re
import subprocess
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

if getattr(sys, "frozen", False):
    ROOT = os.path.dirname(sys.executable)      # 📦 EXE apna folder (Hemomemo)
    if not (os.path.isdir(os.path.join(ROOT, "model"))
            or os.path.isdir(os.path.join(ROOT, "data"))):
        ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)

from harvest.purify import keywords, sanitize  # noqa: E402
from harvest.verify import verify_chunk  # noqa: E402
from harvest import net_guard             # noqa: E402

net_guard.install()   # 🛡️ LIVE-NET firewall: whitelist-only (AI-API/Qadiani block)

HD = os.path.join(ROOT, "harvest")
STATEF = os.path.join(HD, "STATE.json")
SEENF = os.path.join(HD, "seen.json")
LBFILE = os.path.join(HD, "NET_LOCK")
BUDGET = 70.0          # ek tick ki zindagi (second)
GAP = 2.0              # requests ke darmiyan sukoon (site ka ehtram)
UA = "Mozilla/5.0 (HMHS-Muslim-Text-AIKnowledge-Harvester; offline NumPy AI)"

OUTS = {
    "quran": os.path.join(ROOT, "data", "corpus_big", "harvest_quran.txt"),
    "ilm": os.path.join(ROOT, "data", "corpus_big", "harvest_ilm.txt"),
}

# 🚫 SIRF TRUE ISLAMIC SOURCES (No Qadiyani/Shia/Fake data)
TRUSTED_SOURCES = [
    "http://www.clearquran.com/",
    "https://islamqa.info/en/answers/",
    "https://quranx.com/hadith/",
]

# 🚫 FAITH-FORBIDDEN markers (Qadiyani / Ahmadi / Shia / anti-Sunni content)
FAITH_OFF = [
    "qadiyani", "qadiani", "ahmadi", "ahmadiyya", "mirza ghulam",
    "shia", "taifa", "ghulat", "muqtadi",
]

def is_trusted(url):
    return any(url.startswith(s) for s in TRUSTED_SOURCES)

# Tick mein logic update (harvester.py ke andar)


# ---------------------------------------------------------------- helpers
def etext(h: str) -> str:
    """HTML -> saaf text (regex tareeqa — script tags me atakta nahi)."""
    h = re.sub(r"(?is)<(script|style|head)\b.*?</\1>", " ", h)
    h = re.sub(r"(?is)<(br|/p|/div|/li|/h[1-6])[^>]*>", "\n", h)
    h = re.sub(r"(?s)<[^>]+>", "\n", h)
    return html.unescape(h)


def _state():
    try:
        with open(STATEF, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"start": time.time(), "pages": 0, "pairs": 0, "bytes": 0,
                "quran_next": 1, "miss": 0, "ended": False}


def _save(st):
    with open(STATEF, "w", encoding="utf-8") as f:
        json.dump(st, f)


def _seen():
    try:
        with open(SEENF, encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def _save_seen(seen):
    if len(seen) > 50000:
        seen = set(list(seen)[-50000:])
    with open(SEENF, "w", encoding="utf-8") as f:
        json.dump(sorted(seen), f)


def fetch(url):
    ok, why = net_guard.check(url)
    if not ok:
        print("NET-GUARD BLOCK: %s (%s)" % (url[:70], why))
        return None
    try:
        req = Request(url, headers={"User-Agent": UA})
        with urlopen(req, timeout=20) as r:
            return r.read().decode("utf-8", "ignore")
    except (HTTPError, URLError, OSError, ValueError):
        return None


def net_locked():
    return os.path.exists(LBFILE)


def lock(reason="24 hours mukammal"):
    """24h poora — internet access BAND (hamare harvester ki taraf se)."""
    with open(LBFILE, "w", encoding="utf-8") as f:
        f.write("HMHS harvest band: %s | %s\n" % (reason, time.ctime()))
    subprocess.run(["schtasks", "/Change", "/TN", "HMHS_KNOWLEDGE_HARVEST",
                    "/DISABLE"], capture_output=True)
    print("LOCKED: %s" % reason)


# ---------------------------------------------------------------- parsers
def parse_quran(num, et):
    """clearquran page -> (chapter-name, [verse-text]).
    Ghaziyab format: <div id="quran-text"><p><span>1 </span>In the name ...</p>..."""
    verses = []
    body = et
    mb = re.search(r'<div id="quran-text">(.*?)</div>', et, re.S)
    if mb:
        body = mb.group(1)
    pat = re.compile(r"<span>\s*(\d+)\s*</span>\s*(.*?)</p>", re.S)
    for vm in pat.finditer(body):
        n = int(vm.group(1))
        text = re.sub(r"<[^>]+>", " ", vm.group(2))
        text = re.sub(r"\s+", " ", text).strip()
        if n <= 290 and len(text) > 10:
            verses.append((n, text))
    verses.sort(key=lambda x: x[0])
    name = ""
    mn = re.search(r'(?<![-\w])chapter-name">\s*([^<]+)', et)
    if mn:
        name = mn.group(1).strip()
    texts = [t for _, t in verses]
    while len(texts) and texts[-1].count(" ") < 4:
        texts.pop()
    return name, texts


# ---------------------------------------------------------------- writers…
def parse_ilm(et, aid):
    """islamqa.info/en/answers/N -> fatwa ke asli sentences (truncated).
    Anchor: content usually 'Praise be to Allah' se shuru hota hai aur
    'And Allah knows best.' par khatam."""
    t = re.sub(r"\s+", " ", et)
    start = None
    for marker in ("Praise be to Allah", "All praise is due", "Praise be"):
        i = t.find(marker)
        if i >= 0:
            start = i
            break
    if start is None:
        i = t.rfind("Question")
        m = re.search(r"Answer(.{500,9000})", t[i:i + 15000], re.S) if i >= 0 else None
        start = i + 8 if m else -1
        if m:
            body = m.group(1)
        else:
            return None
    else:
        body = t[start:]
    end = body.find("And Allah knows best")
    if end > 0:
        body = body[:end] + " And Allah knows best."
    end2 = body.find("Reference")
    if end2 > 200:
        body = body[:end2]
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", body) if s.strip()]
    # sirf moh sinari sentences (nav-junk hatao)
    sents = [s for s in sents if len(s) > 25 and not s.startswith(("Share", "Search", "Send"))]
    return sents[:12]


# ---------------------------------------------------------------- writer
def write_pairs(src, chunks, seen, fir):
    added = 0
    for ch in chunks:
        txt = sanitize(ch)
        if len(txt) < 60 or len(txt) > 900:
            continue
        # 🛡️ FAITH-GUARD & VERIFICATION
        low = txt.lower()
        if any(mark in low for mark in FAITH_OFF):
            continue
        if not verify_chunk(txt):
            continue
        h = hashlib.sha1(txt.encode("utf-8")).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        kw = keywords(txt)
        if not kw:
            continue
        line = "Sawal: %s\nJawab: %s\n\n" % (kw, txt.replace("\n", " "))
        with open(OUTS[src], "a", encoding="utf-8") as f:
            f.write(line)
        fir.append("Sawal: %s\nJawab: %s..." % (kw, txt[:70]))
        added += 1
    return added


# ---------------------------------------------------------------- tick
def tick(budget=BUDGET):
    st = _state()
    if net_locked():
        print("LOCK maujood (user ne band kiya) — internet band hai.")
        return

    seen = _seen()
    t_deadline = time.time() + budget
    pages = pairs = 0
    first = []

    def gap():
        left = t_deadline - time.time()
        if left > 0:
            time.sleep(min(GAP, max(0.0, left)))

    # --- 1) Quran (114 chapters, ek ek karke) --------------------------
    qn = int(st.get("quran_next", 1))
    if qn <= 114 and time.time() < t_deadline:
        html = fetch("http://www.clearquran.com/%03d.html" % qn)
        gap()
        if html:
            nm, verses = parse_quran(qn, etext(html))
            chunks = []
            i = 0
            label = "Quran %d%s" % (qn, (": " + nm) if nm else "")
            while i < len(verses):
                grp = " ".join(verses[i:i + 4])[:850]
                chunks.append("%s: %s" % (label, grp))
                i += 4
            got = write_pairs("quran", chunks, seen, first)
            pairs += got
            pages += 1
            st["quran_next"] = qn + 1
            st["bytes"] += len(html)
        else:
            st["miss"] += 1

    # --- 2) IslamQA fatwas (jab tak budget hai, max 4/tick) ------------
    fp = 0
    while time.time() < t_deadline and fp < 4:
        aid = random.randint(1, 50000)
        html = fetch("https://islamqa.info/en/answers/%d" % aid)
        gap()
        if not html:
            st["miss"] += 1
            continue
        pages += 1
        fp += 1
        st["bytes"] += len(html)
        sents = parse_ilm(etext(html), aid)
        if sents:
            chunks = []
            i = 0
            while i < len(sents):
                grp = " ".join(sents[i:i + 3])[:850]
                chunks.append("IslamQA (fatwa %d): %s" % (aid, grp))
                i += 3
            got = write_pairs("ilm", chunks, seen, first)
            pairs += got
        else:
            st["miss"] += 1

    st["pages"] += pages
    st["pairs"] += pairs
    st["t_last"] = time.time()
    _save(st)
    _save_seen(seen)
    el_h = (time.time() - st["start"]) / 3600.0
    print("harvest tick: pages +%d | pairs +%d | total %d pages, %d pairs"
          " | LIVE | %.1f hours guzar gaye | miss=%d"
          % (pages, pairs, st["pages"], st["pairs"], el_h, st["miss"]))
    for ln in first[:3]:
        print("  " + ln.replace("\n", " | "))


# ---------------------------------------------------------------- mains
def purify_files():
    """Mojud harvest files saaf: FAITH Off (qadiyani/shia) wale pair hatao."""
    for src, p in OUTS.items():
        if not os.path.exists(p):
            continue
        with open(p, encoding="utf-8") as f:
            blocks = [b for b in f.read().split("\n\n") if b.strip()]
        keep, drop = [], 0
        for b in blocks:
            low = b.lower()
            if any(mark in low for mark in FAITH_OFF):
                drop += 1
                continue
            keep.append(b)
        with open(p, "w", encoding="utf-8") as f:
            f.write("\n\n".join(keep) + ("\n" if keep else ""))
        print("%s: %d hata diye, %d paak baq massali (paak rahe disaar)"
              % (os.path.basename(p), drop, len(keep)))


def status():
    st = _state()
    el = time.time() - st["start"]
    locked = net_locked()
    print("harvest status: %.1f hours chale | pages %d | pairs %d |"
          " quran chapter %d/114 | miss %d"
          % (el / 3600.0, st.get("pages", 0), st.get("pairs", 0),
             st.get("quran_next", 1), st.get("miss", 0)))
    for src, p in OUTS.items():
        sz = os.path.getsize(p) if os.path.exists(p) else 0
        print("  %-7s %8d bytes" % (src, sz))
    print("internet: %s" % ("LOCKED (band)" if locked else
                            "LIVE (whitelist-only — AI-APIs + Qadiani sites BLOCK)"))


def main():
    if net_locked():
        print("LOCK ojood — internet-band mode. Kuch nahi kiya jayega.")
        status()
        return
    if "--status" in sys.argv:
        status()
        return
    if "--stop" in sys.argv:
        lock("user ne pehle hi band kiya")
        return
    if "--once" in sys.argv or "--tick" in sys.argv:
        tick()
        return
    print("istemaal: --once | --status | --stop")


if __name__ == "__main__":
    main()
