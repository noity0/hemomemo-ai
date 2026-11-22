# _watch_cod.ps1 — 2h trainer ke Mukammal hote hi 20-min CODING-training
# khud start (checkpoint-takraav se bachne ke liye chain-watcher).
$ErrorActionPreference = "Continue"
Set-Location D:\DigitalBrain
$pat = '_train' + '2h'          # self-match se bachne ke liye jorh kar banaya
$deadline = (Get-Date).AddHours(4)
while ((Get-Date) -lt $deadline) {
    $p = Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
         Where-Object { $_.CommandLine -and $_.CommandLine.Contains($pat) }
    if (-not $p) { break }
    Start-Sleep -Seconds 60
}
"WATCHER: 2h trainer khatam — ab 20-min CODING-FOCUS training shuru"
$env:TRAIN_SECONDS = "1200"
$env:CODING_FOCUS  = "1"
$env:OMP_NUM_THREADS = "2"
$env:MKL_NUM_THREADS = "2"
py -3 -u _train2h.py 2>&1
"CODING-TRAINING-DONE"
