# ☪ Hemomemo AI — Apna Dimagh (100% Local AI — NO API, NO LLM, NO Cloud)

**Hemomemo AI** apna **khud ka dimagh** hai — koi LLM nahi, koi bahar ka model nahi,
koi AI-API nahi, koi cloud nahi, koi MCP nahi. Poora dimagh **pure-NumPy** ka
**2-layer LSTM** hai (7M parameters), jo **aap ke apne PC par** chalta hai.

👤 **Owner / Creator:** Hafiz Muhammed Huzaifa Shamim (**HMHS**) — 17 saal ka student,
DJ Science College, Karachi. Email: laptopshampoo@gmail.com · Instagram: huzaifa_464
📜 **License:** MIT (yaqini azaadi — neeche LICENSE file dekho)

---

## 🧠 Apna Dimagh — LLM NAHI (Architecture)

Hemomemo **LLM-based app NAHI** hai. Ye apna **dimagh-tanaab** (neural + retrieval +
reasoning + yaad) hai:

```
 aap ka sawal
      |
      v
 +--------------+    +----------------+    +---------------------+
 | L1 net-guard | -> | L2 input-guard | -> | INTENT (pehchan)    |
 | (whitelist)  |    | (kachra-blok)  |    | math/coding/game/   |
 +--------------+    +----------------+    | islamic/general     |
                                           +----------+----------+
                                                      |
                     +--------------------------------+----------------+
                     |                                                 |
                     v                                                 v
        +---------------------+                        +------------------------+
        | YAAD (episodic)     |                        | ILM (knowledge corpus) |
        | episodic.jsonl      |                        | Sawal:/Jawab: pairs    |
        | token-overlap +     |                        | corpus_big/*.txt       |
        | recency-boost       |                        | keyword-retrieval      |
        +---------+-----------+                        +-----------+------------+
                  |                                                 |
                  +------------------> +----------------------------+
                                       v
                        +-----------------------------------+
                        | REASONING LOOP (model/reasoning)  |
                        | - math: DETERMINISTIC (pakka sahi)|
                        | - steps/plan banata hai           |
                        +----------------+------------------+
                                         |
                                         v
                        +-----------------------------------+
                        | COMPOSER (model/generate)         |
                        | apna 2-layer LSTM (NumPy, 7M)     |
                        | order-driven, template-NAHI       |
                        +----------------+------------------+
                                         |
                                         v
                        +-----------------------------------+
                        | L4 sacred-guard + L5 HMHZ-VM      |
                        +----------------+------------------+
                                         |
                                         v
                                   aap ko JAWAB
```

**Har hissa local hai:** yaad `data/memory/episodic.jsonl` par, ilm
`data/corpus_big/*.txt` par, dimagh `model/checkpoints/genmaster_*.npz` par —
sab **aap ke PC** par. Koi token, koi quota, koi bahar-ka-server — **nahi**.

---

## 🎮 Teen Kaam — Text, Code, AGENT (Minecraft Bot-Player)

Hemomemo AI ke **teen kaam** hain:

### 1) TEXT — Chat (apna dimagh)
- Sawal-jawab, ilm, islami-adab, general chat.
- Har baat **yaad** mein mehfooz (aap ke PC par) — agle jawab behtar.

### 2) CODE — Coding AI
- Python / JavaScript / Java / Kotlin / SQL / HTML / CSS / Bash / Rust / Go / PHP …
- Jawab **code-block** mein — copy-button ke sath (desktop app).
- Coding knowledge: `coding_knowledge.txt` + `coding_deep_master.txt` (13,600+ bytes).

### 3) AGENT — Game-Bot Player (Minecraft!) 🟩
**Sabse bada kaam:** Hemomemo **Minecraft mein player ki tarah** khelta hai!

- **Server-mode:** offline-mode/LAN Minecraft server se **join** karta hai
  (`py -3 -m agent.modes agent` ya `py -3 agent\mc_bot.py <server-host> <username>`).
  Chat parhta/likhta hai, aap ko salaam karta hai, aap ke sawalon ke jawab
  **apne local dimagh** se deta hai — live, game ke andar!
- **Direct-mode:** bina server ke — aap terminal mein likho, bot sath khelta hai
  (`py -3 -m agent.modes agent`).
- **Faisla 100% local:** bot ka har jawab `model/reasoning.py` (yaad + ilm +
  deterministic-math) se aata hai. **Koi AI-API game ke andar bhi nahi.**
- **Imandari-hadd:** online-mode (Mojang-auth) servers ke liye bahar ka auth
  chahiye hota hai — wo **jaan-boojh kar support nahi** (NO-API-law). Block-level
  khel (dig/build) ke liye optional `mcpi` hook diya gaya hai (server-side plugin).

Protocol: apna **VarInt-framing + handshake + login + chat** likha gaya hai
(`agent/mc_bot.py`) — koi SDK koi library zaroori nahi.

---

## 📥 Download (Windows 7 → 11 Pro)

**GitHub:** https://github.com/noity0/hemomemo-ai/releases/tag/v4.2.0-people
→ **HemomemoUltra-People.zip** (~131 MB) → Extract All → **`Hemomemo-Ultra-Brain.exe`**

**Live sites:**
- 🌍 GitHub Pages: **https://noity0.github.io/hemomemo-ai/**
- 🌍 Netlify Mirror: **https://hemomemo-ai.netlify.app/**

App khulte hi **Hemomemo local API** khud ON: `http://127.0.0.1:8790`
(3 free API keys / account — `hemo…` keys, PBKDF2-hashed, 100% PC-par).

---

## 🛠️ Build (Windows workflow)

```
BUILD-WINDOWS.bat     <- 1) tests  2) EXE (PyInstaller)  3) package
py -3 tests\test_new_modules.py    <- honest tests (22 checks)
py -3 scripts\make_package.py      <- package + SHA-256 manifest
```

Error-handling: har build-step fail hone par ruk kar **imandari error** dikhata hai
(koi jhooti "success" nahi).

---

## 🔒 Security (6 layers — sab local)

L1 net-firewall (AI-API hosts HARD-BLOCK) · L2 input-guard · L3 integrity
(SHA-256 manifest, fail-closed) · L4 sacred-guard · L5 HMHZ secret-VM ·
L6 API-guard (local keys). Koi platform API / cloud / MCP / doosra AI — **nahi**.

## 🧪 QA — Imandari

QA-500 suite har release se pehle chalti hai. **Nateeja jaisa hai waisa bataya
jata hai** — koi nakli "success" nahi. Naye dimagh-modules ke 22 tests
(memory / retrieval / reasoning / deterministic-math / mc-bot protocol) —
**22/22 PASS** (2026-11-07).

---

*Built with ❤️ by Hafiz Muhammed Huzaifa Shamim (HMHS) — Alhamdulillah,
100% local, 100% apna dimagh. MIT License.*
