# _apply_all.ps1 — FULL republish-chain (direct-steps, chain-replacement):
#   step-0: app-band (user-hukum: EXE-copy se pehle app band) + stale-chain/trainer kill
#   step-1: make_package (PyInstaller EXE-rebuild + package-refresh; ~15 min)
#   step-2: _apply_rest.ps1 (make_desktop_package -> _zip_web.py -> _publish_final.ps1)
$ErrorActionPreference = "Continue"
cd D:\DigitalBrain

"== STEP-0: app-band + stale-chain/trainer safai =="
taskkill /IM "Hemomemo-Ultra-Brain.exe" /F 2>$null
taskkill /IM "Hemomemo-GameBot.exe" /F 2>$null
Get-CimInstance Win32_Process -Filter "Name='python.exe' or Name='pythonw.exe'" |
  Where-Object { $_.CommandLine -match 'make_package|make_desktop_package|_apply_rest|_apply_training|_zip_web|_publish_final|train_deep5h' } |
  ForEach-Object { "stale PID " + $_.ProcessId + " band"; Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

"== STEP-1: MAKE-PACKAGE (EXE-rebuild, code-fix ke sath) =="
& "C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" -Xutf8 "D:\DigitalBrain\scripts\make_package.py"
"make_package rc=$LASTEXITCODE"
if ($LASTEXITCODE -ne 0) { "GUARD: make_package FAIL - ruk gaya (purana zip/release salamat)"; exit 1 }

"== STEP-2: DESKTOP-PACKAGE + FRESH-ZIP + PUBLISH =="
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\DigitalBrain\_apply_rest.ps1"
"apply_rest rc=$LASTEXITCODE"

"== APPLY-ALL-DONE =="
