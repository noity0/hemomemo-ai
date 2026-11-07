"""
👤 server/accounts.py — HEMOMO AI API ke PER-USER ACCOUNTS (100% local)

User qanoon (saaf-saf): "har bande ki APNI API hogi — Hemomemo AI jisse wo
copy kar paye aur usse koi bhi kaam karwa paye. API is se LINKED hai —
Hemomemo AI API. NO any platform API of the world."

  - SIGN-UP / SIGN-IN: email (Gmail bhi) + password — SAB KUCH ISI PC par
    (data/genone_users.json). ⚠️ Google/Facebook waala asli OAuth JAAN-BOOJH
    kar NAHI hai: asli Google sign-in ko Google ki OAuth API chahiye — aur
    user ka pakka qanoon hai "no any platform API of the world". Is liye ye
    LOCAL sign-in hai: aap apna Gmail/Email + apna password yahin rakhte hain
    — Google ko koi call NAHI jata, koi platform API NAHI lagti.
  - HAR BANDE KI APNI KEYS: har `hemo…` key uski Hemomemo AI API key hai
    (X-Hemomemo-Key header). 🎫 FREE HADD: ek account sirf **3 keys** bana
    sakta hai (user qanoon). Har key poora random (secrets.token_hex) aur
    SACH-MUCH isi local DigitalBrain API se juri hoti hai — kisi doosri
    AI/platform se koi taluq nahi.
  - PASSWORD KABHI PLAIN NAHI: PBKDF2-HMAC-SHA256 (200k rounds, 16B namak).
  - USAGE: har account apni request-ginti + aakhri-istemaal yaad rakhta hai.

API:
    signup(email, password)  -> dict (ok) | dict (error + code)
    signin(email, password)  -> dict (ok) | dict (error + code)
    new_key(key)             -> dict (nayi key, max 3) | dict (error + code)
    valid_key(key)           -> bool (guard.py L6 call karta hai)
    me(key)                  -> dict | None  (email/keys/requests/created)
    bump(key)                -> usage +1 (server chat pass par)
"""
import hashlib
import json
import os
import re
import secrets
import sys
import time

# 🔗 ROOT-TALASH (frozen-aware): EXE me bundle ho to bhi data EXE ke APNE
#    folder me ho (temp\_MEIxxx me NAHI — bande ki accounts wahan gayab hote)
if getattr(sys, "frozen", False):
    ROOT = os.path.dirname(sys.executable)          # 📦 package-folder
    if not os.path.isdir(os.path.join(ROOT, "data")):
        ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USERS_PATH = os.path.join(ROOT, "data", "genone_users.json")
_PBKDF2_ROUNDS = 200_000
_EMAIL_RX = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
_KEY_LIMIT = 3          # 🎫 FREE HADD (user qanoon): 3 API keys per account
_lock = __import__("threading").Lock()


# ------------------------------------------------------------ store
def _load():
    try:
        with open(USERS_PATH, encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict) and isinstance(d.get("users"), dict):
            _migrate_keys(d)
            return d
    except Exception:
        pass
    return {"users": {}, "note": "Hemomemo AI API per-user accounts "
                                 "(100% local — no platform API)"}


def _migrate_keys(d):
    """Purane `gk_…` keys → naya `hemo…` (prefix-swap, key-wahi).

    Kisi bande ka kaam nahi rukta: random-hissa bilkul wahi rehta hai,
    sirf shuruaat ab Hemomemo ke naam se hoti hai (hemo…)."""
    ch = False
    for u in d["users"].values():
        if str(u.get("key", "")).startswith("gk_"):
            u["key"] = "hemo" + str(u["key"])[3:]
            ch = True
        keys = u.get("keys")
        if isinstance(keys, list):
            for i, k in enumerate(keys):
                if str(k).startswith("gk_"):
                    keys[i] = "hemo" + str(k)[3:]
                    ch = True
    if ch:
        try:
            _save(d)
        except Exception:
            pass


def _save(d):
    os.makedirs(os.path.dirname(USERS_PATH), exist_ok=True)
    tmp = USERS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=1)
    os.replace(tmp, USERS_PATH)          # atomic — half-written kabhi nahi


def _norm_user(u: dict):
    """Purana single-key hisaab → naya keys-list hisaab (bila nuqsan)."""
    if "keys" not in u or not isinstance(u.get("keys"), list):
        u["keys"] = []
    if u.get("key") and u["key"] not in u["keys"]:
        u["keys"].insert(0, u["key"])    # purani key pehle (salamat)
    if u["keys"] and not u.get("key"):
        u["key"] = u["keys"][0]
    return u


def _hash_pw(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                               salt, _PBKDF2_ROUNDS).hex()


def _check_email(email: str) -> bool:
    return bool(_EMAIL_RX.match(str(email or "").strip()))


