# -*- coding: utf-8 -*-
"""_gamesdata.py — GAMES + GENERAL-KNOWLEDGE live-collector (user ka hukum:
google/wikis pr ja kr random words, health-education, gender-topics aur
SPECIALY MINECRAFT + all-games ka data collect karke brain me store karna —
Sawal:/Jawab: pairs me, samajhne-ke-liye).

Qanoon (pakka):
  - net_guard L1 firewall LAGA kar — whitelist ke siwa KUCH nahi
  - Doosre AI-API hosts HARD-BLOCK (openai/gemini/anthropic/...) — waise hi
  - Sirf READ: minecraft.wiki + wikipedia (educational, scientific, modest)
  - Jo aaye wo ASCII-pak bana kar data/corpus_big/games_knowledge.txt me
    Sawal:/Jawab: pairs ke tor par INSTALL hota hai
  - Dedup (sha1) — ek hi ilm dobara nahi likha jata
"""
import hashlib
import html as _html
import io
import json
import os
import re
import sys
import time
import urllib.parse

import requests            # certifi CA-bundle (urllib ka SSL is PC par purana)

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                              errors="replace")
sys.path.insert(0, r"D:\DigitalBrain")
os.chdir(r"D:\DigitalBrain")

from harvest import net_guard            # noqa: E402
net_guard.install()                      # L1 firewall (whitelist-only)

OUT = os.path.join("data", "corpus_big", "games_knowledge.txt")
SEEN_F = os.path.join("harvest", "seen_games.json")
_hdrs = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "HMHS-GamesKnowledge-Collector; offline NumPy AI")}
# ⚠️ minecraft.wiki (Cloudflare) Mozilla-prefixed UA ko 403 karta hai —
#    wahan ke liye chhota saaf UA (test-proven 200)
_hdrs_mc = {"User-Agent": ("HMHS-GamesKnowledge-Collector/1.0 "
                           "(offline NumPy AI; contact: laptopshampoo@gmail.com)")}
GAP = 2.5                                # site ka ehtram — request ke darmiyan

# ─── topics ─────────────────────────────────────────────────────────────
MINECRAFT = (                        # 🎮 SPECIAL: minecraft (user ka hukum)
    "Creeper", "Enderman", "Villager", "Netherite", "Redstone circuit",
    "Enchanting", "Nether", "The End (Minecraft)", "Ender Dragon", "Zombie",
    "Skeleton", "Spider", "Crafting table", "Furnace", "Smelting", "Biome",
    "Overworld", "Diamond (item)", "Obsidian", "Bedrock", "TNT", "Bow",
    "Sword", "Pickaxe", "Mining", "Farming", "Breeding", "Trading",
    "Daylight cycle", "Weather", "Speedrun", "Hardcore", "Multiplayer",
    "Server", "Realms", "Skin", "Mod", "Texture pack", "Snapshot", "Mob",
)
GAMES = (                            # 🕹️ baqi mashhoor games
    "Tetris", "Pac-Man", "Super Mario", "Pokémon", "Roblox", "Fortnite",
    "Among Us", "Candy Crush Saga", "Subway Surfers", "Temple Run",
    "Clash of Clans", "PlayerUnknown's Battlegrounds", "Garena Free Fire",
    "Call of Duty", "FIFA (video game series)", "Grand Theft Auto",
    "Minecraft Dungeons", "Minecraft Legends", "Chess", "Carrom", "Ludo",
    "Scrabble", "Sudoku", "Rubik's Cube", "Esports", "Speedrunning",
    "Game development", "Video game design", "Level design",
    "Game mechanics",
)
GENERAL = (                          # 🌍 random words / general-knowledge
    "Compass", "Telescope", "Lighthouse", "Clock", "Paper", "Ink", "Mirror",
    "Button", "Zipper", "Umbrella", "Candle", "Soap", "Toothbrush", "Bicycle",
    "Kite", "Pyramid", "Bridge", "Tunnel", "Lever", "Pulley", "Wheel",
    "Magnet", "Battery", "Light bulb", "Ruler", "Globe", "Atlas", "Library",
    "Museum", "Dictionary",
)
HEALTH = (                           # 🩺 health-education (scientific, modest)
    "Sex education", "Puberty", "Adolescence", "Human reproductive system",
    "Menstrual cycle", "Reproduction", "Personal hygiene", "Pregnancy",
    "Childbirth", "Nutrition", "Mental health", "Sleep hygiene",
    "Physical exercise", "Human body", "Immune system",
)
GENDER = (                           # ⚖️ gender-topics (educational/sociology)
    "Gender", "Gender role", "Gender equality", "Women's rights",
    "Sex differences in humans", "Gender studies", "Third gender",
    "Gender neutrality", "Men's health", "Gender identity",
)


def _get(url, timeout=15):
    ok, why = net_guard.check(url)
    if not ok:
        return None
    try:
        r = requests.get(url, headers=_hdrs, timeout=timeout)
        if r.status_code != 200:
            return None
        return r.text
    except Exception:
        return None


def _ascii(text, cap=900):
    t = re.sub(r"[^\x20-\x7e\n]", " ", text or "")
    t = re.sub(r"[ \t]{2,}", " ", t)
    t = re.sub(r"\n{2,}", "\n", t).strip()
    return t[:cap]


def wiki_summary(topic):
    u = ("https://en.wikipedia.org/api/rest_v1/page/summary/"
         + urllib.parse.quote(topic.replace(" ", "_")))
    j = _get(u)
    if not j:
        return None
    try:
        d = json.loads(j)
        ext = (d.get("extract") or "").strip()
        return ext if len(ext) > 80 else None
    except Exception:
        return None


