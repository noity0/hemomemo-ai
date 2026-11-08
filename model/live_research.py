"""
🌐 live_research.py — Hemomemo AI LIVE INTERNET-RESEARCH (whitelist-only, guard ON)

Kiya karta hai:
  - GAIR-ISLAMIC sawal jo yaad/model se pura na hua → live research (jawab)
  - ISLAMIC sawal par internet NAHI — sirf Quran + 7 Hadith books (corpus)
    se cited jawab; ilm na ho to imandari se mana (no fake)
  - net_guard: AI-model APIs + Qadiani sites HARD-BLOCK; sirf pak whitelist
  - SSL-fallback: kuch networks par whitelisted host ka cert intercept hota
    hai (expired dikhta hai) — us case me sirf WHITELIST host ke liye ek-dafa
    unverified-context retry (log me sabit) — kisi gair-whitelist host par nahi
  - QADIANI-guard: research text me banned-faith word mile to FORAN DROP
  - Research ka nateja data/corpus_big/liveresearch.txt me save — agli dafa
    brain khud yaad(retrieval) se jawab dega (live sirf pehli baar)

Run test:
    python model\\live_research.py "photosynthesis kya hai"
"""
import base64
import hashlib
import html as _htmlmod
import json
import os
import re
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

if getattr(sys, "frozen", False):
    ROOT = os.path.dirname(sys.executable)      # 📦 EXE apna folder (Hemomemo)
    if not (os.path.isdir(os.path.join(ROOT, "model"))
            or os.path.isdir(os.path.join(ROOT, "data"))):
        ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from harvest import net_guard              # noqa: E402
net_guard.install()                        # 🛡️ firewall ON

OUT_PATH = os.path.join(ROOT, "data", "corpus_big", "liveresearch.txt")
CACHE = {}
_SEEN = None
_SSL_FALLBACK = ssl._create_unverified_context()   # sirf whitelisted host par

# 🕌 Islamic intent words (ye Quran/Hadith se honge — net istemal NAHI hoga)
_SACRED_HARD = {
    "quran", "hadith", "sunnah", "allah", "islam", "deen", "namaz", "salah",
    "roza", "siyam", "zakat", "hajj", "umrah", "wudu", "ghusl", "tayammum",
    "qibla", "qiblah", "tahajjud", "fajr", "zuhr", "asr", "isha", "maghrib",
    "kafir", "kufr", "shirk", "jannah", "jahannam", "nabi", "prophet",
    "rasool", "muhammad", "bukhari", "muslim", "tirmidhi", "abudawud",
    "nasai", "ibnmajah", "muwatta", "hijab", "dhikr", "tawheed", "tawhid",
    "bismillah", "alhamdulillah", "inshallah", "iftar", "sahur", "khatam",
    "mushrik", "muttaqi", "ayat", "sura", "surah", "mahram", "mehram",
    "murtad", "talaq", "nikah", "sadaqah", "fitr", "eid", "makkah",
    "madinah", "kaaba", "zakariya", "jibril", "sallallahu", "wasallam",
    "ummat", "shahadah", "shahada", "iman", "dunya", "aakhiret",
}
_SACRED_SOFT = {
    "ibadat", "masjid", "jamaat", "khairat", "nafs", "taqwa", "hidayat",
    "imam", "sabr", "shukr", "khushu", "ilhaam", "risalat", "haq", "batil",
    "juz", "sajdah", "dawah", "akhlaq", "tariqah", "hayaa",
}
_SACRED_BANNED = {"mirza", "qadiani", "qadian", "ahmadiyya", "ahmadi"}


def is_sacred(prompt: str) -> bool:
    """Kya ye SIRF-Islamic sawal hai? (True = internet NAHI, books se do)"""
    words = set(re.findall(r"[a-z]{2,}", prompt.lower()))
    if words & _SACRED_BANNED:
        return True          # qadiani sawal bhi books-verify hi hoga
    if words & _SACRED_HARD:
        return True
    return (len(words & _SACRED_SOFT) >= 2)


_TITLE_STOP = set("""kya kyun kaun kaise hai hain ho ke ki ka ko se me in aur
the what how why is are do does a an of in on for about give me please batao
btao bolo jao nahin nahi nhi tha te ye woh it its ka matlab definition par""".split())


def _title_from(prompt: str) -> str:
    """Unknown sawal → sabse salient alfaaz → wiki title."""
    words = [w for w in re.findall(r"[A-Za-z]{3,}", prompt)
             if w.lower() not in _TITLE_STOP]
    if not words:
        return ""
    return "_".join(words[:3])


def _fetch_json(url: str, timeout: float = 12.0):
    """Guard-check + JSON. SSL-intercept par WHITELIST-ONLY fallback (logged)."""
    ok, why = net_guard.check(url)
    if not ok:
        net_guard._log("RESEARCH-BLOCK url=%s reason=%s" % (url[:180], why))
        return None
    req = urllib.request.Request(
        url, headers={"User-Agent": "HMHS-MuslimTexture-AI/1.0 "
                                    "(offline NumPy; knowledge research)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8", "ignore"))
    except ssl.SSLError:
        pass
    except urllib.error.URLError as e:
        # 🎯 CERT-INTERCEPTED network: reason me SSL cert fail (expired) —
        # sirf guard-passed (whitelist) URL ke liye ek-dafa fallback
        if not ("CERTIFICATE" in str(e.reason) or isinstance(
                e.reason, ssl.SSLError)):
            return None
        net_guard._log("SSL-FALLBACK url=%s" % url[:180])
        try:
            with urllib.request.urlopen(req, timeout=timeout,
                                        context=_SSL_FALLBACK) as r:
                return json.loads(r.read().decode("utf-8", "ignore"))
        except (urllib.error.HTTPError, urllib.error.URLError, ValueError,
                OSError):
            return None
        except ssl.SSLError:
            return None
    except (urllib.error.HTTPError, ValueError, OSError):
        return None
    return None


