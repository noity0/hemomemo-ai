"""gems.py - Hemomemo GEMS (custom assistants - 100% LOCAL, no AI-API)
===================================================================
Gem = aap ka bana-hua assistant-shakhs (naam + andaz + focus). Ye sirf
apke LOCAL dimagh (token-brain + memory) ke UPAR persona hai - koi
bahar-ka model/API nahi. Sab gems: data/gems.json (aap ki file).

Commands:
  gem list                  - saare gems
  gem use <name>            - gem ON (har chat ab usi ke andaz me)
  gem band                  - gem OFF (normal chat)
  gem banao <name> role: <role> style: <style> topics: <t1,t2>
  gem <name>                - gem ki tafseel

Default gems (pehli-baar khud ban jate hain):
  Ustad (islamic-ustaad), Coder (programmer-ustaad),
  Rafiq (dostana-musalman-saathi), Reporter (khabar-nigar)
"""
import json
import os
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEMS_PATH = os.path.join(_ROOT, "data", "gems.json")
ACTIVE_PATH = os.path.join(_ROOT, "data", "gem_active.json")

_DEFAULTS = [
    {"name": "Ustad", "role": "islamic-ustaad (Quran/Sunnah/ilm ka ustaad)",
     "style": "izzat-dar, hawala-dar (Quran-hadith ke hawale), sade-misali",
     "topics": "islam, quran, hadith, seerat"},
    {"name": "Coder", "role": "programmer-ustaad (45+ zabanein ka coder)",
     "style": "seedha-code, chhote-misale, galti pakad ke sudhar",
     "topics": "python, cmd, powershell, web, coding"},
    {"name": "Rafiq", "role": "dostana-saathi (roz-mara ka hamdam)",
     "style": "garam-josh, hansi-mazaq, hosla-afzai",
     "topics": "aam-baat, din-charya, mashwara"},
    {"name": "Reporter", "role": "khabar-nigar (duniya ki khabrein)",
     "style": "fact-wala, chhote-nukat, sources ke sath",
     "topics": "khabrein, world-news, deep-research"},
]


