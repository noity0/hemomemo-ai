r"""
📜 install_sacred_texts.py — Quran (SARE ZUBANOAN) + 7 Hadith BOOK INSTALLER

Kam:
  A) Quran: 440+ translations, 98 languages (fawazahmed0/quran-api @1) download
     → knowledge/quran/translations/{lang}-{translator}.min.json
  B) Hadith: 7 books (Bukhari, Muslim, Nasai, Abu Dawud, Tirmidhi, Ibn Majah,
     Muwatta Malik) × languages (ara, eng, urd) (fawazahmed0/hadith-api @1,
     data sunnah.com se) → knowledge/hadith/
  C) Masters: data/quran_master.json, data/bukhari_master.json,
     data/hadith_master.json (pehle khaali '{}' the — ab sach)
  D) Korpus: English hadith → data/corpus_big/hadith_{book}_english_full.txt
     (Sawal/Jawab style — chat yaad-dahai me sada istemal)
  E) SCAN: tamam nai files me Qadiani/Ahmadi sources ka check (source_policy)
  F) Report: knowledge/_install/install_report.json

RESUME: files jo theek hain wo dubara download NAHI honge. Dobara chalao.
Qadiani QAWAIDA: harvest/source_policy.py me — koi Qadiani source/translator Nahi.
Run:  python scripts\install_sacred_texts.py
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
os.chdir(ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from harvest.source_policy import (  # noqa: E402
    BANNED_AUTHOR_RX, FORBIDDEN_RX, assert_clean, host_allowed,
    scan_files as policy_scan)
from harvest.purify import keywords, sanitize  # noqa: E402

RAW = "https://raw.githubusercontent.com"
CDN = "https://cdn.jsdelivr.net"
Q_EDITIONS_URL = RAW + "/fawazahmed0/quran-api/1/editions.json"
Q_FILE = RAW + "/fawazahmed0/quran-api/1/editions/{id}.min.json"
Q_FILE_ALT = RAW + "/fawazahmed0/quran-api/1/editions/{id}.json"
Q_CDN = CDN + "/gh/fawazahmed0/quran-api@1/editions/{id}.min.json"
H_FILE = RAW + "/fawazahmed0/hadith-api/1/editions/{lang}-{book}.min.json"
H_FILE_ALT = RAW + "/fawazahmed0/hadith-api/1/editions/{lang}-{book}.json"
H_CDN = CDN + "/gh/fawazahmed0/hadith-api@1/editions/{lang}-{book}.min.json"

QS = os.path.join(ROOT, "knowledge", "quran", "translations")
HS = os.path.join(ROOT, "knowledge", "hadith")
INSTALL_DIR = os.path.join(ROOT, "knowledge", "_install")
LOG_PATH = os.path.join(INSTALL_DIR, "install.log")

HADITH_BOOKS = ["bukhari", "muslim", "abudawud", "tirmidhi", "nasai",
                "ibnmajah", "malik"]
HADITH_LABELS = {
    "bukhari": "Sahih al-Bukhari", "muslim": "Sahih Muslim",
    "abudawud": "Sunan Abi Dawud", "tirmidhi": "Jami at-Tirmidhi",
    "nasai": "Sunan an-Nasai", "ibnmajah": "Sunan Ibn Majah",
    "malik": "Muwatta Malik",
}
HADITH_LANGS = ["ara", "eng", "urd"]

_T0 = time.time()
_STATS = {"quran_ok": 0, "quran_skip": 0, "quran_err": 0, "quran_banned": 0,
          "hadith_ok": 0, "hadith_err": 0, "forbidden_hits": {},
          "bytes": 0}


def log(msg):
    line = "[%6.1fs] %s" % (time.time() - _T0, msg)
    print(line, flush=True)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


# ---------------------------------------------------------------- helper
def fetch(url, timeout=90, tries=3):
    """URL se bytes; min.json fail → .json fallback → jsdelivr fallback."""
    candidates = [url]
    if url.endswith(".min.json"):
        candidates.append(url[:-9] + ".json")
    else:
        candidates.append(url[:-5] + ".min.json")
    out = []
    for u in candidates:
        if not host_allowed(u):
            continue
        out.append(u)
    # jsdelivr fallback (agar raw fail): edition path → cdn
    cdn_url = url.replace(RAW + "/fawazahmed0/quran-api/1/", CDN + "/gh/fawazahmed0/quran-api@1/")
    cdn_url = cdn_url.replace(RAW + "/fawazahmed0/hadith-api/1/", CDN + "/gh/fawazahmed0/hadith-api@1/")
    if cdn_url != url:
        out.append(cdn_url)
    last = None
    for u in out:
        for attempt in range(tries):
            try:
                req = urllib.request.Request(u, headers={"User-Agent": "HMHS-DigitalBrain/1.0"})
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    return r.read()
            except (urllib.error.HTTPError, urllib.error.URLError, OSError) as e:
                last = e
                if isinstance(e, urllib.error.HTTPError) and e.code in (404, 403):
                    break                    # ye URL exist nahi karta → agla
                time.sleep(1.0 + attempt)
        # agla URL
    raise RuntimeError("fetch fail %s (%s)" % (url, last))


def valid_json(raw):
    try:
        return json.loads(raw.decode("utf-8", errors="strict"))
    except Exception:
        return None


def save_bytes(path, raw):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(raw)
    _STATS["bytes"] += len(raw)


def file_bad_text(raw):
    """Raw json text me forbidden words? (match str ya None)"""
    try:
        m = FORBIDDEN_RX.search(raw.decode("utf-8", errors="ignore"))
        return m.group(0) if m else None
    except Exception:
        return None


# ---------------------------------------------------------------- QURAN
def build_quran():
    os.makedirs(QS, exist_ok=True)
    log("QURAN: edition list download ...")
    raw = fetch(Q_EDITIONS_URL)
    editions = json.loads(raw.decode("utf-8"))
    log("QURAN: %d editions mile" % len(editions))
    index = []
    for key, meta in sorted(editions.items()):
        name = meta.get("name", key.replace("_", "-"))
        author = meta.get("author", "")
        lang = meta.get("language", "")
        meta_text = "%s %s %s %s" % (key, name, author, meta.get("comments", ""))
        # transliteration-only variants (-la / -lad) hatao (translation khud hai)
        if re.search(r"[_-](la|lad)\d*$", key):
            _STATS["quran_skip"] += 1
            continue
        # Qadiani/Rashad filtras — meta, id aur author sab check
        banned_reason = None
        if BANNED_AUTHOR_RX.search(meta_text):
            banned_reason = "meta-fail (%s)" % (author or name)
        if FORBIDDEN_RX.search(meta_text):
            banned_reason = "meta-fail (forbidden word)"
        if banned_reason:
            _STATS["quran_banned"] += 1
            log("QURAN BANNED (%s): %s" % (banned_reason, name))
            continue
        path = os.path.join(QS, name + ".min.json")
        if os.path.exists(path) and os.path.getsize(path) > 2000:
            try:
                with open(path, "rb") as f:
                    if valid_json(f.read()) is not None:
                        _STATS["quran_skip"] += 1
                        index.append({"id": name, "author": author,
                                      "language": lang, "file": path})
                        continue
            except OSError:
                pass
        u = Q_FILE.format(id=name)
        try:
            raw = fetch(u)
        except Exception as e:
            _STATS["quran_err"] += 1
            log("QURAN ERR %s: %s" % (name, str(e)[:90]))
            continue
        hit = file_bad_text(raw)
        if hit:
            _STATS["quran_banned"] += 1
            _STATS["forbidden_hits"]["quran/" + name] = hit
            log("QURAN FORBIDDEN TEXT %s: %s" % (name, hit))
            continue
        if valid_json(raw) is None:
            _STATS["quran_err"] += 1
            log("QURAN BAD-JSON %s" % name)
            continue
        save_bytes(path, raw)
        _STATS["quran_ok"] += 1
        index.append({"id": name, "author": author, "language": lang,
                      "file": path})
        if _STATS["quran_ok"] % 25 == 0:
            log("QURAN progress: %d save | skip %d | err %d" % (
                _STATS["quran_ok"], _STATS["quran_skip"], _STATS["quran_err"]))
    # index file (editions ki poori fehrist)
    idx_path = os.path.join(ROOT, "knowledge", "quran", "editions_index.json")
    langs = {}
    for e in index:
        langs.setdefault(e["language"], 0)
        langs[e["language"]] += 1
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump({"total": len(index), "languages": len(langs),
                   "languages_count": langs, "editions": index}, f,
                  ensure_ascii=False)
    log("QURAN DONE: %d saved (skip %d, err %d, banned %d) | languages %d" % (
        _STATS["quran_ok"], _STATS["quran_skip"], _STATS["quran_err"],
        _STATS["quran_banned"], len(langs)))
    return index


# ---------------------------------------------------------------- HADITH
def fetch_json_from_data(data):
    """Hadith-api book json → (list_of_hadith_dict) defensive parse."""
    if isinstance(data, dict):
        h = data.get("hadiths")
        if isinstance(h, list):
            return h
    return []


def build_hadith():
    os.makedirs(HS, exist_ok=True)
    index = []
    for lang in HADITH_LANGS:
        for book in HADITH_BOOKS:
            fname = "%s-%s.min.json" % (lang, book)
            path = os.path.join(HS, fname)
            if os.path.exists(path) and os.path.getsize(path) > 20000:
                cnt = None
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        cnt = len(fetch_json_from_data(json.load(f)))
                except Exception:
                    cnt = None
                index.append({"lang": lang, "book": book, "file": path,
                              "hadiths": cnt})
                continue
            for u in (H_FILE.format(lang=lang, book=book),
                      H_FILE_ALT.format(lang=lang, book=book)):
                try:
                    raw = fetch(u)
                    break
                except Exception:
                    raw = None
            if raw is None:
                log("HADITH MISSING: %s" % fname)
                continue
            hit = file_bad_text(raw)
            if hit:
                _STATS["forbidden_hits"]["hadith/" + fname] = hit
                log("HADITH FORBIDDEN %s: %s" % (fname, hit))
                continue
            data = valid_json(raw)
            if data is None:
                log("HADITH BAD-JSON %s" % fname)
                continue
            n = len(fetch_json_from_data(data))
            save_bytes(path, raw)
            index.append({"lang": lang, "book": book, "file": path,
                          "hadiths": n})
            log("HADITH %s → %d hadiths (%d KB)" % (fname, n, len(raw) // 1024))
    # hadith index file
    idx_path = os.path.join(HS, "hadith_index.json")
    with open(idx_path, "w", encoding="utf-8") as f:
        json.dump({"books": HADITH_LABELS, "languages": HADITH_LANGS,
                   "files": index}, f, ensure_ascii=False)
    log("HADITH DONE: %d files" % len(index))
    return index


# ---------------------------------------------------------------- MASTERS
def build_masters(quran_index, hadith_index):
    quran_master = {
        "name": "Al-Quran (complete + translations)",
        "arabic_editions": [e["id"] for e in quran_index if e["id"].startswith("ara")],
        "translations": len([e for e in quran_index if not e["id"].startswith("ara")]),
        "files": [os.path.relpath(e["file"], ROOT) for e in quran_index],
        "index_file": "knowledge/quran/editions_index.json",
        "policy": "sirf pure-sunni sources (harvest/source_policy.py)",
        "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(os.path.join(ROOT, "data", "quran_master.json"), "w",
              encoding="utf-8") as f:
        json.dump(quran_master, f, ensure_ascii=False, indent=1)

    # bukhari_master (pehle '{}' khaali tha)
    buk = [h for h in hadith_index if h["book"] == "bukhari"]
    bukhari_master = {
        "name": HADITH_LABELS["bukhari"],
        "languages": {h["lang"]: h.get("hadiths") for h in buk},
        "files": [os.path.relpath(h["file"], ROOT) for h in buk],
        "updated": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(os.path.join(ROOT, "data", "bukhari_master.json"), "w",
              encoding="utf-8") as f:
        json.dump(bukhari_master, f, ensure_ascii=False, indent=1)

    hadith_master = {"books": HADITH_LABELS, "count": len(hadith_index),
                     "files": [{"lang": h["lang"], "book": h["book"],
                                "hadiths": h.get("hadiths"),
                                "file": os.path.relpath(h["file"], ROOT)}
                               for h in hadith_index],
                     "updated": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(os.path.join(ROOT, "data", "hadith_master.json"), "w",
              encoding="utf-8") as f:
        json.dump(hadith_master, f, ensure_ascii=False, indent=1)
    log("MASTERS: quran/bukhari/hadith master.json likhe gaye")


# ---------------------------------------------------------------- CORPUS
def _hadith_text_list(data):
    """(num, text) list — defensive."""
    out = []
    for h in fetch_json_from_data(data):
        if not isinstance(h, dict):
            continue
        t = h.get("text") or ""
        ent = h.get("englishEntry") or {}
        if not t and isinstance(ent, dict):
            t = ent.get("text") or ""
        if not t:
            continue
        try:
            num = h.get("hadithnumber") or h.get("arabicnumber") or ""
        except Exception:
            num = ""
        out.append((str(num), str(t)))
    return out


def build_corpus(hadith_index):
    """English hadith → data/corpus_big/hadith_{book}_english_full.txt
    (Sawal:/Jawab: style — chat yaad me turant istemal hota hai)"""
    big = os.path.join(ROOT, "data", "corpus_big")
    os.makedirs(big, exist_ok=True)
    wrote = []
    for h in hadith_index:
        if h["lang"] != "eng":
            continue
        book = h["book"]
        try:
            with open(h["file"], "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            log("CORPUS read-err %s" % book)
            continue
        items = _hadith_text_list(data)
        lines = []
        for num, t in items:
            t = sanitize(t)
            if len(t) < 25:
                continue
            label = "%s %s" % (HADITH_LABELS[book], num)
            kw = keywords(t, 4)
            lines.append("Sawal: %s hadith %s\nJawab: %s: %s" % (
                kw, book.lower(), label, t))
        path = os.path.join(big, "hadith_%s_english_full.txt" % book)
        head = ("# %s (English, sunnah.com data) — HMHS corpus\n"
                "# installs: scripts/install_sacred_texts.py\n" % HADITH_LABELS[book])
        with open(path, "w", encoding="utf-8") as f:
            f.write(head + "\n".join(lines) + "\n")
        wrote.append((book, len(items), os.path.getsize(path)))
        log("CORPUS %s: %d hadiths → %s" % (book, len(items),
                                            os.path.relpath(path, ROOT)))
    return wrote


# ---------------------------------------------------------------- SCAN+REPORT
def final_scan():
    res = policy_scan(QS)
    _STATS["forbidden_hits"].update({"quran/" + k: v
                                     for k, v in res["hits"].items()})
    log("SCAN quran translations: %d files, hits %d, bytes %d" % (
        res["scanned"], len(res["hits"]), res["bytes"]))
    return res


def main():
    os.makedirs(INSTALL_DIR, exist_ok=True)
    log("INSTALL START — Quran(all languages) + 7 Hadith books")
    quran_index = build_quran()
    hadith_index = build_hadith()
    build_masters(quran_index, hadith_index)
    wrote = build_corpus(hadith_index)
    final_scan()
    _STATS["corpus"] = [{"book": b, "hadiths": n, "bytes": sz} for b, n, sz in wrote]
    _STATS["secs"] = round(time.time() - _T0, 1)
    report = os.path.join(INSTALL_DIR, "install_report.json")
    with open(report, "w", encoding="utf-8") as f:
        json.dump(_STATS, f, ensure_ascii=False, indent=1)
    log("REPORT → %s" % os.path.relpath(report, ROOT))
    log("INSTALL FINISHED in %ss | quran %d | hadith %d | corpus %d | bytes %.1f MB" % (
        _STATS["secs"], _STATS["quran_ok"], _STATS["hadith_ok"],
        len(wrote), _STATS["bytes"] / 1e6))


if __name__ == "__main__":
    main()
