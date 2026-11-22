# HEMOMEMO-AI QANOON (imandari-ki-kitab — har-upgrade isko izzat-karega)

## QANOON-1: BACKGROUND/HIDDEN (16-Nov-2026 se, hamesha-ke-liye)
- Hemomemo-AI ki SARI zaroori-cheezein sirf **background/hidden** chalengi —
  screen ya front par **kabhi nahi** (server pythonw windowless, code-exec
  CREATE_NO_WINDOW=0x08000000, publish-chain self-hidden + IDLE priority).
- PC lag na kare: heavy-kaam hamesha **IDLE-priority**.
- Agar koi cmd/shell window screen par aaye aur wo **sirf Hemomemo-AI ki ho**
  → **permanently band** karo (root-cause fix, sirf chhupana nahi).
- Ghair-Hemomemo (chrome/edge/millida/BlueStacks/waghera) ko **chherna nahi**.
- Windows ke ~187 Microsoft-system-tasks kabhi nahi chhernge (system-law).
- `CreateExplorerShellUnelevatedTask` = Windows-explorer-helper — kabhi nahi chherna.

## QANOON-2: SOCH MEHANAT-SE, API-KE-BINA
- Koi AI-platform API/model/LLM nahi. Sirf **non-AI APIs** (math/wikipedia-type)
  + apna **NumPy dimagh** (TokenBrain soch-loop).
- **Koi AI-API-key nahi, koi AI-endpoint nahi, koi AI-connection nahi** —
  `/v1/chat/completions` sirf OpenAI-**shape** ka facade hai (tools/SDK ke liye);
  jawab hamesha apna local NumPy dimagh deta hai, koi bahar-call nahi (sabit:
  server/model chat-path me koi http/urlopen nahi).
- Owner-credentials zip/repo me **kabhi nahi** (netlify-token sirf
  `D:\DigitalBrain\.netlify_token.txt`).
- Video-gen **DISABLED** (delete nahi). Trainer **OFF**. QA-files zip/repo me **kabhi nahi**.

## QANOON-3: KAAM-KA-TAREEQA
- Chota-badlaav **ek-waqt** me. Har-qadam ke baad **tests**.
- README me sirf **test-sabit** claims (anjaan number = jhoot).

## 16-Nov-2026 WINDOW-QANOON KI TANZEEM (kya-band-hua)
- Scheduled-tasks DISABLED (auto-window ke tamam-tanur):
  Hemomemo9MTrainer (18-Nov: deleted), HemomemoApplyNow, HemomemoServerWatch (har-5-min .bat →
  cmd+powershell — yehi baar-baar-window ka asli-jurm tha), hmhs_24h_retrain,
  HMHS_KNOWLEDGE_HARVEST + 8 third-party (BlueStacksHelper, OneDrive
  Reporting/Startup, WpsExternal-startup, WpsUpdate, Firefox-BackgroundUpdate,
  SoftLanding×2). 10 third-party admin-locked (Avast×2, Opera×2, WPS×3,
  OneDrive Per-Machine Update, Firefox DefaultBrowserAgent, DriverMax Starter).
- QAIM-rahega (windowless, qanoon-mutabiq): Startup Run-key
  `HemomemoServer24x7` → pythonw `_server_watch.pyw` (har-5-min keepalive,
  `_server_OFF.flag` izzat-karta hai) — ye scheduled-task NAHI hai.
- Code-level hamesha-ke-liye: `model/code_exec.py` CREATE_NO_WINDOW,
  `app/hemomemo_app.py` ffprobe CREATE_NO_WINDOW, `mcp_link.py` pehle-se theek.
