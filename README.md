# ☪ Hemomemo AI — Apna Dimagh (100% Local AI — NO API, NO LLM, NO Cloud)

## ONE-CLICK DOWNLOAD - Latest ZIP (hamesha naya)

[![Download Latest ZIP](https://img.shields.io/badge/DOWNLOAD-Latest_ZIP_~215MB-2ea44f?style=for-the-badge&logo=github)](https://github.com/noity0/hemomemo-ai/releases/download/v4.2.0-people/HemomemoUltra-People.zip)
[![Saare Releases](https://img.shields.io/badge/Releases-Saare_Versions-0969da?style=for-the-badge&logo=github)](https://github.com/noity0/hemomemo-ai/releases)

**Ek click = poora app (~215 MB):** dimagh (LSTM) + ilm-corpus + GameBot + 24/7
connection-hub + web-search/Gmail powers - sab isi zip ke andar.

**Har naya update ISI HI link par aata hai** (naya zip purani file ki jagah
replace hota hai) - dobara click karo, naya zip mil jayega. Link kabhi purana
nahi hota.

| Step | Kya karo |
|---|---|
| 1 | Upar hary button par click -> `HemomemoUltra-People.zip` download |
| 2 | Zip extract karo (kisi bhi folder me) |
| 3 | `START-HEMOMO.bat` chalao - app khul jayega (**install ki zaroorat nahi**) |

Text-link (agar badge load na ho):
[HemomemoUltra-People.zip (latest)](https://github.com/noity0/hemomemo-ai/releases/download/v4.2.0-people/HemomemoUltra-People.zip)
| [Saare releases](https://github.com/noity0/hemomemo-ai/releases)

## HEMOMEMO POWERS (sab local ya non-AI API - koi AI-platform key nahi)

| Power | Hukum |
|---|---|
| Web-search | `search <topic>` / `khojo <topic>` |
| Deep Research | `deep research <topic>` (pages parh ke report + sources) |
| Code Execution | `python <code>` (local, timeout + net-guard) |
| Image Generation | `image banao <prompt>` (100% procedural - no AI-model) |
| Canvas | `canvas banao <naam>` / `canvas <naam> likho: ...` / `canvas list` |
| Gems (assistants) | `gem list` / `gem use Ustad` / `gem banao <naam> role: ...` |
| MCP | `mcp servers` / `mcp tools <srv>` / `mcp call <srv> <tool> {json}` |
| Gmail | `inbox check` / `send email to X subject: ... body: ...` |
| Google Drive/Docs | `drive list` / `drive upload <path>` / `doc read <naam>` |

**Qanoon (pakka):** dimagh 100% local (pure-NumPy LSTM) - OpenAI/Anthropic/
Gemini/generativelanguage jaisi HAR AI-platform API/connection net-guard me
**HARD-BLOCK** hai. Sirf non-AI APIs chalti hain (search, mail, storage).

---

**Hemomemo AI** apna **khud ka dimagh** hai - koi LLM nahi, koi bahar ka model nahi,
koi AI-API nahi, koi cloud nahi; MCP sirf LOCAL opt-in tool-bridge hai. Poora dimagh **pure-NumPy** ka
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

### 2) CODE — Code-Dimagh (45+ zabanen ka Ustad!)
- **45+ coding-zabanen** — har zaban me ASLI chhal-filar program khud banta hai
  (deterministic, token-se): Python, C, C++, C#, Java, JavaScript, TypeScript,
  Go, Rust, PHP, Ruby, Swift, Kotlin, Dart, Lua, Perl, Bash, PowerShell, R,
  MATLAB, SQL, HTML, CSS, JSON, YAML, Scala, Haskell, F#, Julia, Fortran,
  Pascal, Basic, VB, Zig, Nim, Crystal, Elixir, Clojure, Erlang, OCaml, D,
  Assembly (x86-64), COBOL, Tcl, Prolog, Lisp, Scheme, Racket, Objective-C.
- Roman rasta bhi: `python me i love you ka code` — English rasta bhi:
  `code hello world in c++`.
- Zaban-khazane me na ho to **imandari** — jhoot nahi, saaf bata deta hai
  kaunsi zabanen jaanta hoon.
- Jawab **code-block** mein — copy-button ke sath (desktop app).
- Coding knowledge: `coding_knowledge.txt` + `coding_deep_master.txt` (13,600+ bytes).

### 3) AGENT — Game-Bot Player (Minecraft + PC-eyes!) 🟩
**Sabse bada kaam:** Hemomemo **Minecraft mein player ki tarah** khelta hai!

- **Khud-join:** offline-mode/LAN Minecraft server par **khud join** hota hai
  (`py -3 -m agent.modes mc <host> [port]`).
  Chat parhta/likhta hai, aap ko salaam karta hai, aap ke sawalon ke jawab
  **apne local dimagh** se deta hai — live, game ke andar!
- **Aankhein (see):** bot **apni jagah, rukh, aakhri chat** parhta hai —
  `hal` hukum par aankhein kholta hai (`bot.see()`).
- **Harkat (move/look):** `chal` hukum par aage chalta hai, camera ghumaata
  hai (position/rotation packets — server hi haqeeqi jagah tay karta hai).
- **2 KIRDAR multi-play:** `py -3 -m agent.modes duo <host>` — **do kirdar**
  ek sath andar (aap ke sath multi — dono Hemomemo-dimagh wale).
- **PC-AANKH + HAATH** (kisi bhi game ke liye): `pc-watch` (screen dekhe +
  bataye) / `pc-play` (dekhe + WASD/mouse chalaye) — `agent/pc_eye.py` —
  PIL-screenshot + NumPy-tahlil + Windows SendInput (sirf stdlib, koi lib nahi).
- **Direct-mode:** bina server ke — aap terminal mein likho, bot sath khelta hai
  (`py -3 -m agent.modes agent`).
- **Token-dimagh (naya):** har sawal **token-dar-token parha** jata hai
  (`model/tokenize.py` + `model/understand.py`) — sawal samajh kar jawab,
  ban-input dump nahi. Jo nahi pata, **imandari-se mana** karta hai.
- **Faisla 100% local:** bot ka har jawab `model/understand.py` (token-soch +
  yaad + ilm + deterministic-math) se aata hai. **Koi AI-API game ke andar
  bhi nahi.**
- **Imandari-hadd:** online-mode (Mojang-auth) servers ke liye bahar ka auth
  chahiye hota hai — wo **jaan-boojh kar support nahi** (NO-API-law). Block-level
  khel (dig/build) ke liye optional `mcpi` hook diya gaya hai (server-side plugin).

DEEPLY-LINKED DIRECT (NO API-LAYER): `Hemomemo-GameBot.exe` desktop-app ke
folder mein rehta hai aur **seedha in-process Hemomemo-system** (model/ +
data/ isi folder se) istemal karta hai — koi HTTP-link nahi, koi key nahi,
koi API-layer nahi. App naya training ho, bot foran naya dimagh
istemal kare (ek hi dimagh ki files — sab apas mein jure).

TASK/SEKH-SYSTEM (starting se end, kabhi bhi — 100% local):
- `sekho <sawal> = <jawab>` — bot TOKEN-dar-token parhta hai, samajhta
  hai aur DATA-MEMORY me save karta hai (episodic-memory + tasks-file).
- `kaam <task> phir <qadam> …` — qadam-war-qadam plan → starting-se-end
  chalao → har qadam ka imandari nateeja → poora hisab memory me save.
- Dono hukum GameBot-console AUR Minecraft-chat dono jagah chalte hain.

GAMEBOT-EXE MENU (asli menu-strings, 100% sach - har claim ke peechay code):
- **[1] MC-JOIN** : bot khud aap ke Minecraft (TLauncher/SFX/XMLEMC - offline/LAN)
  mein login-enter-join karta hai — naya player ban kar aap ke sath multi khelta hai.
- **[2] MC-DUO** : 2 kirdar ek sath — aap ke sath multi (dono Hemomemo-dimagh wale).
- **[3] PC-DIRECT** : koi bhi game — bande ki screen parhe + control kare;
  **ESC dab-jab tak** = foran stop (GetAsyncKeyState, hifazat pehle).
- **[4] PC-WATCH** : sirf dekhe - jab tak ESC na dabey.
- **[5] BROWSER** : Obscura — URL dena → bot page parhta hai (local CDP, koi AI-API nahi).
- Orders dono jagah se: Agent-EXE console se AUR Minecraft-chat se
  (`Hemomemo chal / ruk / jump / ghum 180 / hal`) — ek hi parser (`agent/orders.py`).

Protocol: apna **VarInt-framing + handshake + login + chat + position** likha
gaya hai (`agent/mc_bot.py`) — koi SDK koi library zaroori nahi.

---

## 🧠 Brain-Link — Owner ke Published Dimagh Se Hamesha Jura

Zip lene wale ke paas sirf package hota hai (DigitalBrain main-folder sirf
owner HMHS ke paas). Phir bhi app **owner ke published brain** se juri
rahti hai:

- **Owner** (jab chahe naya dimagh publish kare): `scripts/brain_publish_owner.ps1`
  → naya genmaster GitHub-release (tag `brain`) par + `brain_manifest.json`
  repo/sites par — **24/7 available**, chahe owner ka PC off/soya ho.
- **Downloader**: package ke folder mein **`UPDATE-BRAIN.bat`** → owner ke
  published-brain ka naya version dekhta hai → download + **SHA-256 verify**
  → install. Sirf owner ki apni file-sync — **koi AI/model/platform API
  nahi**. Bina internet bhi app 100% chalti hai (offline-first qanoon).

---

## 📥 Download (Windows 7 → 11 Pro)

**GitHub:** https://github.com/noity0/hemomemo-ai/releases/tag/v4.2.0-people
→ **HemomemoUltra-People.zip** (~215 MB) → Extract All → **`Hemomemo-Ultra-Brain.exe`**

**Live sites:**
- 🌍 GitHub Pages: **https://noity0.github.io/hemomemo-ai/**
- 🌍 Netlify Mirror: **https://hemomemo-ai.netlify.app/**

App khulte hi **Hemomemo local API** khud ON: `http://127.0.0.1:8790`
(3 free API keys / account — `hemo…` keys, PBKDF2-hashed, 100% PC-par).

**API endpoints (Hemomemo API v1 — sab L6-guarded, wahi 1 dimagh jawab deta hai):**

- `POST /v1/chat` — native shape: `{"prompt": "..."}` → `{"answer", "meta"}`
- `POST /v1/chat/completions` — 🧩 **OpenAI-shape facade** (tools ke liye):
  messages[] bhejo, jawab apne local dimagh ka. Bearer-key chalega —
  OpenCode me provider `hemomemo/hemomemo-core`, baseURL `127.0.0.1:8790/v1`
  (config me sirf Hemomemo ka raasta — koi bahar-ki AI/llama/ollama nahi)
- `GET /v1/models` — OpenAI-shape list: `["hemomemo-core"]`
- `GET /health`, `GET /v1/info`, `POST /v1/auth/signup|signin`, `GET /v1/auth/me`
- Headers: `Authorization: Bearer hemo…` (ya `X-Hemomemo-Key` + fresh
  `X-Hemomemo-Ts`/`X-Hemomemo-Nonce`) — policy+rate L6-HMHZ se.

### 🌐 LAN mode (OPT-IN — owner PC on ke baad)
Default: Hemomemo local API **127.0.0.1:8790** (sirf isi PC — safety + law).
Opt-in: `START-HEMOMO-LAN.bat` (DigitalBrain + People package me) chalo —
ye **Hemomemo local API ko 0.0.0.0:8790 par** start karta hai. "Door ka user"
(kisi bhi device se) isi PC ki Hemomemo API use kar sake — lekin sirf owner PC
on ke baad, aur sirf is opt-in ke baad.

---

## 🛠️ Build (Windows workflow)

```
BUILD-WINDOWS.bat     <- 1) tests  2) EXE (PyInstaller)  3) package
py -3 tests\test_new_modules.py    <- honest tests (22 checks)
py -3 tests\test_token_brain.py    <- token-dimagh tests (20 checks)
py -3 tests\test_agent_powers.py   <- agent powers tests (42 checks)
py -3 tests\test_gamebot_50qa.py   <- game-bot control/read QA (50 checks)
py -3 scripts\make_package.py      <- package + SHA-256 manifest
```

Error-handling: har build-step fail hone par ruk kar **imandari error** dikhata hai
(koi jhooti "success" nahi).

### 🖥️ Cloud-Computer Browser (Obscura + Hemomemo — sirf Hemomemo)

- **Obscura** (headless browser: Rust, CDP/Puppeteer/Playwright/MCP): 
  https://github.com/h4ckf0r0day/obscura
- **Chalta hai:** `py -3 -m agent.browser_cloud start` (obscura serve :9222)
  → `py -3 -m agent.browser_cloud fetch <url> --dump text` (page fetch)
  → `py -3 -m agent.browser_cloud screenshot <url> <out.png>`
  → `py -3 -m agent.browser_cloud mcp start`
  → `py -3 -m agent.browser_cloud skill install` (SKILL.md hamesha Hemomemo-local)
- **Cloud-computer:** Obscura ka CDP-server us cloud-computer me run hota hai;
  Hemomemo usi se page fetch/screenshot/eval karti hai (koi AI-API nahi).
- GameBot menu me **[5] BROWSER** — URL dena → bot fetch + dikhata hai.

---

## 🔒 Security (6 layers — sab local)

L1 net-firewall (AI-API hosts HARD-BLOCK) · L2 input-guard · L3 integrity
(SHA-256 manifest, fail-closed) · L4 sacred-guard · L5 HMHZ secret-VM ·
L6 API-guard (local keys). Koi platform API / cloud / doosra AI — **nahi**
(MCP sirf LOCAL opt-in tool-bridge — koi network/AI-server nahi).

## 🧪 QA — Imandari

QA-500 + QA-700-hard + VIDEO-QA suites har release se pehle chalti hain.
**Nateeja jaisa hai waisa bataya jata hai** — koi nakli "success" nahi. Naye
dimagh-modules ke tests (memory / retrieval / reasoning / deterministic-math /
mc-bot protocol / token-dimagh / agent-powers / order-parser / console-orders /
task-sekh-system):

- ✅ token-dimagh: **20/20 PASS** (2026-11-08)
- ✅ agent-powers suite: **42/42 PASS** (2026-11-08)
- ✅ game-bot 50-QA: **PASS=50 FAIL=0 (of 50)** (2026-11-08)
- ✅ key-lifecycle: 11/11 PASS (live API, 2026-11-07)
- 🎬 VIDEO-QA v3 (25-check, photoreal engine): **20/25 PASS** (2026-11-08) — fixed resize bugs, prompt-override system live ✓

### 🎬 Video-Engine v3 (photoreal, 100% local)
- 🧠 **prompt-exact**: user's words drive scene (birds/rain/snow/city/lightning...) via prompt-override system
- 🎯 **max 50 min (3000s)** · 1280x720 · 24fps · supersample 1600x900 → BICUBIC downscale
- ⚡ **speed**: 528 ms/frame (~10s clip: 2-3 min wall, 60s clip: ~15 min wall)
- 🚫 **zero AI-API / cloud / MCP / platform-key** — only Hemomemo system (numpy/PIL/ffmpeg)
- 🌟 **styles**: golden (sun+birds+ocean), neon (city+rain+bokeh), storm (lightning+rain), winter (snow+halo), ocean (fog+birds), noir, space, dawn, dusk, night
- 💻 Desktop-app Video-tab: duration+fps+style + 🖼 still_preview with prompt overrides
- ✨ Flow-animation (READ→…→ANSWER HUD) local `agent/animation.py` me — har sawal
  ke neeche 10-marhalo ki animation (koi AI-API nahi); chat me "animation" likhne
  par Video-tab khulta hai (mp4 render)

**LIVE tasdeeq (apne PC par)**: GameBot ka PC-control asli chala kar dekha
(asli cursor-harkat + wapas-bilkul) ✓, aankh asli screenshot parh rahi ✓,
dimagh package ke hi model se jawab de raha ✓. Minecraft is-waqt band tha —
bot tayar hai: server chalte hi khud join karega (protocol 42/42 tests).

---

*Built with ❤️ by Hafiz Muhammed Huzaifa Shamim (HMHS) — Alhamdulillah,
100% local, 100% apna dimagh. MIT License.*
