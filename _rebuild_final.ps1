# _rebuild_final.ps1 — FINAL rebuild
param()
$ErrorActionPreference = "Continue"
cd D:\DigitalBrain

"== 1) APP-KILL =="
taskkill /IM Hemomemo-Ultra-Brain.exe /F 2>&1 | Out-String
Start-Sleep 3

"== 2) MAKE-PACKAGE =="
py -3 scripts\make_package.py 2>&1 | Select-Object -Last 5

"== 3) APP-START =="
Start-Process -FilePath "D:\HemomemoUltra-People\Hemomemo-Ultra-Brain.exe" `
    -WorkingDirectory "D:\HemomemoUltra-People"
$ok = $false
foreach ($i in 1..45) {
    Start-Sleep -Milliseconds 2000
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:8790/" -UseBasicParsing -TimeoutSec 3
        if ($r.StatusCode -eq 200) { $ok = $true; break }
    } catch {}
}
if ($ok) { "APP-READY" } else { "APP-NOT-READY" }
