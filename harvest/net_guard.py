"""
🌐 net_guard.py — Hemomemo AI LIVE-NET FIREWALL (deny-by-default)

Qanoon (koi tabdeeli nahi):
  1. LIVE internet ON hai — ilm hasil karne ke liye (harvester)
  2. Whitelist ke SIWA kisi bhi jagah request chi jaye — BLOCK + log
     (deny-by-default: poora internet, whitelist se bahar)
  3. HARD-BLOCK (kabhi allow nahi):
     - Doosre AI models / APIs: openai, anthropic, gemini, groq, mistral,
       cohere, deepseek, together, openrouter, x.ai/grok, replicate,
       huggingface (model-hub), ollama registry, qwen/dashscope, zhipu ...
     - Qadiani/Ahmadi sites: alislam.org, aaiil.org, ahmadiyya*, qadian*
  4. Scope: SIRF HMHS ka process (system-wide firewall NAHI — user ke
     doosre apps par asar nahi)

Use (har code me jo net chhuo):
    from harvest import net_guard
    net_guard.install()          # ek dafa — urllib.request.urlopen guarded
    ok, why = net_guard.check(url)

Blocked har call log me aati hai: harvest/net_guard.log
"""

import datetime
import os
import sys
import re
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
LOG_PATH = os.path.join(ROOT, "harvest", "net_guard.log")

# ✅ Whitelist — sirf ye hosts (deny-by-default baqi sab)
ALLOWED_HOSTS = (
    "raw.githubusercontent.com",
    "cdn.jsdelivr.net",
    "cdn.islamic.network",
    "api.alquran.cloud",
    "api.quran.com",
    "quran.com",
    "sunnah.com",
    "api.sunnah.com",
    "hadithapi.com",
    "clearquran.com",
    "islamqa.info",
    "quranx.com",
    "tanzil.net",
    "archive.org",        # 📚 hadith-corpus downloads (fetch_hadith.py source)
    "wikipedia.org",
    "api.wikimedia.org",
    # 🔍 general web-search pages (NO API-keys, sirf read — deta hi details);
    #    in me koi AI-model service NAHI hai — net_guard ki whitelist hi rehta
    "google.com",
    "gstatic.com",
    "duckduckgo.com",
    "bing.com",
    # SEARCH-API + GMAIL (user-qanoon 2026: search/email APIs ALLOWED;
    # AI-platform APIs HARD-BLOCK - BANNED_AI_RX whitelist-se-PEHLE chalta
    # hai, isliye googleapis.com par generativelanguage phir bhi band rahega)
    "googleapis.com",          # Google CSE customsearch JSON (search-API)
    "api.bing.microsoft.com",  # Bing Web-Search v7 (keyed)
    "api.search.brave.com",    # Brave Search API (keyed)
    "imap.gmail.com",          # Gmail READ (imaplib)
    "smtp.gmail.com",          # Gmail SEND (smtplib)
    "mail.google.com",         # Gmail web
    "mojeek.com",         # 🔍 apna-index search (no API, bot-friendly)
    # 📖 knowledge PAGE-READ (research-engine 'parho-samjho' — Perplexity-style
    #    reading, NO AI API): in par search-milay result-pages parhe jate hain
    "britannica.com", "merriam-webster.com", "dictionary.com",
    "wiktionary.org", "wikimedia.org", "w3schools.com",
    "geeksforgeeks.org", "stackoverflow.com", "mozilla.org",
    "nationalgeographic.org", "nationalgeographic.com", "livescience.com",
    "space.com", "nature.com", "sciencedaily.com", "history.com",
    "khanacademy.org", "investopedia.com", "healthline.com",
    "mayoclinic.org", "webmd.com", "stanford.edu", "nasa.gov",
    "howstuffworks.com", "britannica.com",
    # 🎮 games-knowledge (Minecraft + games-wiki — sirf READ, koi AI-API nahi)
    "minecraft.wiki", "fandom.com",
)

# ❌ HARD-BLOCK: doosre AI-model services/model-hubs (kisi bhi shakal me)
BANNED_AI_RX = re.compile(
    r"(?i)openai\.com|anthropic\.com|claude|gemini|generativelanguage"
    r"|googleapis\.com/speech|ai\.google\.dev|cohere\.com|mistral\.ai"
    r"|groq\.com|openrouter\.ai|together\.(ai|xyz)|deepseek|moonshot"
    r"|dashscope|aliyuncs\.com|zhipu|bigmodel\.cn|qwen"
    r"|huggingface\.co|replicate\.com|perplexity|elevenlabs|stability\.ai"
    r"|runwayml|fireworks\.ai|aimlapi\.com|api2d\.com|open\.ai|sk-ant|sk-proj"
)