def _load():
    try:
        with open(GEMS_PATH, "r", encoding="utf-8") as f:
            d = json.load(f)
        g = d.get("gems")
        if isinstance(g, list) and g:
            return g
    except Exception:
        pass
    _ensure_defaults()
    try:
        with open(GEMS_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("gems", [])
    except Exception:
        return list(_DEFAULTS)


def _ensure_defaults():
    try:
        os.makedirs(os.path.dirname(GEMS_PATH), exist_ok=True)
        if not os.path.exists(GEMS_PATH):
            with open(GEMS_PATH, "w", encoding="utf-8") as f:
                json.dump({"gems": _DEFAULTS}, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


def _save(gems):
    os.makedirs(os.path.dirname(GEMS_PATH), exist_ok=True)
    with open(GEMS_PATH, "w", encoding="utf-8") as f:
        json.dump({"gems": gems}, f, ensure_ascii=False, indent=1)


def _active():
    try:
        with open(ACTIVE_PATH, "r", encoding="utf-8") as f:
            return json.load(f).get("gem")
    except Exception:
        return None


def _set_active(name):
    os.makedirs(os.path.dirname(ACTIVE_PATH), exist_ok=True)
    with open(ACTIVE_PATH, "w", encoding="utf-8") as f:
        json.dump({"gem": name or ""}, f, ensure_ascii=False)


def active():
    """Active gem ka dict | None (gem-band = None)."""
    n = _active()
    if not n:
        return None
    for g in _load():
        if g.get("name", "").lower() == n.lower():
            return g
    return None


def answer_active(prompt):
    """Active-gem ke andaz me LOCAL-brain se jawab -> (text, meta).

    persona-instruction + user-sawal -> token-brain (no API, local).
    """
    g = active()
    if not g:
        return None, None
    instr = ("Tum '%s' ho: %s. Andaz: %s. Focus: %s. Jawab isi andaz me do."
             % (g.get("name"), g.get("role", "assistant"),
                g.get("style", ""), g.get("topics", "")))
    try:
        from model.understand import default_token_chat
        txt, m = default_token_chat().respond(
            "%s\nSawal: %s" % (instr, (prompt or "").strip()))
        if isinstance(txt, str) and txt.strip():
            meta = dict(m or {})
            meta.update({"source": "gem", "gem": g.get("name")})
            return "[%s] %s" % (g.get("name"), txt), meta
    except Exception:
        pass
    return ("[%s] Jawab abhi nahi ban saka (local-dimagh busy/ghayab) - "
            "dobara koshish karo." % g.get("name"), {"source": "gem",
                                                     "gem": g.get("name"),
                                                     "state": "fail"})


def run_command(rest):
    """'gem' ke-baad ka hissa -> (text, meta) | (None, None) agar
    ye gem-command hi nahi thi (powers.py aage barhne ke liye)."""
    rest = (rest or "").strip()
    low = rest.lower()
    if not low or low.startswith(("madad", "help")):
        return ("[gems] Hukum: gem list | gem use <naam> | gem band | "
                "gem banao <naam> role: ... style: ... topics: ...",
                {"source": "gems", "state": "help"})
    if low.startswith("list"):
        g = _load()
        act = _active() or ""
        return ("[gems] Custom assistants (100% local - koi API nahi):\n" +
                "\n".join("  - %s%s\n      %s" %
                          (x.get("name"), "  <AB-ACTIVE>" if
                           x.get("name").lower() == act.lower() else "",
                           x.get("role", "")) for x in g)),
        {"source": "gems", "state": "list", "n": len(g)}
    if low.startswith("band"):
        _set_active("")
        return "[gems] Gem band - ab normal chat (apna dimagh khud).", \
            {"source": "gems", "state": "off"}
    m = re.match(r"(?i)^(?:use|on|chalao)\s+([\w-]+)", rest)
    if m:
        name = m.group(1)
        for x in _load():
            if x.get("name", "").lower() == name.lower():
                _set_active(x["name"])
                return ("[gems] AB-ACTIVE: %s - %s\n(Andaz: %s)\n"
                        "(Band karne ke liye: 'gem band')"
                        % (x["name"], x.get("role", ""), x.get("style", "")),
                        {"source": "gems", "state": "on",
                         "gem": x["name"]})
        return "[gems] Gem '%s' nahi (dekh: 'gem list' ya banao naya)." % name, \
            {"source": "gems", "state": "missing"}
    m = re.match(r"(?i)^(?:banao|create|new)\s+([\w-]+)\s*(.*)$", rest)
    if m:
        name, desc = m.group(1), m.group(2)
        role, style, topics = "", "", ""
        rm = re.search(r"(?i)role:\s*(.+?)(?=\s*style:|\s*topics:|$)", desc)
        sm = re.search(r"(?i)style:\s*(.+?)(?=\s*role:|\s*topics:|$)", desc)
        tm = re.search(r"(?i)topics:\s*(.+?)$", desc)
        role = rm.group(1).strip() if rm else role
        style = sm.group(1).strip() if sm else style
        topics = tm.group(1).strip() if tm else topics
        gems = _load()
        if any(x.get("name", "").lower() == name.lower() for x in gems):
            return "[gems] '%s' pehle-se hai (naya naam try karo)." % name, \
                {"source": "gems", "state": "exists"}
        gems.append({"name": name, "role": role or "assistant",
                     "style": style or "sade, dostana", "topics": topics})
        _save(gems)
        return ("[gems] Naya gem bana: %s (role: %s)\nChalao: 'gem use %s'"
                % (name, role or "assistant", name)),
        {"source": "gems", "state": "created", "gem": name}
    m = re.match(r"(?i)^([\w-]+)$", rest)
    if m:
        for x in _load():
            if x.get("name", "").lower() == m.group(1).lower():
                return ("[gems] %s\n  role: %s\n  style: %s\n  topics: %s"
                        % (x["name"], x.get("role", ""), x.get("style", ""),
                           x.get("topics", ""))),
                {"source": "gems", "state": "detail"}
        return "[gems] '%s' nahi mila." % m.group(1), \
            {"source": "gems", "state": "missing"}
    return None, None


if __name__ == "__main__":
    t, _ = run_command("list")
    print(t)