# ------------------------------------------------------------ sign-up/in
def signup(email: str, password: str) -> dict:
    """Naya account → bande ki APNI pehli Hemomemo AI API key (copy-ready)."""
    email = str(email or "").strip().lower()
    password = str(password or "")
    if not _check_email(email):
        return {"error": "email ghalat — misal: naam@gmail.com", "code": 400}
    if len(password) < 6:
        return {"error": "password kam-az-kam 6 heruf ka rakho", "code": 400}
    with _lock:
        d = _load()
        if email in d["users"]:
            return {"error": "ye email pehle se hai — Sign-in karo",
                    "code": 409}
        salt = secrets.token_bytes(16)
        key = "hemo" + secrets.token_hex(24)   # bande ki APNI Hemomemo key
        d["users"][email] = {
            "salt": salt.hex(),
            "pw": _hash_pw(password, salt),
            "key": key,
            "keys": [key],
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
            "requests": 0,
            "last_used": "",
        }
        _save(d)
    return {"ok": True, "email": email, "key": key, "keys": [key],
            "key_limit": _KEY_LIMIT,
            "note": "ye AAPKI Hemomemo AI API key hai — copy kar lo "
                    "(X-Hemomemo-Key header). Kisi platform ki API nahi — "
                    "seedha Hemomemo AI (local) se juri hai."}


def signin(email: str, password: str) -> dict:
    """Sign-in → wahi APNI keys wapas (nayi nahi banti — account linked)."""
    email = str(email or "").strip().lower()
    password = str(password or "")
    with _lock:
        d = _load()
        u = d["users"].get(email)
        if not u:
            return {"error": "ye email registered nahi — pehle Nayi API lein",
                    "code": 403}
        try:
            ok = secrets.compare_digest(
                _hash_pw(password, bytes.fromhex(u["salt"])), u["pw"])
        except Exception:
            ok = False
        if not ok:
            return {"error": "password ghalat", "code": 403}
        _norm_user(u)
        u.setdefault("requests", 0)
        _save(d)
    return {"ok": True, "email": email, "key": u["key"], "keys": u["keys"],
            "key_limit": _KEY_LIMIT,
            "created": u.get("created", ""),
            "requests": u.get("requests", 0),
            "note": "sign-in OK — ye AAPKI Hemomemo AI API key hai "
                    "(X-Hemomemo-Key). 100% local — no platform API."}


def new_key(key: str) -> dict:
    """🎫 Nayi random Hemomemo key (sirf sign-in/apni key ke sath) — max 3."""
    if not valid_key(key):
        return {"error": "pehle sign-in karo (apni key se)", "code": 401}
    with _lock:
        d = _load()
        for email, u in d["users"].items():
            if any(secrets.compare_digest(str(key), str(k))
                   for k in _norm_user(u).get("keys", [])):
                if len(u["keys"]) >= _KEY_LIMIT:
                    return {"error": "free-hadd poori — ek account sirf %d "
                                     "keys le sakta hai" % _KEY_LIMIT,
                            "code": 429, "key_limit": _KEY_LIMIT}
                nk = "hemo" + secrets.token_hex(24)  # har dafa bilkul nayi random
                u["keys"].append(nk)
                u["key"] = u["keys"][0]              # primary pehli rehti hai
                _save(d)
                return {"ok": True, "email": email, "key": nk,
                        "keys": u["keys"], "key_limit": _KEY_LIMIT,
                        "note": "nayi Hemomemo AI key tayyar — random aur "
                                "isi local DigitalBrain API se sach-much juri"}
    return {"error": "key nahi mili", "code": 401}


# ------------------------------------------------------------ keys/usage
def valid_key(key: str) -> bool:
    """guard.py (L6): kya ye key kisi bande ki APNI Hemomemo key hai?"""
    if not key or not str(key).startswith("hemo"):
        return False
    try:
        with _lock:
            d = _load()
        for u in d["users"].values():
            _norm_user(u)
            if any(secrets.compare_digest(str(key), str(k))
                   for k in u.get("keys", [])):
                return True
    except Exception:
        pass
    return False


def bump(key: str):
    """Har kamiyab API-request par bande ki ginti +1 (asli istehsaal)."""
    if not key:
        return
    try:
        with _lock:
            d = _load()
            for u in d["users"].values():
                _norm_user(u)
                if any(secrets.compare_digest(str(key), str(k))
                       for k in u.get("keys", [])):
                    u["requests"] = int(u.get("requests", 0)) + 1
                    u["last_used"] = time.strftime("%Y-%m-%d %H:%M:%S")
                    _save(d)
                    return
    except Exception:
        pass


def me(key: str):
    """/v1/auth/me — bande ki apni jaankari (ya None)."""
    if not key:
        return None
    try:
        with _lock:
            d = _load()
        for email, u in d["users"].items():
            _norm_user(u)
            if any(secrets.compare_digest(str(key), str(k))
                   for k in u.get("keys", [])):
                return {"email": email, "key": key, "keys": u["keys"],
                        "key_limit": _KEY_LIMIT,
                        "created": u.get("created", ""),
                        "requests": u.get("requests", 0),
                        "last_used": u.get("last_used", ""),
                        "api": "Hemomemo AI API v1 (apni key, 100% local)"}
    except Exception:
        pass
    return None


def stats():
    """Kitne bande apni Hemomemo key le chuke (dashboard ke liye)."""
    try:
        with _lock:
            d = _load()
        return {"users": len(d["users"]), "file": "data/genone_users.json"}
    except Exception:
        return {"users": 0}
