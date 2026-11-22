# -*- coding: utf-8 -*-
"""_livedata.py — LIVE-KNOWLEDGE INSTALLER (2-ghantay training window ke sath).

User ka hukum: "google say real live data utha kro, hr waqt live connect,
jitna ho sake knowledge install kro, training ko acha kro".

Qanoon (pakka):
  - net_guard L1 firewall LAGA kar — whitelist ke siwa KUCH nahi
  - Doosre AI-API hosts HARD-BLOCK (openai/gemini/anthropic/...) — waise hi
  - Sirf READ: google search snippets + duckduckgo + wikipedia summaries
  - Jo aaye wo ASCII-pak bana kar data/corpus_big/harvest_live.txt me
    Sawal:/Jawab: pairs ke tor par INSTALL hota hai → retrieval ko foran
    nazar aata hai (app agla chat par ye ilm deta hai)
  - Dedup (sha1) — ek hi ilm dobara nahi likha jata
"""
import hashlib
import html as _html
import io
import json
import os
import re
import sys
import time
import urllib.parse

import requests            # 🛡️ certifi CA-bundle (urllib ka SSL-chain is PC par
                           #     purana hai — requests se pak-connection banta hai)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, r"D:\DigitalBrain")
os.chdir(r"D:\DigitalBrain")

from harvest import net_guard            # noqa: E402
net_guard.install()                      # 🛡️ L1 firewall (whitelist-only)

BUDGET_S = float(os.environ.get("TRAIN_SECONDS", "7200"))
OUT = os.path.join("data", "corpus_big", "harvest_live.txt")
SEEN_LIVE = os.path.join("harvest", "seen_live.json")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "HMHS-LiveKnowledge-Installer; offline NumPy AI")
GAP = 3.0                                # site ka ehtram — har request ke darmiyan

TOPICS = (
    # 🕌 islam (pak-sar-chashm: wikipedia/quran/hadith sources)
    "tawheed", "salah", "zakat", "sawm fasting", "hajr e aswad", "hajj",
    "quran revelation", "hadith authentication isnaad", "seerah of prophet",
    "sahaba companions", "dhikr", "dua etiquette", "istiakhara", "sabr",
    "shukr gratitude", "islamic calendar hijri", "ghusl", "wudu", "tayammum",
    "zakah nisab", "i’tikaf", "laylat al-qadr", "ramadan rules",
    # 🔬 ilm
    "photosynthesis", "solar system", "water cycle", "gravity", "atom",
    "DNA double helix", "vaccine how it works", "mount everest", "pacific ocean",
    "climate change", "black hole", "electric current", "magnetism",
    "human heart", "human brain", "immune system", "antibiotics",
    "photosynthesis equation", "periodic table", "light speed",
    "plate tectonics", "volcano", "rainbow formation", "moon phases",
    "antarctica", "sahara desert", "amazon rainforest", "honey bee",
    "camel adaptation", "date palm tree",
    # 📐 math
    "algebra basics", "geometry basics", "prime number", "fibonacci sequence",
    "percentage calculation", "trigonometry basics", "logarithm",
    "pythagorean theorem", "probability basics", "statistics mean median",
    # 💻 coding (rules + steps — user ka khaas hukum)
    "python programming language", "javascript programming language",
    "typescript language", "java programming language", "c plus plus language",
    "c sharp language", "golang language", "rust programming language",
    "php language", "ruby language", "bash shell scripting", "html5 basics",
    "css3 flexbox grid", "sql database basics", "kotlin language",
    "dart flutter language", "perl scripting", "lua scripting",
    "haskell functional", "scala language", "data structures overview",
    "big o notation", "sorting algorithms", "binary search algorithm",
    "hash table", "linked list", "binary tree traversal", "graph bfs dfs",
    "dynamic programming", "recursion basics", "regex basics",
    "git version control", "rest api design", "json format", "http status codes",
    "sql injection prevention", "unit testing", "debugging techniques",
    "clean code principles", "object oriented programming", "solid principles",
    "neural network basics", "lstm network", "machine learning basics",
    "overfitting underfitting", "gradient descent", "backpropagation",
    "tokenization nlp", "chatbot architecture", "offline ai design",
    "embedded systems basics", "docker container basics", "http vs https",
    "unicode utf 8", "compiler vs interpreter", "memory management",
)

_hdrs = {"User-Agent": UA, "Accept-Language": "en"}

def _get(url, timeout=15):
    ok, why = net_guard.check(url)
    if not ok:
        return None
    try:
        r = requests.get(url, headers=_hdrs, timeout=timeout)
        if r.status_code != 200:
            return None
        return r.text
    except Exception:
        return None


def _ascii(text, cap=900):
    t = re.sub(r"[^\x20-\x7e\n]", " ", text or "")
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = re.sub(r"\n{2,}", "\n", t).strip()
    return t[:cap]


def wiki_summary(topic):
    """Wikipedia REST summary — saaf, bharosay-ka ilm."""
    u = ("https://en.wikipedia.org/api/rest_v1/page/summary/"
         + urllib.parse.quote(topic.replace(" ", "_")))
    j = _get(u)
    if not j:
        return None
    try:
        d = json.loads(j)
        ext = (d.get("extract") or "").strip()
        return ext if len(ext) > 80 else None
    except Exception:
        return None


