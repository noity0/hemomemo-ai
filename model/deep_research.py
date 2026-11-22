"""deep_research.py - Hemomemo DEEP-RESEARCH (100% local, no AI-API)
=================================================================
Marhale (Perplexity-ANDAZ, magar dimagh apna):
  1) search_api se top natije (keyless DDG / keyed search-API)
  2) top pages khud PARHO (urllib + net_guard whitelist)
  3) jumle nikaalo, sawal-keywords se rank karo, duplicate hatao
  4) report: khulasa + ahem-nukat (har nukat ke sath source) + sources

Koi AI-platform API NAHI - sirf search + page-reading + local ranking.
"""
import re
import time
import urllib.request

try:
    from harvest import net_guard
    net_guard.install()
except Exception:
    net_guard = None

from model import search_api as sa

_UA = sa._UA_BROWSER
_TAG_RX = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
_ALL_RX = re.compile(r"<[^>]+>")
_WS_RX = re.compile(r"\s+")
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\u0600-\u06FF])")


def _fetch(url, timeout=9.0):
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    return raw.decode("utf-8", "replace")


def _page_text(url, max_chars=9000):
    """HTML -> saaf text (title + paragraphs)."""
    try:
        html = _fetch(url)
    except Exception:
        return "", ""
    title = ""
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S | re.I)
    if m:
        title = _WS_RX.sub(" ", _ALL_RX.sub(" ", m.group(1))).strip()[:120]
    html = _TAG_RX.sub(" ", html)
    for tag in ("p", "h1", "h2", "h3", "li"):
        html = re.sub(r"<%s[^>]*>" % tag, "\n", html, flags=re.I)
    text = _ALL_RX.sub(" ", html)
    text = _WS_RX.sub(" ", text)
    return title, text[:max_chars]


def _keywords(q):
    stop = ("ka", "ki", "ke", "ko", "kya", "hai", "me", "mein", "the", "a",
            "of", "in", "on", "for", "and", "or", "to", "kaise", "kaisa",
            "karo", "batao", "what", "is", "are", "how", "why")
    return [w for w in re.findall(r"[a-zA-Z\u0600-\u06FF]{3,}", q.lower())
            if w not in stop][:8] or [q.lower()]


def _sentences(text, keys, limit=14):
    out, seen = [], set()
    for s in _SENT_SPLIT.split(text):
        s = s.strip()
        if len(s) < 45 or len(s) > 320:
            continue
        low = s.lower()
        if not any(k in low for k in keys):
            continue
        fp = low[:60]
        if fp in seen:
            continue
        seen.add(fp)
        score = sum(1 for k in keys if k in low) + min(2, len(s) // 120)
        out.append((score, s))
    out.sort(key=lambda t: -t[0])
    return [s for _, s in out[:limit]]


def research(topic, max_pages=4, timeout=45.0):
    """(text, meta) - gehri-report chat-ready."""
    t0 = time.time()
    topic = (topic or "").strip()
    if not topic:
        return "[deep-research] Topic likho: 'deep research <topic>'", \
            {"source": "deep-research", "state": "need-topic"}
    keys = _keywords(topic)
    prov, hits, err = sa.search(topic, max_results=8)
    if not hits:
        return ("[deep-research] Search hi nahi chala (%s) - internet/"
                "net-guard check karo." % (err or "unknown"),
                {"source": "deep-research", "state": "search-fail"})
    pages, lines = [], []
    for h in hits[:max_pages]:
        url = h.get("url", "")
        if not url:
            continue
        title, text = _page_text(url)
        if not text:
            continue
        sents = _sentences(text, keys)
        if sents:
            pages.append({"title": title or h.get("title", ""), "url": url,
                          "n": len(sents)})
            lines.extend((s, url) for s in sents)
    if not lines:
        # page-read fail to search-snippets se hi report banao (honest)
        lines = [(h.get("snippet") or "", h.get("url", "")) for h in hits
                 if h.get("snippet")]
        if not lines:
            return ("[deep-research] Pages parh nahi saka (block/offline) - "
                    "dobara koshish karo.", {"source": "deep-research",
                                             "state": "no-content"})
    seen, picked = set(), []
    for s, u in sorted(lines, key=lambda t: -len(t[0]))[:18]:
        fp = re.sub(r"\W+", "", s.lower())[:70]
        if fp in seen:
            continue
        seen.add(fp)
        picked.append((s, u))
    dom = lambda u: re.sub(r"^https?://(www\.)?", "", u or "").split("/")[0]
    src_list, idx = {}, []
    for s, u in picked:
        i = src_list.setdefault(dom(u), len(src_list) + 1)
        idx.append((s, i))
    out = ["[deep-research] '%s' - report (%d sources, %.1fs):"
           % (topic, len(src_list), time.time() - t0),
           "KHULASA: %d nukat milay:" % len(idx)]
    for s, i in idx:
        out.append("- %s [%d]" % (s[:280], i))
    out.append("SOURCES:")
    for d, i in sorted(src_list.items(), key=lambda t: t[1]):
        out.append("  [%d] %s" % (i, d))
    out.append("(Sirf search+page-read hua - koi AI-API nahi; "
               "dimagh 100% local.)")
    return "\n".join(out), {"source": "deep-research",
                            "provider": prov, "pages": len(pages),
                            "points": len(idx)}


if __name__ == "__main__":
    txt, meta = research("quantum computing basics", max_pages=2)
    print(txt[:1500])
    print("META:", meta)
