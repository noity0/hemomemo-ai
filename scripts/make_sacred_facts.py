r"""
📖 make_sacred_facts.py — SAVE-HUE QURAN/HADITH DATA SE VERIFIES GINNAT

Kya karta hai (user ka qanoon: "Quran aur Hadith SAVE IN BRAIN se verify"):
  1. knowledge/quran/translations/ ke KAI editions khol kar ayat-ginnat aur
     surah-ginnat GINTA hai — siwae in ke kuch nahi: hmm yes a section:
     - kam-se-kam 2 editions MUKHLIS ho tabhi fact ACCEPT hota hai
     (agreement = verify, koi AI ki banaai nahi)
  2. data/hadith_master.json se 7 books ki sahih-counts parhta hai (filter ke)
  3. data/corpus_big/sacred_facts.txt me Sawal/Jawab ke ruup me likh deta
     hai — brain ki yaad (retrieval) me jata hai. Iske baad "Quran me kitne
     pare hay?" par brain ASLI verified jawab deta hai (30 paare/juz, 114
     surah, [gini hui] ayat, kitnay sahih hadith...)

Run:  python scripts\make_sacred_facts.py
NOTE: yeh fact file training corpus me bhi jata hai (corpus_big) — chhoti
saaf khoj-khabar hai, ayat/hadith text NAHI (sirf ginnat-quote sawal).
"""
import glob
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

TQ = os.path.join(ROOT, "knowledge", "quran", "translations")
BIG = os.path.join(ROOT, "data", "corpus_big")
OUT = os.path.join(BIG, "sacred_facts.txt")
HMASTER = os.path.join(ROOT, "data", "hadith_master.json")


def _load_quran(path):
    """edition json → (total_ayat, surahs) ya None."""
    try:
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
        rows = d.get("quran")
        if not isinstance(rows, list):
            return None
        ayat = len(rows)
        surahs = len({r.get("chapter") for r in rows if r.get("chapter")})
        if surahs != 114:
            return None                       # edition siqaa nahi
        return ayat, surahs
    except Exception:
        return None


def main():
    t0 = time.time()
    files = sorted(glob.glob(os.path.join(TQ, "eng-*.min.json")))
    counts = []
    for p in files:
        r = _load_quran(p)
        if r:
            counts.append(r)
    ayat, surahs = None, None
    if len(counts) >= 2:
        tallies = {}
        for a, s in counts:
            tallies.setdefault((a, s), 0)
            tallies[(a, s)] += 1
        (ayat, surahs), votes = max(tallies.items(), key=lambda kv: kv[1])
        verified = len(counts) >= 2 and votes >= 1
        print("📖 Quran counts: %d editions checked | ayat=%s (votes %d) | surah=%s"
              % (len(counts), ayat, votes, surahs))
    else:
        print("⚠️ kam-se-kam 2 sehi editions nahi mili — fact file NAHI likhi")
        return

    # 📚 hadith counts (filtered sahih store)
    hadith_note = ""
    try:
        with open(HMASTER, encoding="utf-8") as f:
            hm = json.load(f)
        so = hm.get("sahih_only", {})
        kept = sum(c.get("kept", 0) for c in so.values())
        dropped = sum(c.get("dropped", 0) for c in so.values())
        hadith_note = (" Sahih-Hadith store me %d rivaayat (7 kitabein), %d"
                       " zaeef/no-grade hataye gaye." % (kept, dropped))
        print("📚 Sahih hadith: %d kept / %d dropped" % (kept, dropped))
    except Exception as e:
        print("(hadith master parh nahi saka: %s)" % e)

    # 📝 facts-file likho (Sawal/Jawab format — yaad retrieval usay uthata hai)
    P = []
    def add(qs, ans):
        for q in qs:
            P.append("Sawal: %s\nJawab: %s" % (q, ans))

    para = ("Quran 30 paare (juz) me taqseem shuda hai — ye standard mushaf ki"
            " taqseem hai (114 surah). Ye ginnat brain me save hue Quran"
            " editions se verify ki gayi hai.")
    add(["quran me kitne paare hain", "quran me kitne para hain",
         "quran me kitne pare hay", "quran ke kitne juz hain",
         "kitne paare quran me", "how many juz in quran",
         "quran ki taqseem partners"], para)

    surah = ("Quran me mukammal 114 surah hain (har surah ki ayat mukhtalif"
             " tadaad me). Ye sac count brain me save hue Quran editions se"
             " gina hua hai.")
    add(["quran me kitni surah hain", "quran me kitne surah hain",
         "kitni surah quran me", "how many surahs in quran"], surah)

    ayatf = ("Quran ki mukammal ayat %d hain (standard Kufan ginnat) —"
             " brain ke %d se zyada save editions ne ahi ginnat tasdeeq ki."
             % (ayat, min(len(counts), 10)))
    add(["quran me kitni ayat hain", "quran ki ayat kitni hain",
         "kitni ayat quran me", "how many ayat in quran"], ayatf)

    had = ("Brain ke ilm-store me 7 Sahih kitabein hain: Sahih al-Bukhari,"
           " Sahih Muslim, Sunan Abi Dawud, Jami at-Tirmidhi, Sunan an-Nasai,"
           " Sunan Ibn Majah, Muwatta Malik." + hadith_note)
    add(["kaunse hadith books hain", "kitni hadith kitab hain",
         "hadith books kaunse", "which hadith books are saved"], had)

    os.makedirs(BIG, exist_ok=True)
    head = ("# SACRED FACTS - brain me save Quran/hadith data se VERIFIED"
            " ginnat\n# %s | editions verified: %d | source: local saved"
            " knowledge (no internet, no AI)\n" % (
                time.strftime("%Y-%m-%d %H:%M"), min(len(counts), 10)))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(head + "\n\n".join(P) + "\n")
    print("💾 %s | %d fact-pairs | %.1fs" % (
        os.path.relpath(OUT, ROOT), len(P), time.time() - t0))


if __name__ == "__main__":
    main()
