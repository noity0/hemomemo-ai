# 🤖 Hemomemo AI — AUTONOMOUS REASONING ENGINE (FULLY AUTONOMOUS UPGRADE)

> **Hemomemo AI ko ab bilkul fully autonomous bana diya.** Koi AI-API, koi pretrained AI,
> koi ollama, koi cloud, koi model-connection, koi external AI-helper use NAHI karta.
> Poora jawab **local algorithmic reasoning engine** se aata hai:
> **algorithms → logic → inference → knowledge graph → context → math → hypothesis → self-verify → speak**.

---

## 🔄 AUTONOMOUS PIPELINE (har sawal ek NAA-change machine-flow)

```
📥 READ     → normalize + tokenize + pattern/intent scan (pure regex)
🧭 FOCUS    → kind classify: chit-chat | identity | sacred | math | how | factoid | compare | logic | unknown
              (kachra/noise input jaise `fdsf`/`ho` → `unknown` → seedha imandari, greeting-spam NAHI)
📚 RECALL   → local knowledge: QA-pairs (corpus + Quran + 7 Sahih books) + KnowledgeGraph + owner data
🌐 RESEARCH → live web: google → duckduckgo → bing → wikipedia (whitelist-only page-reads, NO AI)
⚙️ REASON   → math engine (safe AST eval) OR best local hypothesis OR logic inference
🪞 VERIFY   → self-check: recompute math, source-trust scoring, fabrication-safe checks
✍️ SPEAK    → answer compose + reasoning steps + facts-vs-assumptions + uncertainty + confidence
```

## 🧠 ENGINE MODULES (D:\DigitalBrain\model\autonomous.py)

| Unit | Kya karta hai |
|---|---|
| `classify()` | sawal ki qism (math/logic/fact/sacred/how/chit-chat/identity) — pattern recognition |
| `KnowledgeGraph` | entities + relations + facts store (get / related / all) |
| `local_qa()` / `sacred_answer_text()` | corpus + sacred books ka QA retrieval |
| `owner_answer()` | owner (Hemomemo AI ka creator) ka local sahi jawab |
| `_expr_from` / `_eval_node` / `math_answer()` | safe AST math engine (no eval, stepwise steps, word-problems) |
| `_live_research()` | live google/ddg/bing/wikipedia research (via `model.live_research`) |
| `_score_candidate()` | hypothesis generation + source-trust ranking (confidence 0..1) |
| `answer()` | final decision: best candidate / honest fallback |
| `chat()` / `chat_loop()` | answer + report (text + reasoning meta) |

### Confidence & honesty contract
- **algorithm / math** → confidence ≈ 1.0, **verified = True** (recompute hua).
- **local knowledge / sacred / owner** → verified = True (local copy evidence).
- **live research** → verified = **False**, uncertainty = `live-research-unverified` — web-derived hua, ilm incomplete ho sakta hai.
- **fallback** → confidence ≈ 0.35, uncertainty = `insufficient-evidence` — "best possible from available info" + facts-vs-assumptions.

> ❌ **Koi nakli ayat / nakli hadith / koi fabricated jumla kabhi nahi banegi** — sacred + fabrication guards (`knowledge/quran_guard.py`, live_research faith-clean) ka istemaal hota rahega.

## 🔌 INTEGRATION (Hemomemo AI → fully autonomous chat)

### 🧩 EIK HI SYSTEM (unified chat — single entry)
- `run.py` ka **menu 5 aur menu 9 dono** → `model/generate.py::chat_loop` (ek hi full-system chat).
- Har sawal ke andar SAB kuch chalta hai: 🧠 master-LSTM khud-soch + 🧠🧠 brain2 (deep rescue) +
  ❤️ heart (strength/pulse) + 🤖 autonomous engine + 🌐 live research + 🪞 metacognition + yaad.
- `model/autonomous.py::chat_loop` sirf direct `py -3 model/autonomous.py` run ke liye hai.

### 🤖 ADOPTION RULES (engine ka jawab kab final hota hai)
- (a) pehla rasta kharab (`imaandari`/`tarbiyat`/`grace`/`deep-soch`) AUR engine candidate conf ≥ 0.40
      (live-research/local rescue) → engine ka jawab = final jawab.
- (b) engine khud-se verified (`algorithm`/`math`, conf ≥ 0.60) → adopt.
- (c) sawal kachra/noise (`unknown`, gib) → honest imandari jawab LSTM ke be-meaning output par.
- Meta me `m["autonomous"] = {answer, source, confidence, kind}` — status-line me bhi dikhata hai.
- ❤️ Dil: adopted confident jawab par `core.heart.note_autonomous()` → strength micro-step.

## 🖥️ TERMINAL USAGE (ab "online in terminal")

```powershell
cd D:\DigitalBrain
python model\autonomous.py "photosynthesis kya hai"     # one-shot
python model\autonomous.py                              # interactive terminal mode
python model\generate.py                                # terminal chat (ab fully autonomous)
python run.py → 9) Hemomemo AI                       # menu se bhi
```

Terminal commands: `quit` | `flow on|off|verbose` | `think low|mid|high|auto` | `status` | `clear`.

## 🌐 LIVE RESEARCH (deep, google live)

`model/live_research.py::_search` → **Google → DuckDuckGo Lite → Bing → Wikipedia** (whitelist-only,
koi AI-API NAHI; page-read se data). Islamic sawon par internet NAHI — sirf Quran + Sahih books.

## 🚫 HARD CONSTRAINTS (permanent)

1. No AI API / no cloud / no ollama / no external AI model / no AI-platform / no AI-helper.
2. Own model (pure NumPy LSTM) + own local reasoning engine (pure stdlib algorithms).
3. Net sirf whitelist (google/duckduckgo/bing/wikipedia/sunnah/hadith...) page-read par.
4. Quran READ-ONLY (hash-locked) + Sahih-only hadith policy.

## 🧪 TESTS

```powershell
py -3 scripts\_t_autonomous.py    # engine smoke tests (classify / math / answers)
```

---

## AQAL CORE (model/aqal.py) - Aiqal/Intellect upgrade
- **Chain-of-Thought**: sawal ko stepwise reasoning steps me tornA
- **Analogical**: milte-julte patterns (brain~computer, ilm~roshni...)
- **Causal**: kyun/kaise ka cause-effect chain
- **Deductive / Inductive / Abductive**: premises se conclusion, examples se rule, best explanation
- **Contradiction check + Evidence weighing + Self-correction + Fallacy detection**
- utonomous.answer() ke final candidates par eason() chalti hai aur aqal-steps jawab ki meta me hoti hain.

## FEELINGS SENSORS (model/feelings.py)
- Mood: khush / mutmain / hairan / udaas / bechain / mustaiq
- Senses: input-quality, emotion, urgency, novelty, consistency (hat-reflex removed kabhi nahi)

## SECURITY (ULTRA)
- erify_system_integrity(): sha256 file hash locks kaccha tamper alert + boot shutdown
- secure_sanitize(): prompt/commands injection block
- Quran guard: knowledge/quran_guard.py hash-locked Quran files

## UNIFIED MENU (run.py)
- Options 5 aur 9 merged - **eik hi full-system chat**: Hemomemo AI Chat (FULL SYSTEM).
- 
umpy absent hone par brain-simulation options graceful warning dikhate hain, chat menu band nahi hota.

## VOLATILE-FILE POLICY (pollution-guard)
- data/corpus_big/liveresearch.txt aur data/chat_learned_memory.json runtime files hain:
  - QA/vocab scan se EXCLUDED (gibberish-detection break na ho)
  - runtime pe regenerate hote hain; delete karna safe hai.

