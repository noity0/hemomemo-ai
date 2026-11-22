# 📚 Knowledge Zone — READ-ONLY AREAS

## 🕌 Quran Zone (`quran/`)
Complete Quran + **sab languages ki tarjume** (98+ languages, 400+ tarjume)
yahan install hote hain — `scripts/install_sacred_texts.py` hararta hai.

| File/folder | Kaam | Permission |
|---|---|---|
| `translations/{lang}-{translator}.min.json` | Alif-Lam-Meem se baqi harr ayat (har zuban) | **READ-ONLY (locked)** |
| `editions_index.json` | sab editions ki fehrist (author/language) | READ for AI |
| `quran_manifest.json` | SHA-256 fingerprint + lock time | audit proof |
| (urdu asli) `quran-urdu.txt` | Quran + Urdu tarjuma ( Jab aahey) | **READ-ONLY (locked)** |

### ✅ AI kya KAR sakta hai:
- Quran ki ayah **padhna, sunana, quote karna** (retrieval se)
- Tafseer/madad ke liye URL/verse dhoondhna

### ❌ AI kya KABHI nahi kar sakta:
- Quran file **edit / modify / delete / replace** (OS-level locked)
- Quran text ko **training corpus (`data/corpus.txt`)** me daalna — weights
  kabhi Quran text par train nahi hote (generation se protect)
- Koi "naya Quran" likhna — 100% mana hai

### 🔒 Enforcement
1. OS-level: `read-only` attribute + SHA-256 (`quran_manifest.json`)
2. Script-level: `scripts/prepare_quran.py` sirf READ-index banata hai
3. Chat-level: `knowledge/quran_guard.py` prompt scan → refusals + quotes

## 📖 Hadith Zone (`hadith/`)
**7 Sahih/Sihah kitabein** — sunnah.com (fawazahmed0/hadith-api) se:

| Book | Content |
|---|---|
| Sahih al-Bukhari | ~7,500 hadith (ara/eng/urd) |
| Sahih Muslim | ~7,500 hadith (ara/eng/urd) |
| Sunan an-Nasai | ~5,750 |
| Sunan Abi Dawud | ~5,270 |
| Jami at-Tirmidhi | ~3,950 |
| Sunan Ibn Majah | ~4,340 |
| Muwatta Malik | ~1,600 |

English text seedha **training corpus** (`data/corpus_big/hadith_*_english_full.txt`)
me jati hai (Sawal/Jawab style) — chat yaad-dahai me turant istemal hota hai.

## 🛡️ Source Policy — Qadiani MANA (`harvest/source_policy.py`)
- Sirf whitelisted hosts: raw.githubusercontent.com, cdn.jsdelivr.net
- ✅ Qadiani/Ahmadi/o gair-standard sources **aab EA manaa** hai:
  alislam.org, aaiil.org, Ahmadiyya, Qadiani, Mirza Ghulam — koi nahi
- ✅ Qadiani translators (Maulana Muhammad Ali, Sher Ali, Umm Muhammad,
  Rashad Khalifa) wale editions install NAHI hote
- Scan: har file install wahkt + `harvest/source_policy.py` se kabhi bhi

## 🧰 Installer
```powershell
python scripts\install_sacred_texts.py   # RESUME hota hai (dobara chalao safe)
# report: knowledge\_install\install_report.json
```
