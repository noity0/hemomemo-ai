"""powers.py - Hemomemo POWERS-DISPATCHER (chat me sab tools ek jagah)
===================================================================
User-powers (sab LOCAL ya non-AI API; koi AI-platform key/connection
KABHI nahi):
  web-search   : search <q> / khojo <q>          (search_api)
  deep-research: deep research <topic>           (deep_research)
  python-code  : python <code> / code chalao     (code_exec)
  image-gen    : image banao <prompt>            (img_gen - procedural)
  canvas       : canvas banao/likho/kholo/...    (canvas_board)
  gems         : gem list/use/banao/band         (gems)
  mcp          : mcp servers/tools/call          (mcp_link - stdio)
  gmail        : inbox check / send email ...    (gmail_link)
  gdrive/docs  : drive list/upload/download, doc read  (gdrive_link)

wants(text) -> (tool, payload) | (None, None)
run(tool, payload) -> (text, meta)
"""
import re

_MAIL_GEM_RX = re.compile(r"(?i)^\s*(?:inbox|send\s+e?mail|e?mail\s+"
                          r"bhejo|mail\s+bhejo|check\s+(?:my\s+)?"
                          r"(?:e?mails?|inbox|mail))\b")
_GEM_RX = re.compile(r"(?i)^\s*gem\s*[:,]?\s*(.*)$")
_SEARCH_RX = re.compile(
    r"(?i)^\s*(?:web[\s-]?search|search(?:\s+for|\s+karo|\s+kar)?"
    r"|khojo|khoj(?:\s+karo)?|talaash(?:\s+karo)?|dhoondo|dhundo|google)"
    r"\s*[:\-\s]\s*(.+?)\s*$")
_RESEARCH_RX = re.compile(
    r"(?i)^\s*(?:deep\s+research|gehri\s+research|research\s+karo"
    r"|khoj-bahri)\s*[:,]?\s*(.+?)\s*$")
_CODE_RX = re.compile(
    r"(?i)^\s*(?:python|run\s+python|code\s+chalao|py)\b\s*[:,]?\s*(.*)$",
    re.S)
_IMG_RX = re.compile(
    r"(?i)^\s*(?:(?:image|tasveer|picture|art|poster)\s+(?:banao|bana|"
    r"generate|make|draw|bnao)"                                   # noun-verb: "image banao <p>"
    r"|(?:create|make|draw|generate)\s+(?:an?\s+|the\s+)?"
    r"(?:image|tasveer|picture|art|poster)(?:\s+(?:of|ka|ki|about))?"  # verb-first: "create picture of ai"
    r")\s*[:,]?\s*(.+?)\s*$")
_CANVAS_RX = re.compile(r"(?i)^\s*canvas\s*[:,]?\s*(.*)$")
_MCP_RX = re.compile(r"(?i)^\s*mcp\s*[:,]?\s*(.*)$")
_DRIVE_RX = re.compile(r"(?i)^\s*(?:drive|gdrive)\s*[:,]?\s*(.*)$")
_DOC_RX = re.compile(r"(?i)^\s*doc(?:s)?\s+(?:read|parho|parh)\s*[:,]?\s*(.*)$")

_HELP = (
    "[powers] Hukum-list (sab local ya non-AI-API):\n"
    "  search <topic>                - web-search (DDG keyless)\n"
    "  deep research <topic>         - multi-page report (sources ke sath)\n"
    "  python <code>                 - python-code chalao (local, timeout)\n"
    "  image banao <prompt>          - procedural tasveer (100% local)\n"
    "  canvas banao <naam> | canvas <naam> likho: <text> | canvas list\n"
    "  gem list | gem use <naam> | gem banao <naam> role: ... | gem band\n"
    "  mcp servers | mcp tools <srv> | mcp call <srv> <tool> {json}\n"
    "  inbox check | send email to X subject: ... body: ...\n"
    "  drive list | drive upload <path> | drive download <naam>\n"
    "  doc read <id|naam>\n"
    "(koi AI-platform API nahi - dimagh 100% aap ka)")


def wants(text):
    """(tool, payload) | (None, None)."""
    t = (text or "").strip()
    if not t:
        return None, None
    if t.lower() in ("powers", "powers help", "hukum list", "tools"):
        return "help", ""
    m = _RESEARCH_RX.match(t)
    if m and m.group(1).strip():
        return "research", m.group(1).strip()
    m = _CANVAS_RX.match(t)
    if m:
        return "canvas", m.group(1)
    m = _MCP_RX.match(t)
    if m:
        return "mcp", m.group(1)
    m = _DRIVE_RX.match(t)
    if m:
        return "drive", m.group(1)
    m = _DOC_RX.match(t)
    if m:
        return "doc", m.group(1)
    m = _GEM_RX.match(t)
    if m:
        return "gem", m.group(1)
    m = _IMG_RX.match(t)
    if m:
        return "image", m.group(1)
    m = _CODE_RX.match(t)
    if m:
        code = m.group(1).strip()
        if code:
            return "code", code
    m = _SEARCH_RX.match(t)
    if m:
        q = m.group(1).strip()
        for w in ("karo", "kar", "do", "par", "pe", "for", "about"):
            if q.lower().split()[:1] == [w]:
                q = q.split(" ", 1)[1].strip() if " " in q else q
        if len(q) >= 2:
            return "search", q
    if _MAIL_GEM_RX.match(t):
        return "mail", t
    return None, None


def run(tool, payload):
    """Tool chalao -> (text, meta). Har cheez honest-fail-safe."""
    try:
        if tool == "help":
            return _HELP, {"source": "powers", "state": "help"}
        if tool == "search":
            from model import search_api
            return search_api.search_text(payload)
        if tool == "research":
            from model import deep_research
            return deep_research.research(payload)
        if tool == "code":
            from model import code_exec
            return code_exec.run_python_text(payload)
        if tool == "image":
            from model import img_gen
            return img_gen.generate_text(payload)
        if tool == "canvas":
            from model import canvas_board
            return canvas_board.run_command(payload)
        if tool == "gem":
            from model import gems
            return gems.run_command(payload)
        if tool == "mcp":
            from model import mcp_link
            return mcp_link.run_command(payload)
        if tool == "mail":
            from model import gmail_link as gl
            mw, md = gl.wants_mail(payload)
            return (gl.read_inbox_text() if mw == "read"
                    else gl.send_from_command(md))
        if tool == "drive":
            from model import gdrive_link
            return gdrive_link.run_command(payload)
        if tool == "doc":
            from model import gdrive_link
            return gdrive_link.doc_read(payload)
    except Exception as e:
        return ("[%s] Masla (honest): %s" % (tool, str(e)[:220]),
                {"source": tool, "state": "error"})
    return "Ye tool (%s) abhi wired nahi." % tool, {"source": tool,
                                                   "state": "unknown"}


if __name__ == "__main__":
    for t in ("search quran tafseer", "python print(2+3)", "image banao shami kabab",
              "canvas list", "gem list", "mcp servers", "drive list",
              "deep research karachi news", "inbox check", "aaj kya haal"):
        print(repr(t), "->", wants(t))
