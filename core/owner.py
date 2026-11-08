"""
🪪 owner.py — OWNER DATA (single source of truth)

owner_data.txt (root me) ke sath linked — poora project isi module se owner
ko jaanta hai: core/hub.py, model/generate.py, run.py, server/server.py,
web/index.html aur README.md. Koi API kyun nahi — sirf is PC ka sacha data.
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
OWNER_PATH = os.path.join(ROOT, "owner_data.txt")

# 📄 Yeh details owner_data.txt me likhi hain (link: usi file ki sachi copy)
NAME = "Hafiz Muhammed Huzaifa Shamim"
AGE = 17
COLLEGE = "DJ Science College, Karachi"
RESIDENCE = "Iskaan Residency Block L, Karachi"
FUTURE = "shayad qareebi dinon me doosri jagah shift hona"
SEARCH_URL = (
    "https://www.google.com/search?q=Hafiz+Muhammed+Huzaifa+Shamim")

# 🧠 Yaad-dahai ke liye Sawal→Jawab pairs (model/generate.py _qa_index me jul jaate)
OWNER_QA = (
    ("tumhara owner kaun hai",
     "Mere owner (banane wale) Hafiz Muhammed Huzaifa Shamim hain — ye poora "
     "digital dimagh unhone banaya hai."),
    ("tumhe kisne banaya",
     "Mujhe Hafiz Muhammed Huzaifa Shamim ne banaya hai — poori tafseel "
     "owner_data.txt me hai."),
    ("owner ki umaar kya hai",
     "Mere owner Hafiz Muhammed Huzaifa Shamim ki umaar 17 saal hai."),
    ("owner kahan parhte hain",
     "Mere owner DJ Science College, Karachi me parhte hain, aur Iskaan "
     "Residency Block L, Karachi me rehte hain."),
    ("humhs kisne banaya",
     "Mere owner (Hafiz Muhammed Huzaifa Shamim ne) https://hmhsgame.netlify.app "
     "site banaya - jiska naam HMHS Game hai. Email: laptopshampoo@gmail.com. "
     "Instagram: huzaifa_464."),
    ("huzaifa shamim kaun hai",
     "Hafiz Muhammed Huzaifa Shamim mere owner hain — 17 saal, DJ Science "
     "College Karachi, Iskaan Residency Block L."),
)


def owner_file_exists() -> bool:
    """owner_data.txt root me maujood hai?"""
    return os.path.exists(OWNER_PATH)


def owner_dict() -> dict:
    """Owner ka pura data dict me (file-existence ki sachi intesab ke sath)."""
    return {
        "file": os.path.relpath(OWNER_PATH, ROOT),
        "file_exists": owner_file_exists(),
        "name": NAME,
        "age": AGE,
        "college": COLLEGE,
        "residence": RESIDENCE,
        "future": FUTURE,
        "search_url": SEARCH_URL,
    }


def summary() -> str:
    """Chhoti si ik-line pehchan (run.py / server banner ke liye)."""
    return "%s (%d) — %s" % (NAME, AGE, COLLEGE)


if __name__ == "__main__":
    import json
    import pprint

    pprint.pprint(owner_dict())
    print("summary:", summary())