def wiki_extract(topic, cap=4000):
    u = ("https://en.wikipedia.org/w/api.php?action=query&format=json"
         "&prop=extracts&explaintext=1&redirects=1&titles="
         + urllib.parse.quote(topic))
    j = _get(u)
    if not j:
        return None
    try:
        d = json.loads(j)
        for _pid, pd in d.get("query", {}).get("pages", {}).items():
            ext = (pd.get("extract") or "").strip()
            if len(ext) > 500:
                return ext[:cap]
    except Exception:
        return None
    return None


def _get_mc(url, timeout=15):
    ok, why = net_guard.check(url)
    if not ok:
        return None
    try:
        r = requests.get(url, headers=_hdrs_mc, timeout=timeout)
        if r.status_code != 200:
            return None
        return r.text
    except Exception:
        return None


def mcwiki_extract(topic, cap=4000):
    """minecraft.wiki MediaWiki API — gehra game-ilm (net_guard-whitelisted)."""
    u = ("https://minecraft.wiki/api.php?action=query&format=json"
         "&prop=extracts&explaintext=1&redirects=1&titles="
         + urllib.parse.quote(topic))
    j = _get_mc(u)
    if not j:
        return None
    try:
        d = json.loads(j)
        for _pid, pd in d.get("query", {}).get("pages", {}).items():
            if "extract" in pd:
                ext = (pd["extract"] or "").strip()
                if len(ext) > 300:
                    return ext[:cap]
    except Exception:
        return None
    return None


def _load_seen():
    try:
        with open(SEEN_F, encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def _save_seen(seen):
    try:
        with open(SEEN_F, "w", encoding="utf-8") as f:
            json.dump(sorted(seen)[-60000:], f)
    except Exception:
        pass


def _pairs_for(topic, text, kind):
    """Ek extract se 3-6 Sawal:/Jawab: pairs (samajhne-ke-liye)."""
    out = []
    paras = [p.strip() for p in text.split("\n") if len(p.strip()) > 120]
    if not paras:
        return out
    lead = paras[0][:600]
    out.append("Sawal: %s kya hai (%s)?\nJawab: %s" % (topic, kind, lead))
    q_templates = ("%s ke baare me 3 ahem baatein batao (%s)",
                   "%s kaise kaam karta hai (%s)?",
                   "%s ki ahmiyat kya hai (%s)?",
                   "%s — mazeed tafseel (%s)")
    for i, p in enumerate(paras[1:5]):
        out.append("Sawal: %s\nJawab: %s"
                   % (q_templates[i % len(q_templates)]
                      % (topic, kind), p[:700]))
    return out


def install(pairs):
    new = 0
    seen = _load_seen()
    with open(OUT, "a", encoding="utf-8", errors="replace") as f:
        for p in pairs:
            h = hashlib.sha1(p.encode("utf-8", "ignore")).hexdigest()
            if h in seen:
                continue
            seen.add(h)
            f.write(p + "\n\n")
            new += 1
    _save_seen(seen)
    return new


def harvest_minecraft(done):
    n = 0
    total = len(MINECRAFT)
    for t in MINECRAFT:
        done[0] += 1
        ext = mcwiki_extract(t)
        src = "minecraft"
        if not ext:
            ext = wiki_summary("Creeper (Minecraft)" if t == "Creeper" else t)
            src = "wikipedia"
        if not ext:
            print("  [%d/%d] %s — KUCH NAHI MILA" % (done[0], total, t),
                  flush=True)
            time.sleep(GAP)
            continue
        pairs = _pairs_for(t, _ascii(ext, 3500), src)
        d = install(pairs)
        n += d
        print("  [%d/%d] %s (%s) — %d pairs (naya-%d)"
              % (done[0], total, t, src, len(pairs), d), flush=True)
        time.sleep(GAP)
    return n


def harvest_wiki_topics(topics, kind, done, total):
    n = 0
    for t in topics:
        done[0] += 1
        ext = wiki_summary(t)
        if not ext:
            ext = wiki_extract(t, 3000)
        if not ext:
            print("  [%d/%d] %s — KUCH NAHI MILA" % (done[0], total, t),
                  flush=True)
            time.sleep(GAP)
            continue
        pairs = _pairs_for(t, _ascii(ext, 3000), kind)
        d = install(pairs)
        n += d
        print("  [%d/%d] %s — %d pairs (naya-%d)"
              % (done[0], total, t, len(pairs), d), flush=True)
        time.sleep(GAP)
    return n


def main():
    done = [0]
    total = len(MINECRAFT) + len(GAMES) + len(GENERAL) + len(HEALTH) + len(GENDER)
    t0 = time.time()
    print("🎮 GAMES+ILM COLLECTOR SHURU: %d topics | OUT: %s"
          % (total, OUT), flush=True)
    n = harvest_minecraft(done)
    n += harvest_wiki_topics(GAMES, "game", done, total)
    n += harvest_wiki_topics(GENERAL, "general-knowledge", done, total)
    n += harvest_wiki_topics(HEALTH, "health-education", done, total)
    n += harvest_wiki_topics(GENDER, "gender-topic", done, total)
    print("🎮 MUKAMMAL: %d naye pairs | %.1f min | file: %s"
          % (n, (time.time() - t0) / 60.0, OUT), flush=True)


if __name__ == "__main__":
    main()