def wiki_full_extract(topic, cap=4000):
    """Poora article plain-text (gehra ilm — 'jitna ho sake' hukum par)."""
    u = ("https://en.wikipedia.org/w/api.php?action=query&format=json"
         "&prop=extracts&explaintext=1&redirects=1&titles="
         + urllib.parse.quote(topic))
    j = _get(u)
    if not j:
        return None
    try:
        d = json.loads(j)
        pages = d.get("query", {}).get("pages", {})
        for _pid, pd in pages.items():
            ext = (pd.get("extract") or "").strip()
            if len(ext) > 500:
                return ext[:cap]
    except Exception:
        return None
    return None


def wiki_search(topic, limit=3):
    """Wikipedia ACTION-api search — bot-friendly snippets (Google ke badle)."""
    u = ("https://en.wikipedia.org/w/api.php?action=query&format=json"
         "&list=search&srlimit=%d&srsearch=%s"
         % (limit, urllib.parse.quote(topic)))
    j = _get(u)
    out = []
    if not j:
        return out
    try:
        d = json.loads(j)
        for hit in d.get("query", {}).get("search", []):
            s = _ascii(re.sub(r"(?s)<[^>]+>", " ", hit.get("snippet", "")), 400)
            if len(s) >= 55:
                out.append(s)
    except Exception:
        pass
    return out


def search_snippets(q, engine="google"):
    """Search-page se jumlé (NO API-key, sirf public read)."""
    if engine == "google":
        u = ("https://www.google.com/search?q="
             + urllib.parse.quote(q) + "&num=8&hl=en")
    elif engine == "ddg":
        u = ("https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(q))
    else:
        return []
    page = _get(u)
    if not page:
        return []
    page = _html.unescape(page)
    tmp = re.sub(r"(?is)<(script|style)\b.*?</\1>", " ", page)
    tmp = re.sub(r"(?s)<[^>]+>", "\n", tmp)
    out, saw = [], set()
    for ln in tmp.splitlines():
        s = _ascii(ln, 400)
        if len(s) < 55 or s in saw or "sign in" in s.lower() or "cookie" in s.lower():
            continue
        saw.add(s)
        out.append(s)
        if len(out) >= 6:
            break
    return out


def _load_seen():
    try:
        with open(SEEN_LIVE, encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def _save_seen(seen):
    try:
        with open(SEEN_LIVE, "w", encoding="utf-8") as f:
            json.dump(sorted(seen)[-60000:], f)
    except Exception:
        pass


def install(topic, pairs):
    q1 = "what is %s" % topic
    summ = wiki_summary(topic)
    n = 0
    if summ:
        pairs.append("Sawal: %s kya hai\nJawab: %s" % (topic, summ))
        pairs.append("Sawal: %s\nJawab: %s" % (q1, summ))
        n += 2
    ext = wiki_full_extract(topic)
    if ext:
        # gehra ilm — raw block (training + retrieval dono parhta hai)
        pairs.append("Sawal: %s ki tafseel (deep knowledge)\nJawab: %s"
                     % (topic, ext[:1500]))
        pairs.append("# deep:%s\n%s" % (topic, ext))
        n += 2
    for s in wiki_search(topic)[:2]:
        pairs.append("Sawal: %s — aur batao\nJawab: %s" % (topic, s))
        n += 1
    for eng in ("google", "ddg"):          # fallback (aksar bot-block, koi baat nahi)
        snips = search_snippets("%s explained" % topic, eng)
        time.sleep(GAP)
        for s in snips[:2]:
            pairs.append("Sawal: %s — web sach\nJawab: %s" % (topic, s))
            n += 1
    return n


def main():
    t0 = time.time()
    deadline = t0 + BUDGET_S
    seen = _load_seen()
    pairs, dup = [], 0
    print("🌐 LIVE-KNOWLEDGE INSTALLER shuru — budget %.0f min | %d topics"
          % (BUDGET_S / 60.0, len(TOPICS)), flush=True)
    i, added = 0, 0
    while time.time() < deadline:
        topic = TOPICS[i % len(TOPICS)]
        i += 1
        before = len(pairs)
        try:
            install(topic, pairs)
        except Exception as e:
            print("  topic-fail[%s]: %s" % (topic, str(e)[:50]), flush=True)
        for p in pairs[before:]:
            h = hashlib.sha1(p.encode("utf-8", "ignore")).hexdigest()
            if h in seen:
                dup += 1
        seen.update(hashlib.sha1(p.encode("utf-8", "ignore")).hexdigest()
                    for p in pairs[before:])
        added = len(pairs)
        print("  [%d/%d] %s → total %d items (dup %d) | %.0f min baki"
              % (i, len(TOPICS), topic, added, dup,
                 (deadline - time.time()) / 60.0), flush=True)
        if added >= 40:                     # har 40 items par INSTALL (file me)
            _flush(pairs, seen)
            pairs = []
        time.sleep(20.0)
    _flush(pairs, seen)
    print("🏁 LIVE-INSTALLER mukammal: %d total items | dup %d | %.1f min"
          % (added, dup, (time.time() - t0) / 60.0), flush=True)


def _flush(pairs, seen):
    if not pairs:
        return
    _save_seen(seen)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write("\n\n# live-install %s\n" % time.strftime("%Y-%m-%d %H:%M"))
        for p in pairs:
            f.write(p + "\n")
    print("  💾 INSTALL: +%d items -> corpus_big/harvest_live.txt"
          % len(pairs), flush=True)


if __name__ == "__main__":
    main()
