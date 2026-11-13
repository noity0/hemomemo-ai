"""search_api.py - Hemomemo WEB-SEARCH (Search-API qanoon: ALLOWED)
==============================================================
User-hukum (qanoon amended): web-search API allowed, AI-platform API
KABHI nahi. Ye module sirf SEARCH karta hai - dimagh 100% local rehta hai.

Providers:
  1. DuckDuckGo HTML/Lite  - KEYLESS (default, hamesha chalta hai)
  2. Google CSE (customsearch JSON)   - optional key: data/api_keys.json
  3. Bing Web-Search v7               - optional key
  4. Brave Search API                 - optional key

api_keys.json format (OWNER-machine par, zip me KABHI nahi jata):
  {"google_cse_key": "...", "google_cse_cx": "...",
   "bing_search_key": "...", "brave_search_key": "..."}

net_guard: ye module urllib use karta hai - harvest.net_guard.install()
se guarded hota hai (deny-by-default whitelist: duckduckgo/google/bing
allowed; AI-platform hosts BANNED_AI_RX se HARD-BLOCK).
"""
import html as _html
import json
import os
import re
import time
import urllib.parse
import urllib.request

try:
    from harvest import net_guard
    net_guard.install()                        # firewall ON (urllib guarded)
except Exception:
    net_guard = None

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYS_PATH = os.path.join(_ROOT, "data", "api_keys.json")

_UA_BROWSER = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
               "AppleWebKit/537.36 (KHTML, like Gecko) "
               "Chrome/124.0.0.0 Safari/537.36")
_UA_HEMOMEMO = "HemomemoAI-Search/4.2 (local; +no-AI-API)"

_TAG_RX = re.compile(r"<[^>]+>")
_WS_RX = re.compile(r"\s+")
_CACHE = {}                                    # query -> results (session)

# --------------------------------------------------------------- helpers


def _clean(s):
    """HTML-tags hatao + entities + spaces collapse."""
    s = _TAG_RX.sub(" ", s or "")
    s = _html.unescape(s)
    return _WS_RX.sub(" ", s).strip()


def _fetch(url, timeout=10.0, browser_ua=True, headers=None):
    """Plain GET -> text (net_guard ke through)."""
    h = {"User-Agent": _UA_BROWSER if browser_ua else _UA_HEMOMEMO}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    for enc in ("utf-8", "latin-1"):
        try:
            return raw.decode(enc)
        except Exception:
            continue
    return raw.decode("utf-8", "replace")


def _fix_url(href):
    """DDG redirect (uddg=) ya protocol-relative URL -> asli URL."""
    if not href:
        return ""
    href = _html.unescape(href.strip())
    if href.startswith("//duckduckgo.com/l/?") or "uddg=" in href[:60]:
        try:
            q = urllib.parse.urlparse(href if href.startswith("http")
                                      else "https:" + href).query
            u = urllib.parse.parse_qs(q).get("uddg", [""])[0]
            if u:
                return u
        except Exception:
            pass
    if href.startswith("//"):
        return "https:" + href
    return href


def _load_keys():
    """data/api_keys.json -> dict (ghaib ho to {} - keyless chalega)."""
    try:
        with open(KEYS_PATH, "r", encoding="utf-8") as f:
            k = json.load(f)
        return k if isinstance(k, dict) else {}
    except Exception:
        return {}

# ------------------------------------------------- 1) DuckDuckGo (keyless)