# ❌ HARD-BLOCK: Qadiani/Ahmadi + gair-pak sources
BANNED_FAITH_RX = re.compile(
    r"(?i)alislam\.org|aaiil\.org|ahmadiyya|qadian|mirza[ -]?ghulam"
    r"|mirzai|lahore-ahmadi"
)

# ❌ LOCAL AI daemons (ollama/lmstudio waghera) bhi block — koi model hai hi nahi
BANNED_LOCAL_RX = re.compile(
    r"(?i)localhost:11434|127\.0\.0\.1:11434|registry\.ollama\.ai|ollama\.com"
    r"|lmstudio|localhost:1234|127\.0\.0\.1:1234|localhost:5001"
)

_BLOCK_LOG_LOCK = None
_ORIGINAL_URLOPEN = None


def _log(line: str):
    """Chhota log (bade ho to purge kar do)."""
    try:
        if os.path.exists(LOG_PATH) and os.path.getsize(LOG_PATH) > 1_000_000:
            os.remove(LOG_PATH)
    except OSError:
        pass
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write("%s %s\n" % (datetime.datetime.now().isoformat(timespec="seconds"),
                                 line))
    except OSError:
        pass


def check(url: str):
    """(ok, reason) — True = allow; False = HARD-BLOCK ya whitelist-bahir."""
    if not url:
        return False, "empty-url"
    try:
        host = urllib.parse.urlparse(url).netloc.lower()
        full = (host + urllib.parse.urlparse(url).path).lower()
    except ValueError:
        return False, "bad-url"
    m = BANNED_FAITH_RX.search(full)
    if m:
        return False, "FAITH-BLOCK (%s)" % m.group(0)
    m = BANNED_AI_RX.search(full)
    if m:
        return False, "AI-BLOCK (%s)" % m.group(0)
    # 🌐 Hemomemo ki APNI API-server port (127.0.0.1:8790/8791) — apna hi ghar:
    # ye Hemomemo ka khud ka local API hai (koi doosra platform nahi)
    if host in ("127.0.0.1:8790", "localhost:8790", "127.0.0.1:8791",
                "localhost:8791"):
        return True, "allowed (Hemomemo apni API-port)"
    if BANNED_LOCAL_RX.search(full):
        return False, "LOCAL-AI-BLOCK"
    # whitelist (suffix match) — port ka bachav
    if not any(host == h or host.endswith("." + h) for h in ALLOWED_HOSTS):
        return False, "NOT-WHITELISTED (deny-by-default)"
    return True, "allowed"


def guarded_urlopen(url, *args, **kwargs):
    """urllib.request.urlopen ka guard-wrapped badal."""
    target = url
    try:
        if not isinstance(target, str):
            target = target.full_url          # Request object case
    except AttributeError:
        pass
    ok, why = check(str(target))
    if not ok:
        _log("BLOCK url=%s reason=%s" % (str(target)[:180], why))
        raise urllib.error.URLError("Hemomemo AI-NET-GUARD BLOCKED: %s" % why)
    _log("ALLOW url=%s" % (str(target)[:180],))
    return _ORIGINAL_URLOPEN(url, *args, **kwargs)


def install():
    """Ek dafa call: process ke darmiyan har urllib call guard se guzregi."""
    global _ORIGINAL_URLOPEN
    if _ORIGINAL_URLOPEN is None:
        _ORIGINAL_URLOPEN = urllib.request.urlopen
        urllib.request.urlopen = guarded_urlopen
        _log("GUARD INSTALLED (whitelist-only, AI-models+Qadiani hard-block)")
    return True


def status() -> dict:
    """Firewall ki halat (hub status/report ke liye)."""
    return {
        "mode": "LIVE (whitelist deny-by-default)",
        "allowed_hosts": list(ALLOWED_HOSTS),
        "hard_blocks": ["AI-model APIs", "Qadiani/Ahmadi sites",
                        "local AI daemons (ollama/lmstudio)"],
        "guard_on": _ORIGINAL_URLOPEN is not None,
        "log": os.path.relpath(LOG_PATH, ROOT),
    }


if __name__ == "__main__":
    install()
    tests = [
        ("https://raw.githubusercontent.com/fawazahmed0/hadith-api/1/x.json", True),
        ("https://api.openai.com/v1/chat/completions", False),
        ("https://alislam.org/quran", False),
        ("https://islamqa.info/en/answers/1", True),
        ("https://najmalilm.example.com/a", False),
        ("http://127.0.0.1:11434/api/tags", False),
    ]
    for u, want in tests:
        ok, why = check(u)
        mark = "OK " if ok == want else "FAIL"
        print("%s %-62s -> %s (%s)" % (mark, u[:60], ok, why))