def _load_seen():
    global _SEEN
    if _SEEN is None:
        _SEEN = set()
        if os.path.exists(OUT_PATH):
            try:
                with open(OUT_PATH, encoding="utf-8", errors="ignore") as f:
                    for b in f.read().split("\n\n"):
                        if b.strip():
                            _SEEN.add(hashlib.sha1(
                                b[:180].encode("utf-8", "ignore")
                            ).hexdigest())
            except OSError:
                pass
    return _SEEN


def _remember(text: str, prompt: str = None):
    """Research result corpus me likho (ASLI SAWAL + Jawab) — agli dafa
    yaad se khud jawab milega (live research sirf pehli baar)."""
    seen = _load_seen()
    sig = hashlib.sha1(text.encode("utf-8", "ignore")).hexdigest()
    if sig in seen:
        return
    seen.add(sig)
    q = re.sub(r"\s+", " ", (prompt or "").lower()).strip()[:120] or "live research item"
    try:
        with open(OUT_PATH, "a", encoding="utf-8") as f:
            f.write("Sawal: %s\nJawab: %s\n\n" % (q, text))
        # ⚡ CHAT-YAAD me turant jal-dal (same process me ai dafa free milta hai)
        from model import generate as G
        if getattr(G, "_QA_INDEX", None) is not None:
            G._QA_INDEX.append((q, text))
    except Exception:
        pass


def _summary_for(title: str, deadline: float = None):
    """REST summary of a wikit title (str | None). deadline (time.time()) par
    net-hang ROKI jaati hai — trainer-CPU par bhi chat kabhi lamba na rahe."""
    if not title:
        return None
    url = ("https://en.wikipedia.org/api/rest_v1/page/summary/" +
           urllib.parse.quote(title.replace(" ", "_"), safe="_()%.~"))
    d = _fetch_json(url, timeout=5.0 if deadline else 12.0)
    if not isinstance(d, dict):
        return None
    ex = (d.get("extract") or "").strip()
    if len(ex) > 60:
        return "%s: %s" % (d.get("title", title), ex[:420])
    return None


def _strip_snip(snip: str) -> str:
    """MediaWiki search snippet ke HTML tags saaf."""
    txt = re.sub(r"<[^>]+>", "", snip or "")
    return (txt.replace("&quot;", '"').replace("&amp;", "&")
               .replace("&#39;", "'").strip())


def _wiki(query: str, deadline: float = None):
    """3-strategy wiki research (sab en.wikipedia.org — whitelist me):
    1) REST summary seedha   2) apna lexicon → English title summaries
    3) wiki-search page-parhi → title → summary (sirf topic-hit par!)
    4) wiki-search ka snippet hi (last resort)
    deadline (time.time()) — har net-op se pehle check, chat kabhi hang nahi."""
    title = _title_from(query)
    if not title:
        return None

    def _left():
        return deadline is None or time.time() < deadline

    out = _summary_for(title, deadline) if _left() else None
    if out:
        return out
    # 🌏 APNA lexicon: har translated token akhri-akhri ("bijli"→"electricity",
    # "suraj"→"sun") — joined nahi (akhri rasta nahi jis par page mil jaye)
    tws = _translated_tokens(query)
    for t in tws[:3]:
        if t.lower() == title.lower() or not _left():
            continue
        out = _summary_for(t, deadline)
        if out:
            return out
    if not _left():
        return None
    # --- strategy 3: wiki-search se saha title dhoondo — LEKIN topic-hit
    # guard: summary me sawal ka koi topic-word hona ZARURI (Asha-junke
    # entity-answers phir kabhi nahi)
    api = ("https://en.wikipedia.org/w/api.php?action=query&format=json"
           "&list=search&srlimit=1&srsearch=" +
           urllib.parse.quote(title.replace("_", " ")))
    d = _fetch_json(api, timeout=5.0 if deadline else 12.0)
    items = ((d or {}).get("query") or {}).get("search") or []
    if items:
        top = items[0].get("title") or ""
        out = _summary_for(top)
        if out:
            topic_words = [w for w in re.findall(r"[a-z]{3,}", title.replace("_", " ").lower())]
            if any(w in out.lower() for w in topic_words):
                return out
        # --- strategy 4: snippet hi le lo — LEKIN sirf jab usme sawal ka
        # word ho (giberish sawal par junk entity answer mat do)
        snip = _strip_snip(items[0].get("snippet", ""))
        tw = [w for w in title.replace("_", " ").split() if len(w) >= 3]
        hit = any(w.lower() in snip.lower() for w in tw)
        if len(snip) > 60 and hit:
            return "%s: %s" % (top or title, snip[:420])
    return None


