"""canvas_board.py - Hemomemo CANVAS (local documents - no AI-API)
================================================================
Canvas = saved-board (text/notes/plans). Sab local files:
  data/canvas/<name>.canvas.json  {text, updated}
+ "canvas <name> dikhao" -> PNG-card bhi ban jata hai (img_gen se).

Commands (powers.py se aate hain):
  canvas banao <name>            - nayi khali canvas
  canvas <name> likho <text>     - text jodo (append)
  canvas <name> kholo|parho      - text dikhao
  canvas <name> dikhao           - PNG-card banao + path
  canvas list                    - saari canvases
  canvas <name> mitao            - delete
"""
import json
import os
import re
import time

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DIR = os.path.join(_ROOT, "data", "canvas")


def _safe(name):
    n = re.sub(r"[^a-zA-Z0-9_-]", "_", (name or "").strip())[:40]
    return n or "untitled"


def _path(name):
    return os.path.join(_DIR, "%s.canvas.json" % _safe(name))


def create(name, text=""):
    os.makedirs(_DIR, exist_ok=True)
    p = _path(name)
    if os.path.exists(p):
        return False, "canvas '%s' pehle-se hai (kholne ke liye: canvas %s kholo)" % (_safe(name), _safe(name))
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"text": text or "", "created": time.strftime("%Y-%m-%d %H:%M"),
                   "updated": time.strftime("%Y-%m-%d %H:%M")}, f,
                  ensure_ascii=False, indent=1)
    return True, _safe(name)


def append(name, text):
    p = _path(name)
    if not os.path.exists(p):
        create(name)
    with open(p, "r", encoding="utf-8") as f:
        d = json.load(f)
    d["text"] = ((d.get("text") or "") + "\n" + (text or "")).strip()
    d["updated"] = time.strftime("%Y-%m-%d %H:%M")
    with open(p, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    return d["text"]


def read_text(name):
    p = _path(name)
    if not os.path.exists(p):
        return None
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f).get("text", "")
    except Exception:
        return None


def delete(name):
    p = _path(name)
    if os.path.exists(p):
        os.remove(p)
        return True
    return False


def list_all():
    if not os.path.isdir(_DIR):
        return []
    return sorted(f[:-len(".canvas.json")] for f in os.listdir(_DIR)
                  if f.endswith(".canvas.json"))


def render_png(name):
    """Canvas-text -> PNG-card (img_gen.quote_card) -> (path, err)."""
    from model import img_gen as ig
    t = read_text(name)
    if t is None:
        return None, "canvas '%s' nahi mili" % _safe(name)
    if not t.strip():
        t = "(khali canvas: %s)" % _safe(name)
    return ig.quote_card(t[:800])


_VERBS_BANA = ("banao", "bana", "create", "naya", "new", "make")
_VERBS_LIKH = ("likho", "likh", "append", "jodo", "add", "write")
_VERBS_PADH = ("kholo", "parho", "parh", "read", "open", "dikha-text")
_VERBS_PNG = ("dikhao", "dikha", "show", "image", "tasveer", "png")
_VERBS_MITA = ("mitao", "delete", "hatao", "remove", "khatam")


def run_command(rest):
    """'canvas' ke-baad ka hissa -> (text, meta)."""
    rest = (rest or "").strip()
    if not rest or rest.lower() in ("list", "sab", "saari"):
        names = list_all()
        if not names:
            return ("[canvas] Abhi koi canvas nahi. Banao: 'canvas banao "
                    "mere-khayal'", {"source": "canvas", "state": "empty"})
        return ("[canvas] Saari canvases:\n" +
                "\n".join("  - " + n for n in names)),
        {"source": "canvas", "state": "list", "n": len(names)}
    m = re.match(r"(?i)^(?:banao|create|new)\s+([\w-]+)\s*(.*)$", rest)
    if m:
        ok, msg = create(m.group(1), m.group(2))
        if ok:
            return ("[canvas] Nayi canvas bani: '%s' (likho: 'canvas %s "
                    "likho <text>')" % (msg, msg),
                    {"source": "canvas", "state": "created", "name": msg})
        return "[canvas] %s" % msg, {"source": "canvas", "state": "exists"}
    m = re.match(r"^(?:list|mitao)\b(.*)$", rest)
    if m and rest.lower().startswith("mitao"):
        name = m.group(1).strip() or ""
        return ("[canvas] '%s' %s" % (_safe(name),
                                      "mita di" if delete(name) else "nahi mili"),
                {"source": "canvas", "state": "deleted"})
    m = re.match(r"(?i)^([\w-]+)\s+(.*)$", rest)
    if not m:
        # sirf naam diya -> kholo hi samjho
        t = read_text(rest.strip())
        if t is not None:
            return "[canvas] '%s':\n%s" % (_safe(rest), t or "(khali)"), \
                {"source": "canvas", "state": "read"}
        return ("[canvas] Samajh nahi aaya. Format: canvas banao <naam> | "
                "canvas <naam> likho: <text> | canvas <naam> kholo | "
                "canvas <naam> dikhao | canvas list",
                {"source": "canvas", "state": "help"})
    name, act = m.group(1), m.group(2).strip()
    low = act.lower()
    if any(low.startswith(v) for v in _VERBS_PNG):
        path, err = render_png(name)
        if not path:
            return "[canvas] %s" % err, {"source": "canvas", "state": "error"}
        return ("[canvas] '%s' ka PNG-card bana: %s" % (_safe(name), path),
                {"source": "canvas", "state": "png", "file": path})
    if any(low.startswith(v) for v in _VERBS_MITA):
        return ("[canvas] '%s' %s" % (_safe(name),
                                      "mita di" if delete(name) else "nahi mili"),
                {"source": "canvas", "state": "deleted"})
    if any(low.startswith(v) for v in _VERBS_LIKH):
        text = act.split(":", 1)[-1] if ":" in act else \
            act[len(act.split()[0]):].strip()
        if not text:
            return "[canvas] Kya likhun? 'canvas %s likho: <text>'" % _safe(name), \
                {"source": "canvas", "state": "need-text"}
        append(name, text)
        return ("[canvas] '%s' me jod diya (ab: %d harf)" % (_safe(name), len(read_text(name) or "")),
                {"source": "canvas", "state": "appended"})
    if any(low.startswith(v) for v in _VERBS_PADH):
        t = read_text(name)
        if t is None:
            return "[canvas] '%s' nahi mili (banao: canvas banao %s)" % (_safe(name), _safe(name)), \
                {"source": "canvas", "state": "missing"}
        return "[canvas] '%s':\n%s" % (_safe(name), t or "(khali)"), \
            {"source": "canvas", "state": "read"}
    return ("[canvas] '%s' ke sath kya karna hai? (likho: <text> | kholo | "
            "dikhao | mitao)" % _safe(name),
            {"source": "canvas", "state": "help"})


if __name__ == "__main__":
    print(run_command("list")[0])
    print(run_command("banao test-demo")[0])
    print(run_command("test-demo likho: Pehla khayal")[0])
    print(run_command("test-demo kholo")[0])
    run_command("test-demo mitao")
