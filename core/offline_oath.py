"""
🌍 offline_oath.py — SAREY QANOON KA PAKKA URDU-QAIDNAMA (PERMANENT, KABHI-NAHI-BHOOLTE)

Hemomemo AI ka SIRTUKHM oath (har module, har chat, har generation
yaad rahe — kisi ke kehne par bhi nahi tootega):

    1. NO API          — koi bhi API-key/API-service NAHI (payment/subscription haram)
    2. NO Other-AI     — ya koi ai VERIFIED by another AI — kisi doosre AI-model
                         se koi connection NAHI (chat button, endpoint, gateway)
    3. NO AI-platform  — kisi AI platform (yani jo AI-hay) ka poll/subscribe/attach NAHI
    4. NO AI-helper    — jawab banay me kisi external AI helper ka istemaal NAHI
                         (pritika-machinery, hooks, wrappers banned ALL)
    5. OWN MODEL ONLY  — jawab Hemomemo AI ka APNA pure-NumPy LSTM + apni yaad +
                         apna bio-dimagh + apna dil + apna cognition-flow
    6. Slm-white-list UI sirf PAGE-READ (ilm ki kitabein) — AI-service NAHI;
                         aur bhi net ki hikmeta: sirf needs-
                         mutabiq (unknown) sawal par, kaudit-tah qanun (chit-chat,
                         zakit, gair-sacred/gair-junk) — vitrat net_guard hard-block

Yeh qa is format me likhi hai: har module ai `oath_text()` print/read kare
(model_card.json me bhi permanent rule ho chuki hai).
"""
import os
import sys

if getattr(sys, "frozen", False):
    ROOT = os.path.dirname(sys.executable)      # 📦 EXE apna folder (Hemomemo)
    if not (os.path.isdir(os.path.join(ROOT, "model"))
            or os.path.isdir(os.path.join(ROOT, "data"))):
        ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

OATH_LINES = (
    "🌍 OFFLINE-OATH (Hemomemo AI ke apne dimagh ka pakka qanoon — hamesha):",
    "  1. No API — koi API-service NAHI (kabhi ke lab par na le ya doosra)",
    "  2. No doosre AI-model se connection — koi openai/gemini/claude NAHI",
    "  3. No AI-platform connection — koi chat-platform/bot attach NAHI",
    "  4. No AI-helper — kisi model ki madad bina til-e-corner NAHI",
    "  5. APNA MODEL hi — pure NumPy LSTM + yaad + bio-dimagh + heart + cognition",
    "     Saudi/agent style hard-block: harvest/net_guard.py (still kill)",
    "  6. Net sirf whitelisted PAGE-READ (DDG-lite/Wikipedia) research-zarurat par",
)


def oath_text() -> str:
    return "\n".join(OATH_LINES)


def assert_offline() -> bool:
    """ASLI self-report (no network use): net_guard ke AI-block regexes zinda
    hain aur mamooli AI-host waqai pakde jate hain — warna False (oath toota)."""
    try:
        from harvest import net_guard as _ng
        rx = getattr(_ng, "BANNED_AI_RX", None)
        if rx is None:
            return False                       # block-regex hi nahi → oath adhoora
        # khud-jaanch: mamooli AI-hosts regex par pakde jayne (sirf string-test)
        for probe in ("api.openai.com", "generativelanguage.googleapis.com",
                      "api.anthropic.com"):
            if not rx.search(probe):
                return False
        return True
    except Exception:
        return False      # net_guard na mile to oath tasdeeq NAHI hota (sach)


if __name__ == "__main__":
    print(oath_text())
