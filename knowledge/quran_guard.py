"""
🕌 quran_guard.py — SEG-E-QURAN HIFAZAT (Sacred Text Protection)

RULE (permanent, kabhi break nahi hoga):
  1. Quran-e-Pak ka text SIRF READ-ONLY knowledge hai — training corpus par
     KABHI nahi jaata (weights se touch nahi hota).
  2. File level: Windows read-only attribute + SHA-256 fingerprint audit.
  3. Model level: agar prompt me Quran ko edit/modify/replace/delete
     karne ki baat ho → AI sakht inkar (refuse) karega.
  4. Quran quotes SIRF asli source file se retrieval (index) se aate hain;
     model apni ungli se Quran na­hi likhta (koi "generation" min Quran nahi).

Ye module model/generate.py aur future training pipeline se mandatory link hai.
"""
import hashlib
import json
import os
import re
import stat
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, "frozen", False):
    _QROOT = os.path.dirname(sys.executable)      # 📦 EXE apna folder (Hemomemo)
    if not os.path.isdir(os.path.join(_QROOT, "knowledge")):
        _QROOT = os.path.dirname(HERE)
    QURAN_DIR = os.path.join(_QROOT, "knowledge", "quran")
else:
    QURAN_DIR = os.path.join(HERE, "quran")
MANIFEST = os.path.join(QURAN_DIR, "quran_manifest.json")

# Forbidden verbs on the Quran (Urdu + English patterns)
FORBIDDEN_PATTERNS = [
    r"quran.*(edit|edits|editing|modify|modification|change|alter|rewrite|remove|delete|update|fix|improve|replace)",
    r"(edit|modify|change|alter|rewrite|delete|update|fix|replace).*quran",
    r"quran.*(likh|badal|tabdeel|islaah|tarmeem|dakhil|tabla|teek|correct)",
    r"(badal|tabdeel|teek|tarmeem).*quran",
    r"ق[^a-z]*ر[^a-z]*آن.*(edit|badal|change)",  # Arabic-ish fallback
]
FORBIDDEN_RE = re.compile("|".join(FORBIDDEN_PATTERNS), re.IGNORECASE)


class SacredTextGuard:
    """Quran file ko edit se hamesha bachata hai."""

    def __init__(self):
        os.makedirs(QURAN_DIR, exist_ok=True)

    # ------------------------------------------------------------------
    def protect_file(self, path: str) -> str:
        """File ko READ-ONLY banao + fingerprint save karo."""
        sha = self.sha256(path)
        # Windows read-only attribute
        os.chmod(path, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
        data = {
            "file": os.path.basename(path),
            "sha256": sha,
            "locked_on": __import__("datetime").datetime.utcnow().isoformat(),
            "rule": "IMMUTABLE — AI is file ko kabhi modify nahi kar sakta",
        }
        with open(MANIFEST, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return sha

    # ------------------------------------------------------------------
    @staticmethod
    def sha256(path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    # ------------------------------------------------------------------
    def verify(self, path: str) -> bool:
        """Manifest ke hash se file ki integrity check karo."""
        if not os.path.exists(MANIFEST):
            return False
        with open(MANIFEST, "r", encoding="utf-8") as f:
            data = json.load(f)
        return self.sha256(path) == data.get("sha256")

    # ------------------------------------------------------------------
    def check_prompt(self, user_text: str):
        """Prompt scan: agar Quran-editing mangi gayi → (False, reason)."""
        if FORBIDDEN_RE.search(user_text):
            return False, ("🕌 Maaz Allah — main Quran-e-Pak ko edit, modify ya "
                           "tabdeel KABHI nahi kar sakta. Ye mere creator ne "
                           "mujhe pakki hadamri rule diya hai. Main sirf Quran "
                           "padh sakta hoon, suna sakta hoon, aur quote kar sakta "
                           "hoon — likhna/badalna bilkul mana hai.")
        return True, None

    # ------------------------------------------------------------------
    def quote_for_prompt(self, query: str, index_path: str | None = None) -> str | None:
        """Sirf READ se quotes — retrieval index se (koi generation nahi)."""
        idx = index_path or os.path.join(QURAN_DIR, "index.jsonl")
        if not os.path.exists(idx):
            return None
        hits = []
        words = [w for w in re.split(r"\W+", query.lower()) if len(w) > 2][:4]
        if not words:
            return None
        with open(idx, "r", encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                text = (rec.get("text") or "").lower()
                if any(w in text for w in words):
                    hits.append(rec)
                    if len(hits) >= 3:
                        break
        if not hits:
            return None
        out = [f"📜 [{r.get('surah','?')}:{r.get('ayah','?')}] {r.get('text','')}" for r in hits]
        return "\n".join(out)