# 🛡️ qadiani-guard research-text par bhi (kisi bhi non-Islamic ilm me bhi)
_FORBIDDEN_OK = None
def _faith_clean(text: str) -> bool:
    global _FORBIDDEN_OK
    if _FORBIDDEN_OK is None:
        from harvest.source_policy import FORBIDDEN_RX
        _FORBIDDEN_OK = FORBIDDEN_RX
    return not bool(_FORBIDDEN_OK.search(text or ""))


# ----------------------------------------------------------------------
# 🔍 WEB-SEARCH (Google-style details — NO API, sirf read-page parsing)
# ----------------------------------------------------------------------
_TAG_RX = re.compile(r"<[^>]+>")
_UA_BROWSER = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
               "(HMHS-MuslimTexture-AI offline reader) "
               "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36")


def _fetch_text(url: str, timeout: float = 6.0, browser_ua: bool = False):
    """Guard + SSL-fallback ke sath RAW page (search-page parsing)."""
    ok, why = net_guard.check(url)
    if not ok:
        net_guard._log("RESEARCH-BLOCK url=%s reason=%s" % (url[:180], why))
        return None
    req = urllib.request.Request(
        url, headers={"User-Agent": _UA_BROWSER if browser_ua else
                      "HMHS-MuslimTexture-AI/1.0 (offline NumPy research)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode("utf-8", "ignore")
    except ssl.SSLError:
        return _unverified_read(req, timeout)
    except urllib.error.URLError as e:
        if "CERTIFICATE" not in str(e.reason) and not isinstance(
                e.reason, ssl.SSLError):
            return None
        net_guard._log("SSL-FALLBACK url=%s" % url[:180])
        return _unverified_read(req, timeout)
    except (urllib.error.HTTPError, ValueError, OSError):
        return None


def _unverified_read(req, timeout):
    try:
        with urllib.request.urlopen(req, timeout=timeout,
                                    context=_SSL_FALLBACK) as r:
            return r.read().decode("utf-8", "ignore")
    except (urllib.error.HTTPError, urllib.error.URLError, ValueError, OSError):
        return None


def _clean_html(txt: str) -> str:
    return _htmlmod.unescape(_TAG_RX.sub(" ", txt)).strip()


def _unredirect(u: str):
    """DDG/Google/Bing redirect-links → asli URL (uddg=, /url?q=, bing u=a1<base64>)."""
    if not u:
        return None
    u = _htmlmod.unescape(u)
    if "uddg=" in u:
        m = re.search(r"uddg=([^&]+)", u)
        if m:
            u = urllib.parse.unquote(m.group(1))
    elif u.startswith("/url?"):
        m = re.search(r"[?&]q=([^&]+)", u)
        if m:
            u = urllib.parse.unquote(m.group(1))
    # 🅱 Bing click-redirect: /ck/a?!&...&u=a1<base64-of-target-url>
    m = re.search(r"[?&]u=a1([A-Za-z0-9+/=]{20,})", u)
    if m:
        try:
            b = m.group(1)
            dec = base64.b64decode(b + "=" * (-len(b) % 4)).decode(
                "utf-8", "ignore")
            if dec.startswith("http"):
                u = dec
        except Exception:
            pass
    if u.startswith("//"):
        u = "https:" + u
    return u if u.startswith("http") else None


def _ddg(query: str):
    """DuckDuckGo LITE (no-JS page) — result titles + snippets + URLs pars.
    Return: (items, urls) ya None."""
    url = ("https://lite.duckduckgo.com/lite/?q=" +
           urllib.parse.quote(query) + "&kl=wt-wt&df=y")
    page = _fetch_text(url, timeout=4.5)
    if not page:
        return None
    items, urls = [], []
    for m in re.finditer(r"<a\b([^>]*)>(.*?)</a>", page, re.S):
        attrs, inner = m.group(1), m.group(2)
        if "result-link" not in attrs:
            continue
        title = _clean_html(inner)
        if title:
            items.append(title)
        hm = re.search(r'href=["\']([^"\']+)', attrs)
        u = _unredirect(hm.group(1)) if hm else None
        if u:
            urls.append(u)
    # snippets alag stream me aate hain (tab class='result-snippet')
    snips = [_clean_html(s) for s in re.findall(
        r"class=[\"']?result-snippet[\"']?[^>]*>(.*?)</td>", page, re.S)]
    if snips:
        items = [(i + " — " + s[:220]).strip() for i, s in zip(items, snips)]
    if not items:
        return None
    return (items[:4], urls[:4])


def _ddg_html(query: str):
    """DuckDuckGo HTML (no-JS doosra rasta) — lite par bot-flag aye to ye.
    Return: (items, urls) ya None."""
    url = ("https://html.duckduckgo.com/html/?q=" +
           urllib.parse.quote(query))
    page = _fetch_text(url, timeout=5.0)
    if not page:
        return None
    items, urls = [], []
    for m in re.finditer(r"<a\b([^>]*)>(.*?)</a>", page, re.S):
        attrs, inner = m.group(1), m.group(2)
        if "result__a" not in attrs:
            continue
        title = _clean_html(inner)
        hm = re.search(r'href=["\']([^"\']+)', attrs)
        u = _unredirect(hm.group(1)) if hm else None
        if title:
            items.append(title)
            if u:
                urls.append(u)
    snips = [_clean_html(s) for s in re.findall(
        r"class=[\"']?result__snippet[\"']?[^>]*>(.*?)</a>", page, re.S)]
    if snips:
        items = [(i + " — " + s[:220]).strip() for i, s in zip(items, snips)]
    if not items:
        return None
    return (items[:4], urls[:4])


def _mojeek(query: str):
    """Mojeek (apna-index engine — NO API, bot-friendly) — DDG band ho to
    azaad rasta. Return: (items, urls) ya None."""
    url = ("https://www.mojeek.com/search?q=" + urllib.parse.quote(query))
    page = _fetch_text(url, timeout=5.0, browser_ua=True)
    if not page:
        return None
    items, urls = [], []
    for m in re.finditer(r"<a\b([^>]*)>(.*?)</a>", page, re.S):
        attrs, inner = m.group(1), m.group(2)
        if 'class="title"' not in attrs:
            continue
        title = _clean_html(inner)
        hm = re.search(r'href=["\']([^"\']+)', attrs)
        u = _unredirect(hm.group(1)) if hm else None
        if title and u:
            items.append(title)
            urls.append(u)
    # snippet <p class="s"> — items ke sath joro
    snips = [_clean_html(s) for s in re.findall(
        r'<p class="s">(.*?)</p>', page, re.S)]
    if snips and len(snips) == len(items):
        items = [(i + " — " + s[:220]).strip() for i, s in zip(items, snips)]
    if not items:
        return None
    return (items[:4], urls[:4])


def _bing(query: str):
    """Bing search HTML (no API, sirf PAGE-READ) — DDG bot-flag par ye azaad
    rasta (bing.com whitelist me pehle se hai; koi AI-service NAHI).
    Return: (items, urls) ya None."""
    url = ("https://www.bing.com/search?setlang=en&q=" +
           urllib.parse.quote(query))
    page = _fetch_text(url, timeout=4.5, browser_ua=True)
    if not page:
        return None
    items, urls = [], []
    for m in re.finditer(r"<li class=\"b_algo\".*?</li>", page, re.S):
        block = m.group(0)
        tm = re.search(r"<h2[^>]*>\s*<a([^>]*)>(.*?)</a>", block, re.S)
        if not tm:
            continue
        title = _clean_html(tm.group(2))
        pm = re.search(r"<p[^>]*>(.*?)</p>", block, re.S)
        body = _clean_html(pm.group(1)) if pm else ""
        txt = (title + (" — " + body[:240] if body else "")).strip()
        if len(title) >= 6:
            items.append(txt)
            hm = re.search(r'href=["\']([^"\']+)', tm.group(1))
            u = _unredirect(hm.group(1)) if hm else None
            if u:
                urls.append(u)
    if not items:
        return None
    return (items[:4], urls[:4])


def _google(query: str):
    """Google search HTML (no API) — h3 titles + result-snippet divs + URLs.
    Return: (items, urls) ya None."""
    url = ("https://www.google.com/search?num=8&hl=en&q=" +
           urllib.parse.quote(query))
    page = _fetch_text(url, browser_ua=True)
    if not page:
        return None
    items, urls = [], []
    for m in re.finditer(r"<h3[^>]*>(.*?)</h3>", page, re.S):
        t = _clean_html(m.group(1))
        if len(t) >= 4:
            items.append(t)
    # h3 ke pehle wala <a href> usi result ka link hota hai
    for m in re.finditer(r"<a\b[^>]*href=[\"']([^\"']+)[\"'][^>]*>", page):
        u = _unredirect(m.group(1))
        if u and "google." not in urllib.parse.urlparse(u).netloc:
            urls.append(u)
    urls = urls[:len(items) or 6]
    snips = [_clean_html(s.group(1)) for s in re.finditer(
        r'class="[^"]*VwiC3b[^"]*"[^>]*>(.*?)</div>', page)]
    if snips and items:
        items = [i + " — " + s[:200] for i, s in zip(items, snips)]
    if not items:
        return None
    return (items[:4], urls[:4])


def _results_relevant(query: str, items) -> bool:
    """Junk-guard: gibberish sawal ('ofhlsef') par engines random YouTube/FB
    junk dete hain. 🆕 PER-ITEM check: koi EK result hi sawal ke topic-words ka
    60%+ apne ANDAR rakhta ho — poore-blob par nahi (warna ek result me 'asli'
    doosre me 'imtihan' mil kar junk pass ho jata tha)."""
    qtoks = list(dict.fromkeys(re.findall(
        r"[a-z0-9]{4,}", (query or "").lower())))
    if not qtoks:
        return False
    need = 1 if len(qtoks) == 1 else max(2, (len(qtoks) * 3 + 4) // 5)
    for it in (items or []):
        low = (it or "").lower()
        if sum(1 for t in qtoks if t in low) >= need:
            return True
    return False


# 🚫 SPAM-SHAPE junk (yt-shorts/trailer/app-promo/hashtag/mojibake) — ye
# "asli" web-content hai magar jawab ke liye kachra ('asli imtihan' par
# '#viral #ytshorts' jaisa junk jawab na bane)
_SPAM_RX = re.compile(
    r"(?i)(#\w{2,}|ytshorts|\bshorts\b|official trailer|watch .{0,24}app\b"
    r"|download now|streaming (now|free)|full (episode|movie|song)\b"
    r"|subscribe .{0,12}channel|[\u00c3\u00c2\u2580-\u259f]{2,})")


def _coverage_ok(text: str, query: str) -> bool:
    """🚫 FAKE-JAWAB guard: jawab me sawal ke 60%+ topic-words (aur kam-se-kam
    2) na hon to wo off-topic kachra hai — asli jawab nahi ('solar system
    planets' par 'solar panel price… order now' ka jawab JHOOT hai — imandari
    = None, phir wiki-deep asli talash karega)."""
    qtok = set(re.findall(r"[a-z0-9]{4,}", (query or "").lower()))
    if len(qtok) < 2:
        return True
    low = (text or "").lower()
    hits = sum(1 for w in qtok if w in low)
    return hits >= max(2, (len(qtok) * 3 + 4) // 5)


def _weak_text(text: str) -> bool:
    """KAMZOR-jawab shakal: sawal-wala snippet ('… correct order?'), sirf
    title-joint list ('Chart | How to | …' bina kisi jumle ke), ya bohat
    chhota — asli PROSE nahi → wiki-deep ko mauqa do (parho-samjho behtar)."""
    if not text:
        return True
    t = text.strip()
    if t.endswith("?"):
        return True
    if " | " in t and ". " not in t:          # title-joint, jumla-khana nahi
        return True
    return len(re.sub(r"\W+", " ", t).split()) < 12


def _polish_web(items, query: str = "") -> str:
    """🌐 TOPIC-MUTABIQ jawab banao (user qanoon):
      - DDG ka SNIPPET (asli content) pehle — title sirf tab jab chhota ho
      - junk domains (YouTube/FB/Insta/subscribe) REJECT
      - sawal ke topic-words jitna zyada ho us me — utna AGAY rakho"""
    qtok = _topic_tokens(query)
    rows, seen = [], set()
    for it in items[:6]:
        t = re.sub(r"\s+", " ", (it or "")).strip()
        if not t or _JUNK_RX.search(t) or _SPAM_RX.search(t):
            continue
        title, _, snip = t.partition(" — ")
        snip = snip.strip()
        body = snip if len(snip) >= 40 else title.strip()
        if len(body) < 14:
            continue
        key = body.lower()[:38]
        if key in seen:
            continue
        seen.add(key)
        bl = body.lower()
        score = sum(1 for w in qtok if w in bl)
        rows.append((score, body))
    if not rows:
        return ""
    rows.sort(key=lambda p: -p[0])
    # 🛡️ topic-hit NAHI to topic keh nahi — score-0 rows BAHIR (junk-song
    # jaisa crash-prevent; asli topic word hi jawab me chahiye)
    if qtok and rows[0][0] == 0:
        return ""
    rows.sort(key=lambda p: (-p[0], len(p[1])))    # topic-hit zyada pehle
    out = " | ".join(b[:170] for _, b in rows[:3])
    return "Web (live padhai): " + out


# junk-result domains/actions — research jawab me nahi chahiye
_JUNK_RX = re.compile(r"(?i)(youtube\.?|facebook|instagram|tiktok|pinterest|"
                      r"reddit|subscribe|log ?in|sign ?up|apply now|"
                      r"shop now|add ?to ?cart|menu.{0,12}search)")

# reference/TOC/wiki-kachra jumle — jawab me nahi
_JUNK2_RX = re.compile(
    r"(?i)(retrieved|isbn|doi:|archived from|see also|external links|"
    r"references|disambiguation|pages associated|all pages with titles|"
    # wikipedia\.org/wiki — sirf URL-kachra (hamara '(manba: en.wikipedia.org)'
    # attribution ASLI jawab ka hissa hai, wo junk NAHI)
    r"wikipedia\.org/wiki|\.pdf|^\[\d+\]|citation|etymology \[|"
    r"this (article|page) is|categories? :|hidden category|↑"
    r"|list of (songs|tracks|albums|films|episodes)|discography|filmography|"
    r"soundtrack|track ?listing)")

# asli proose-jumle ki pehchan (copula/verb)
_COPULA_RX = re.compile(
    r"(?i)\b(is|are|was|were|refers to|means|can be|known as|called|"
    r"consists|occurs|describes|involves)\b")
_TOPIC_FILLERS = {
    "kya", "hota", "hoti", "hote", "hain", "hai", "ka", "ke", "ki", "ko",
    "se", "mein", "me", "bata", "batao", "btao", "bataiye", "explain",
    "karo", "kro", "kar", "do", "dena", "mujhe", "mera", "meri", "apne",
    "what", "how", "why", "who", "the", "a", "an", "is", "are", "about",
    "of", "and", "to", "in", "on", "for", "kahan", "kab",
    # 🆕 "tell me about X" → X hi search ho (baaki sab filler)
    "tell", "told", "please", "plz", "pls", "want", "know", "give",
    "info", "information", "something", "anything", "sab", "kuch",
}


def _topic_tokens(q: str):
    ws = re.findall(r"[a-z0-9]{3,}", (q or "").lower())
    # chhote lekin topic-maani rakne wale tech-words (DDG/wiki ke liye salient)
    ws2 = re.findall(r"(?<![a-z0-9])(?:ai|ml|pc|tv|gpu)(?![a-z0-9])",
                     (q or "").lower())
    out = ws2 + [w for w in ws if w not in _TOPIC_FILLERS and w not in ws2]
    return out[:8]


def _topic_query(q: str) -> str:
    """Sawal → saaf SEARCH-QUERY (fillers nikaal kar topic-words)."""
    ws = _topic_tokens(q)
    return " ".join(ws) if ws else (q or "")


# ----------------------------------------------------------------------
# 📖 PAGE-READ ENGINE (Perplexity-style — NO API, sirf page parh kar samajh)
# ----------------------------------------------------------------------
_SKIP_BLOCK_RX = re.compile(
    r"(?is)<(script|style|noscript|svg|form|nav|footer|header|aside)"
    r"[^>]*>.*?</\1>")


def _readable(html: str) -> str:
    """HTML → saaf readable text (script/style/nav kachra bahir, block-tags
    newline — sentences sahi katenge)."""
    html = _SKIP_BLOCK_RX.sub(" ", html or "")
    html = re.sub(r"(?i)</(p|div|li|h[1-6]|tr|blockquote|section)>", "\n", html)
    txt = _clean_html(html)
    return re.sub(r"[ \t]{2,}", " ", txt)


def _sentences(text: str):
    """Text → jaanchi-janchi jumle (50..320 chars, 6+ words) — 'parhna' yehi
    hai; reference/TOC/disambiguation-kachra bahir."""
    out = []
    for para in (text or "").split("\n"):
        para = para.strip()
        if len(para) < 45 or _JUNK_RX.search(para):
            continue
        for s in re.split(r"(?<=[.!?])\s+", para):
            s = s.strip()
            if not (50 <= len(s) <= 320) or _JUNK_RX.search(s):
                continue
            # 🚫 title-joint ('Guide - Facts | Site') prose nahi — page-ka sir
            if " | " in s:
                continue
            if len(s.split()) < 6 or _JUNK2_RX.search(s) or _SPAM_RX.search(s):
                continue
            out.append(s)
    return out


def _read_pages(urls, deadline=None, limit=3):
    """Top result-pages GUP-GUP parho (sirf whitelist hosts — net_guard).
    Return: [(domain, [jumle...]), ...] — yehi 'read + samajh' hai."""
    pages, seen = [], set()
    for u in (urls or [])[:limit + 3]:
        if deadline is not None and time.time() > deadline:
            break
        if len(pages) >= limit:
            break
        try:
            host = urllib.parse.urlparse(u).netloc.lower()
        except ValueError:
            continue
        if not u or u in seen:
            continue
        seen.add(u)
        raw = _fetch_text(u, timeout=5.5, browser_ua=True)
        if not raw:
            continue
        sents = _sentences(_readable(raw))
        if len(sents) >= 3:                       # khaali/junk page nahi
            pages.append((host.replace("www.", ""), sents))
    return pages


def _synthesize(query: str, items, pages) -> str:
    """📖 SAMAJH: snippets + parhe-huye pages ke jumle → SMART-score →
    multi-source jawab (source-domains ke sath). Koi AI API nahi — ye
    extractive-samajh hai: topic-hit + copula (asli proose) + intro-position
    (article ke pehle jumle = tareef-wala) — reference-kachra neeche rehta."""
    qtok = _topic_tokens(query)
    if not qtok:
        return ""
    cands = []                                    # (score, source, jumla)
    for host, sents in (pages or []):
        for idx, s in enumerate(sents):
            low = s.lower()
            sc = sum(2 for w in qtok if w in low)
            if not sc:
                continue
            # 🧠 asli proose (is/are/refers...) + INTRO-bonus (pehle jumle)
            if _COPULA_RX.search(s):
                sc += 2
            sc += max(0, 3 - idx * 0.15)
            cands.append((sc, host, s))
    for it in (items or [])[:6]:
        t = re.sub(r"\s+", " ", (it or "")).strip()
        if not t or _JUNK_RX.search(t):
            continue
        body = t.partition(" — ")[2].strip() or t
        if len(body) < 30:
            continue
        low = body.lower()
        sc = sum(1 for w in qtok if w in low) + \
            (2 if _COPULA_RX.search(body) else 0) + 1   # snippet pos-bonus
        if sc:
            cands.append((sc, "search", body))
    if not cands:
        return ""
    cands.sort(key=lambda x: (-x[0], len(x[2])))
    picked, used, domains = [], set(), []
    for sc, src, s in cands:
        key = re.sub(r"[^a-z0-9]", "", s.lower())[:50]
        if key in used:
            continue
        used.add(key)
        picked.append((src, s))
        if src != "search" and src not in domains:
            domains.append(src)
        if len(picked) >= 5:
            break
    if not picked:
        return ""
    body_txt = " ".join(s[:230] for _, s in picked)
    out = "Web (live padhai): " + body_txt
    if domains:
        out += " (manba: %s)" % ", ".join(domains[:3])
    return out


# ----------------------------------------------------------------------
# 📚 WIKI-DEEP-READ (reliable 'parho-samjho' — search + poora article)
# ----------------------------------------------------------------------
def _wiki_deep(query: str, deadline: float = None):
    """📖 PERPLEXITY-STYLE (NO API-key): wiki-search page-parhi → top titles →
    POORE article-pages parho (_read_pages) → jumle topic-rank → jawab.
    en.wikipedia.org whitelist me + bot-friendly — ye engine SAB networks
    par chalta hai (DDG/Bing bot-walls ka jawab). Return: text ya None."""
    qq = _topic_query(query)
    if not qq:
        return None
    api = ("https://en.wikipedia.org/w/api.php?action=query&format=json"
           "&list=search&srlimit=4&srsearch=" + urllib.parse.quote(qq))
    d = _fetch_json(api, timeout=5.0 if deadline else 10.0)
    titles = [it.get("title", "") for it in
              ((d or {}).get("query") or {}).get("search", [])]
    titles = [t for t in titles if t]
    if not titles:
        return None
    urls = ["https://en.wikipedia.org/wiki/" +
            urllib.parse.quote(t.replace(" ", "_"), safe="_()%.~")
            for t in titles[:3]]
    pages = _read_pages(urls, deadline=deadline, limit=3)
    if not pages:
        return None
    syn = _synthesize(query, [], pages)
    return (syn or None)


def _wiktionary(word: str, deadline: float = None):
    """📖 Single-word (anjaan lafz) ki definition — en.wiktionary (whitelist,
    NO API-key). Return: text ya None (entry na ho to)."""
    if not word:
        return None
    api = ("https://en.wiktionary.org/w/api.php?action=query&format=json"
           "&prop=extracts&exintro=1&explaintext=1&redirects=1&titles=" +
           urllib.parse.quote(word.strip()))
    d = _fetch_json(api, timeout=5.0 if deadline else 10.0)
    pages = (d or {}).get("query", {}).get("pages", {})
    # 1-2 harf ke lafz ('h') ki entry chhoti hoti hai — 60 nahi 20
    min_len = 20 if len(word.strip()) <= 2 else 60
    found = None
    for _pid, p in pages.items():
        ex = (p.get("extract") or "").strip()
        if "may refer to" in ex[:80] or len(ex) < min_len:
            continue
        found = ex
        break
    # 🆕 1-2 harf ('h'): intro khali aata hai (matan sections me bandha hai) →
    # poora plaintext parho, section-headers (Letter/See also/…) hatao
    if not found and len(word.strip()) <= 2:
        api2 = api.replace("&exintro=1&", "&")
        d2 = _fetch_json(api2, timeout=5.0 if deadline else 10.0)
        for _pid, p in ((d2 or {}).get("query", {}).get("pages", {})
                        or {}).items():
            ex = (p.get("extract") or "").strip()
            lines = [l for l in ex.splitlines() if l.strip() and not re.match(
                r"(?i)^(see also|etymology.*|letter|pronunciation|"
                r"translingual|english|symbol|references|further reading)$"
                r"|^\([^)]{0,30}\)[: ]", l.strip())]
            ex = "\n".join(lines).strip()
            if "may refer to" in ex[:80] or len(ex) < min_len:
                continue
            found = ex
            break
    if not found:
        return None
    # chhote lafz ('h') par sirf pehla jumla — aage sections alag maudit hain
    sents = _sentences(found)[:1 if len(word.strip()) <= 2 else 2]
    if sents:
        return "Web (wiktionary): " + " ".join(sents) + \
               " (manba: en.wiktionary.org)"
    return None


# 🌏 APNA Roman-Urdu→English lexicon (brain ki apni hifz — koi API/translator/
# AI nahi!): Roman-Urdu sawal DDG par English-topic se behtar milta hai →
# pehli search khali aye to translated-query se doosri koshish
_UR_EN = {
    "dimagh": "brain", "dimaq": "brain", "dimaagh": "brain",
    "cheez": "thing", "cheezein": "things", "chiz": "thing",
    "bijli": "electricity", "roshni": "light", "awaz": "sound", "awaaz": "sound",
    "zameen": "earth", "aasman": "sky", "suraj": "sun", "chaand": "moon",
    "sitara": "star", "hawa": "wind", "pani": "water", "aag": "fire",
    "samandar": "ocean", "barish": "rain", "dhoop": "sunlight",
    "ped": "tree", "phool": "flower", "fasal": "crop", "khet": "farm",
    "janwar": "animal", "khoon": "blood", "haddi": "bone", "sehat": "health",
    "bimari": "disease", "dawa": "medicine", "dard": "pain",
    "khana": "food", "chai": "tea", "mohabbat": "love",
    "duniya": "world", "mulk": "country", "shehar": "city", "gaon": "village",
    "ilm": "science", "taareekh": "history", "tareekh": "history",
    "dil": "heart", "khel": "game", "khilona": "toy", "gari": "car",
    "jahaaz": "airplane", "kashti": "ship", "zanjeer": "chain",
    "machli": "fish", "billi": "cat", "kutta": "dog", "parinda": "bird",
    "taare": "stars", "mausam": "weather", "kaam": "work",
}


def _translated_tokens(q: str):
    """Topic-tokens jin me apna lexicon match hua (Roman-Urdu → English)."""
    return [_UR_EN[w] for w in _topic_tokens(q) if w in _UR_EN]


# 🆕 bare-numbers ka apna human-form (koi API nahi): search engines par
# "1000000000+" jaisa kachra-query achha nahi milta — "1 billion" milta hai.
_NUM_WORDS = ((10**12, "trillion"), (10**9, "billion"), (10**6, "million"),
              (10**3, "thousand"))


def _humanize_num(q: str):
    """'1000000000+' → '1 billion+', '250000' → '250 thousand' (sirf 4+ digit
    runs badalte hain — chhote numbers/vocab-shabd jaise hain waise rehte)."""
    def _one(m):
        s = m.group(1).lstrip("0") or "0"
        n = int(s)
        for div, name in _NUM_WORDS:
            if n >= div and n % div == 0:
                v = n // div
                if 1 <= v < 1000:
                    return "%s %s" % (v, name)
        return s
    return re.sub(r"\b(\d{4,})\b", _one, (q or ""))


def _search(query: str):
    """⚡ FAST chain: DDG-lite → Google → Bing (sab page-READ, NO API/key).
    Return: (polished_text | None, urls, raw_items) — urls PAGE-READING ke
    liye (Perplexity-style parho-samjho); anti-bot par agla engine."""
    qq = _topic_query(query)
    if not qq:
        return None, [], []
    got = None
    # ⚡ 5-engine chain (sab page-READ, NO API): DDG-lite → DDG-html →
    # Mojeek → Google → Bing
    for fn in (_ddg, _ddg_html, _mojeek, _google, _bing):
        try:
            got = fn(qq)
        except Exception:
            got = None
        if got:
            break
    if not got:
        return None, [], []
    items, urls = got
    text = None
    if _results_relevant(query, items):
        text = _polish_web(items, query)
        if text and not _faith_clean(text):
            text = None
        # 🚫 junk-SHAPE: snippet-jawab khud list/discography/spam-shape me ho
        # to wo asli jawab nahi ('List of songs…' ka jawab nahi banta)
        if text and (_JUNK2_RX.search(text) or _SPAM_RX.search(text)):
            text = None
    return text, urls, items


def research(prompt: str):
    """Live ilm research — (text ya None). Islamic sawal par None + log.
    📖 PERPLEXITY-STYLE (NO AI API/key — sirf page-reading):
      1) search (DDG→Google→Bing) → snippets + result-URLs
      2) top pages GUP-GUP PARHO (whitelist-only, net_guard on)
      3) SAMJHO: jumlon ko topic-rank karo, multi-source combine
      4) jawab (manba-domains ke sath) → yaad me save (agli dafa brain khud)
    ⏱️ TOTAL budget 15s — chat kabhi hang nahi."""
    key = re.sub(r"\s+", " ", (prompt or "").lower()).strip()
    if not key:
        return None
    if is_sacred(prompt):     # 🕌 Islamic → internet NAHI, books se hoga
        net_guard._log("RESEARCH-SKIP-SACRED %r (books-only)" % key[:60])
        return None
    if key in CACHE:
        return CACHE[key]
    _t0 = time.time()
    def _budget():
        return (time.time() - _t0) < 15.0
    dd = _t0 + 15.0                     # ⏰ deadline — page-read bhi uske andar
    # 🆕 bare-numbers ("1000000000+") pehle insani-shakal me ("1 billion+")
    hum = _humanize_num(key)
    text, urls, items = _search(hum)
    if not text and hum != key and _budget():
        text2, urls2, items2 = _search(key)     # asli roop par bhi ek koshish
        urls, items, text = (urls or urls2), (items or items2), text2
    # 📖 PAGE-READ: snippets se URL mila → poora page PARHO → samjho
    if urls and _budget():
        pages = _read_pages(urls, deadline=dd)
        if pages:
            syn = _synthesize(key, items, pages)
            if syn and _faith_clean(syn):
                text = syn               # page-read wala jawab behtar hai
            elif text:
                text = text + " (manba: %s)" % ", ".join(
                    d for d, _ in pages[:2])
    # 🚫 FAKE-JAWAB guard: search-jawab off-topic (topic-words gayab) ya
    # SPAM-shape (shorts/trailer/hashtag) → None, neeche wale asli engines
    # (wiki-deep/wiktionary) phir koshish karenge; junk YAAD me bhi nahi jata
    if text and (_SPAM_RX.search(text) or not _coverage_ok(text, key)):
        text = None
    # 📚 WIKI-DEEP-READ: (a) jawab NAHI mila, ya (b) mila magar KAMZOR-shakal
    # (sawal-snippet/title-list) — asli prose tab bhi wiki-deep se behtar
    if _budget() and (not text or _weak_text(text)):
        wdeep = _wiki_deep(key, deadline=dd)
        if wdeep and _faith_clean(wdeep) and not _weak_text(wdeep):
            text = wdeep
    # 📖 SINGLE-WORD (anjaan lafz — 'h' jaisa ek-harf bhi): wiktionary
    if not text and _budget():
        raws = re.findall(r"[a-z]+", key)
        t1 = _topic_tokens(key)
        word = t1[0] if len(t1) == 1 else (raws[0] if len(raws) == 1 else None)
        if word:
            wd = _wiktionary(word, deadline=dd)
            if wd and _faith_clean(wd):
                text = wd
    if not text and _budget():           # 🌏 apna lexicon: Roman-Urdu→English
        tws = _translated_tokens(key)
        if tws and _budget():
            text = _search(" ".join(tws) + " explained")[0]
    if not text and _budget():           # wiki-summary fallback (deadline-bound)
        text = _wiki(hum, deadline=dd)
    # 🚫 FINAL GUARDS (HAR raste ke jawab par — search/page-read/wiki sab):
    # spam-shape + list/discography-kachra + off-topic coverage — kuch bhi
    # fake/kachra jawab YAAD me nahi jata, imandari behtar hai
    if text and (_SPAM_RX.search(text) or _JUNK2_RX.search(text)
                 or not _coverage_ok(text, key)):
        text = None
    if text and _faith_clean(text):
        _remember(text, key)             # ASLI sawal ki key par memory
        CACHE[key] = text
        return text
    return None


if __name__ == "__main__":
    if len(sys.argv) > 1:
        out = research(" ".join(sys.argv[1:]))
        print(out if out else "✗ live se kuch na mila")
    else:
        print('istemaal: python model\\live_research.py "sawal"')
