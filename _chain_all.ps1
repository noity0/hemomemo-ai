# _chain_all.ps1 — POORA CHAIN (user ka hukum):
#  [2h trainer khatam] -> STEP A: 2h-brain sab jagah apply (package+zip+publish)
#  -> STEP B: 20-min CODING training -> STEP C: 20-min GAMES/ILM training
#  -> STEP D: dono-trainings ka final brain sab jagah apply (package+zip+publish)
#  -> STEP E: QA-500
$ErrorActionPreference = "Continue"
Set-Location D:\DigitalBrain

# ── 1) 2h trainer ke khatam hone ka intezar ──
$pat = '_train' + '2h'
$deadline = (Get-Date).AddHours(3)
while ((Get-Date) -lt $deadline) {
    $p = Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
         Where-Object { $_.CommandLine -and $_.CommandLine.Contains($pat) }
    if (-not $p) { break }
    Start-Sleep -Seconds 45
}
"CHAIN: 2h trainer KHATAM — ab 2h-brain sab jagah apply"

# ── 2) STEP A: 2h-brain → package + zip + publish ──
py -3 scripts\make_package.py 2>&1 | Select-Object -Last 3
Compress-Archive -Path "D:\HemomemoUltra-People\*" `
  -DestinationPath "D:\DigitalBrain\web\HemomemoUltra-People.zip" -Force
"CHAIN: STEP-A zip tayyar — PUBLISH shuru (2h brain)"
pwsh -NoProfile -ExecutionPolicy Bypass -File D:\DigitalBrain\_gh.ps1 2>&1 |
  Select-Object -Last 4
"CHAIN: STEP-A PUBLISH-DONE (2h brain sab jagah)"

# ── 3) STEP B: 20-min CODING training ──
"CHAIN: CODING training SHURU"
$env:TRAIN_SECONDS = "1200"
$env:CODING_FOCUS  = "1"
$env:GAMES_FOCUS   = "0"
py -3 -u _train2h.py 2>&1 | Select-Object -Last 6
"CHAIN: coding training KHATAM"

# ── 4) STEP C: 20-min GAMES/ILM training (minecraft + games + health/gender) ──
"CHAIN: GAMES training SHURU"
$env:CODING_FOCUS = "0"
$env:GAMES_FOCUS  = "1"
py -3 -u _train2h.py 2>&1 | Select-Object -Last 6
"CHAIN: games training KHATAM"

# ── 5) STEP D: dono trainings ka final brain → sab jagah apply ──
py -3 scripts\make_package.py 2>&1 | Select-Object -Last 3
Compress-Archive -Path "D:\HemomemoUltra-People\*" `
  -DestinationPath "D:\DigitalBrain\web\HemomemoUltra-People.zip" -Force
"CHAIN: STEP-D zip tayyar — FINAL PUBLISH (dono brains)"
pwsh -NoProfile -ExecutionPolicy Bypass -File D:\DigitalBrain\_gh.ps1 2>&1 |
  Select-Object -Last 4
"CHAIN: STEP-D FINAL-PUBLISH-DONE"

# ── 6) STEP E: QA-500 (final package par) ──
"CHAIN: QA-500 SHURU"
py -3 -u _qa500.py 2>&1 | Select-Object -Last 8
"CHAIN-ALL-DONE"