def ddg_html_search(query, max_results=6, timeout=10.0):
    """html.duckduckgo.com HTML-results -> [{title,url,snippet}]."""
    url = ("https://html.duckduckgo.com/html/?q="
           + urllib.parse.quote_plus(query))
    page = _fetch(url, timeout=timeout, browser_ua=True)
    out, links = [], []
    for m in re.finditer(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>',
            page, re.S):
        links.append((_fix_url(m.group(1)), _clean(m.group(2))))
    snips = [_clean(s.group(1)) for s in re.finditer(
        r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>', page, re.S)]
    for i, (u, t) in enumerate(links):
        if not u or not t:
            continue
        out.append({"title": t, "url": u,
                    "snippet": snips[i] if i < len(snips) else ""})
        if len(out) >= max_results:
            break
    return out


def ddg_lite_search(query, max_results=6, timeout=10.0):
    """lite.duckduckgo.com fallback (sada table-HTML)."""
    url = ("https://lite.duckduckgo.com/lite/?q="
           + urllib.parse.quote_plus(query))
    page = _fetch(url, timeout=timeout, browser_ua=True)
    out = []
    links = [(_fix_url(m.group(1)), _clean(m.group(2)))
             for m in re.finditer(
                 r'<a[^>]+href="([^"]+)"[^>]*class="result-link"[^>]*>'
                 r"(.*?)</a>", page, re.S)]
    if not links:
        links = [(_fix_url(m.group(1)), _clean(m.group(2)))
                 for m in re.finditer(
                     r'<a[^>]+rel="nofollow"[^>]+href="([^"]+)"[^>]*>'
                     r"(.*?)</a>", page, re.S)]
    snips = [_clean(s.group(1)) for s in re.finditer(
        r'class="result-snippet"[^>]*>(.*?)</td>', page, re.S)]
    for i, (u, t) in enumerate(links):
        if not u or not t:
            continue
        out.append({"title": t, "url": u,
                    "snippet": snips[i] if i < len(snips) else ""})
        if len(out) >= max_results:
            break
    return out

# ------------------------------------------------- 2) keyed providers


def google_cse_search(query, max_results=6, timeout=10.0, keys=None):
    """Google Custom-Search JSON API (SEARCH-api - AI-API NAHI hai)."""
    k = keys if keys is not None else _load_keys()
    key, cx = k.get("google_cse_key"), k.get("google_cse_cx")
    if not key or not cx:
        return []
    u = ("https://www.googleapis.com/customsearch/v1?key=%s&cx=%s&q=%s&num=%d"
         % (urllib.parse.quote(key), urllib.parse.quote(cx),
            urllib.parse.quote_plus(query), max(1, min(10, max_results))))
    j = json.loads(_fetch(u, timeout=timeout, headers={
        "User-Agent": _UA_HEMOMEMO}))
    return [{"title": it.get("title", ""),
             "url": it.get("link", ""),
             "snippet": _clean(it.get("snippet", ""))}
            for it in (j.get("items") or [])][:max_results]


def bing_search(query, max_results=6, timeout=10.0, keys=None):
    """Bing Web-Search v7 (SEARCH-api)."""
    k = keys if keys is not None else _load_keys()
    key = k.get("bing_search_key")
    if not key:
        return []
    u = ("https://api.bing.microsoft.com/v7.0/search?q=%s&count=%d"
         "&responseFilter=Webpages"
         % (urllib.parse.quote_plus(query), max(1, min(20, max_results))))
    j = json.loads(_fetch(u, timeout=timeout, headers={
        "User-Agent": _UA_HEMOMEMO,
        "Ocp-Apim-Subscription-Key": key}))
    vals = ((j.get("webPages") or {}).get("value")) or []
    return [{"title": v.get("name", ""), "url": v.get("url", ""),
             "snippet": _clean(v.get("snippet", ""))} for v in vals][:max_results]


def brave_search(query, max_results=6, timeout=10.0, keys=None):
    """Brave Search API (SEARCH-api)."""
    k = keys if keys is not None else _load_keys()
    key = k.get("brave_search_key")
    if not key:
        return []
    u = ("https://api.search.brave.com/res/v1/web/search?q=%s&count=%d"
         % (urllib.parse.quote_plus(query), max(1, min(20, max_results))))
    j = json.loads(_fetch(u, timeout=timeout, headers={
        "Accept": "application/json",
        "X-Subscription-Token": key}))
    res = ((j.get("web") or {}).get("results")) or []
    return [{"title": r.get("title", ""), "url": r.get("url", ""),
             "snippet": _clean(r.get("description", ""))}
            for r in res][:max_results]

# --------------------------------------------------------------- main API


def search(query, max_results=6, timeout=10.0):
    """(provider, results, error) - key-mile to keyed, warna DDG keyless.

    results: [{title,url,snippet}] - empty list + error = offline/block.
    """
    q = (query or "").strip()
    if not q:
        return "none", [], "khali-sawal"
    ck = (q.lower(), max_results)
    if ck in _CACHE:
        return _CACHE[ck][0], list(_CACHE[ck][1]), ""
    keys = _load_keys()
    tried = []
    for name, fn in (("google-cse", google_cse_search),
                     ("bing", bing_search),
                     ("brave", brave_search)):
        try:
            r = fn(q, max_results=max_results, timeout=timeout, keys=keys)
            if r:
                _CACHE[ck] = (name, r)
                return name, r, ""
        except Exception as e:
            tried.append("%s: %s" % (name, e))
    for name, fn in (("duckduckgo-html", ddg_html_search),
                     ("duckduckgo-lite", ddg_lite_search)):
        try:
            r = fn(q, max_results=max_results, timeout=timeout)
            if r:
                _CACHE[ck] = (name, r)
                return name, r, ""
        except Exception as e:
            tried.append("%s: %s" % (name, e))
    err = "; ".join(tried) or "koi-provider-jawab-na-de"
    return "none", [], err[:300]


def search_text(query, max_results=5, timeout=10.0):
    """Chat-ready formatted jawab -> (text, meta)."""
    t0 = time.time()
    prov, res, err = search(query, max_results=max_results, timeout=timeout)
    if not res:
        msg = ("[web-search] '%s' - koi result nahi mila.\n"
               "Wajah: %s\n(Isa hota hai jab internet band ho ya "
               "net-guard ne host roka ho.)" % (query, err or "unknown"))
        return msg, {"source": "web-search", "error": err}
    lines = ["[web-search] '%s' - top %d natije (%s, %.1fs):"
             % (query, len(res), prov, time.time() - t0)]
    for i, r in enumerate(res, 1):
        lines.append("%d. %s\n   %s\n   %s"
                     % (i, r.get("title", "")[:120],
                        r.get("snippet", "")[:200],
                        r.get("url", "")[:160]))
    lines.append("(Dimagh 100% local - sirf search-API istemal hua, "
                 "koi AI-API nahi.)")
    return "\n".join(lines), {"source": "web-search", "provider": prov,
                              "n": len(res)}

# ------------------------------------------------- intent-detect (app hook)


_SEARCH_RX = re.compile(
    r"(?i)^\s*(?:web[\s-]?search|search(?:\s+for|\s+karo|\s+kar)?"
    r"|khojo|khoj(?:\s+karo)?|talaash(?:\s+karo)?|dhoondo|dhundo"
    r"|google)\s*[:\-\s]\s*(.+?)\s*$")
_FILLER = ("karo", "kar", "do", "dedo", "dijiye", "par", "pe", "about",
           "for", "ke", "baare", "mein", "me")


def wants_search(text):
    """(True, query) agar user ne SEARCH hukum diya, warna (False, None)."""
    t = (text or "").strip()
    if not t:
        return False, None
    m = _SEARCH_RX.match(t)
    if not m:
        return False, None
    q = m.group(1).strip()
    # leading filler-words hatao ("search karo python" -> "python")
    parts = q.split()
    while parts and parts[0].lower().strip(",.") in _FILLER:
        parts.pop(0)
    q = " ".join(parts).strip()
    if len(q) < 2:
        return False, None
    return True, q


if __name__ == "__main__":
    for _t in ("search python dictionary", "khojo quran tafseer",
               "hello kaise ho"):
        print(_t, "->", wants_search(_t))
    prov, res, err = search("Hemomemo AI github noity0", 3)
    print("provider:", prov, "| n:", len(res), "| err:", err)
    for r in res:
        print("-", r["title"], "|", r["url"])
