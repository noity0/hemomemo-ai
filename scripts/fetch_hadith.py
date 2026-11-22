"""
📥 fetch_hadith.py — Hemomemo AI: Hadith Books Download + Brain me Dal

7 Hadith kitaabon ko archive.org (Urdu/Hindi sources) se download karo aur
unhe D:\\DigitalBrain\\data\\corpus_big/ me brain ke QA format (Sawal/Jawab) me dalo.

Quran (clearquran/harvest_quran) ko TOUCH NAHI kar raha — sirf READ-ONLY rehta hai.
"""
import os
import ssl
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from harvest.purify import sanitize, keywords  # noqa: E402
from harvest import net_guard as _ng           # noqa: E402
_ng.install()                                  # 🛡️ firewall: AI/banned-host hard-block

OUT_DIR = os.path.join(ROOT, "data", "corpus_big")
UA = "Mozilla/5.0 (HMHS Muslim Texture Hadith Harvester; offline NumPy AI)"
CTX = ssl._create_unverified_context()


def fetch(url, tries=3):
    for k in range(tries):
        try:
            req = Request(url, headers={"User-Agent": UA})
            with urlopen(req, timeout=60, context=CTX) as r:
                return r.read().decode("utf-8", "ignore")
        except Exception as e:
            print("   try %d/%d failed: %s" % (k + 1, tries, str(e)[:70]))
            time.sleep(3)
    return None


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    sources = [
        ("Sahih al-Bukhari",
         "https://archive.org/download/books-saheh-al-bukhari-urdu-sahi-bukhari-jilad-1_202504/books_Saheh%20Al-Bukhari_urdu_Sahi-Bukhari-Jilad-1_djvu.txt",
         "hadith_bukhari.txt", "bukhari sahih hadith"),
        ("Muwatta Imam Malik",
         "https://archive.org/download/mautaimammaliktransbyallamaabdulhakeemakhtarshahjahanpurir.a./Mauta%20imam%20Malik%20Trans%20by%20Allama%20Abdul%20hakeem%20akhtar%20shahjahanpuri%20r.a._djvu.txt",
         "hadith_muwatta.txt", "muwatta imam malik hadith"),
        ("Sunan an-Nasai",
         "https://archive.org/download/sunan-an-nasai-vol.-5-3971-4987_202511/Sunan%20an-Nasai%20Vol.%201%20-%201-876_djvu.txt",
         "hadith_an_nasai.txt", "nasai sunan hadith"),
        ("Jami at-Tirmidhi",
         "https://archive.org/download/jami-at-tirmidhi-in-1-file_202405/Jami%20at-Tirmidhi%20in%201%20file_djvu.txt",
         "hadith_tirmidhi.txt", "tirmidhi jami hadith"),
        ("Sahih Muslim",
         "https://archive.org/download/saheh-al-muslim-urdu/Saheh-Al-Muslim-urdu-Vol-1_djvu.txt",
         "hadith_sahih_muslim.txt", "sahih muslim hadith"),
        ("Sunan Abu Dawud",
         "https://archive.org/download/SunanAbuDawudVol.2/Sunan%20Abu%20Dawud,%20vol.%201_djvu.txt",
         "hadith_abu_dawud.txt", "abu dawud sunan hadith"),
        ("Sunan Ibn Majah",
         "https://archive.org/download/sunanibnmajahvolume1/Sunan%20Ibn%20Majah%20-%20Volume%201_djvu.txt",
         "hadith_ibn_majah.txt", "ibn majah sunan hadith"),
    ]
    for book, url, out, sawal_kw in sources:
        print("DOWNLOAD:", book, flush=True)
        t0 = time.time()
        txt_raw = fetch(url)
        if not txt_raw:
            print("   !! FAILED - skip")
            continue
        txt = sanitize(txt_raw)
        print("   raw=%d cleaned=%d chars (%.1fs)" % (len(txt_raw), len(txt), time.time() - t0))
        if len(txt) < 60:
            print("   !! TOO SHORT - skip")
            continue
        kw = keywords(txt) or sawal_kw
        entry = "Sawal: %s\nJawab: %s\n\n" % (kw, txt)
        with open(os.path.join(OUT_DIR, out), "w", encoding="utf-8") as f:
            f.write(entry)
        print("   SAVED:", out, flush=True)
    print("HADITH_FETCH_DONE")


if __name__ == "__main__":
    main()
