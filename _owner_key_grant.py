# -*- coding: utf-8 -*-
"""Owner grant: user's OWN hemo... key into the DEV accounts store.

Ye sirf OWNER (HMHS) ka apna PC hai — apni key apne dev-store me grant karna
owner ka haq hai (append-only: sirf naya record add, purana kuch nahi).
Record signin ke liye password-jaan-boojh random (koi is email se signin nahi
kar sakta) — sirf KEY verification me madad karta hai (valid_key)."""
import hashlib
import json
import os
import secrets
import sys
import time

USER_KEY = "hemof7b9da7ee8fa5bb385ea9cc38e8097b955f6e3f499c49d74"
EMAIL = "owner@hmhs.local"
PATH = r"D:\DigitalBrain\data\hemomemo_users.json"

with open(PATH, encoding="utf-8") as f:
    d = json.load(f)

already = any(
    any(secrets.compare_digest(str(k), USER_KEY) for k in u.get("keys", []))
    for u in d["users"].values())
if already:
    print("owner-grant pehle se mojood — kuch nahi badla")
    sys.exit(0)

salt = secrets.token_bytes(16)                       # signin-karna mumkin nahi
pw_hash = hashlib.pbkdf2_hmac(
    "sha256", secrets.token_bytes(24), salt, 200_000).hex()
d["users"][EMAIL] = {
    "salt": salt.hex(),
    "pw": pw_hash,
    "key": USER_KEY,
    "keys": [USER_KEY],
    "created": time.strftime("%Y-%m-%d %H:%M:%S"),
    "requests": 0,
    "last_used": "",
    "note": "owner-manual grant (OpenCode integration — HMHS apni key)",
}
tmp = PATH + ".tmp"
with open(tmp, "w", encoding="utf-8") as f:
    json.dump(d, f, indent=1)
os.replace(tmp, PATH)
print("owner-grant added:", EMAIL, "->", USER_KEY[:14] + "(hidden)")
print("users me kitne:", len(d["users"]))
