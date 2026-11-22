# _apply_rest.ps1 — make_package ke baad ke steps (chain-ke-barabar, direct):
#   1) make_desktop_package (connection-hub + guide subfolder)
#   2) fresh zip + web-copy (_zip_web.py)
#   3) _publish_final.ps1 (release-upload + repo-push + Pages + netlify)
$ErrorActionPreference = "Continue"
cd D:\DigitalBrain
$py = "C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe"
# 📜 IMANDARI-LOG: har step ka asli output file me - koi chupchap-fail nahi
Start-Transcript -Path "D:\DigitalBrain\data\_apply_rest.log" -Append | Out-Null

"== 0) MAKE-PACKAGE (DigitalBrain -> desktop: naya code + EXE + dimagh) =="
& $py -Xutf8 "D:\DigitalBrain\scripts\make_package.py" 2>&1 | Tee-Object -FilePath "D:\DigitalBrain\data\_make_root_package.log" -Append
"make_package rc=$LASTEXITCODE"
if ($LASTEXITCODE -ne 0) { "GUARD: make-package FAIL - ruk gaya (adhura publish nahi)"; Stop-Transcript | Out-Null; exit 1 }

"== 1) MAKE-DESKTOP-PACKAGE =="
& $py -Xutf8 "D:\DigitalBrain\scripts\make_desktop_package.py" 2>&1 | Tee-Object -FilePath "D:\DigitalBrain\data\_make_package.log" -Append
"make_desktop_package rc=$LASTEXITCODE"
if ($LASTEXITCODE -ne 0) { "GUARD: desktop-package FAIL - ruk gaya (adhura publish nahi)"; Stop-Transcript | Out-Null; exit 1 }

"== 2) FRESH-ZIP + WEB-COPY =="
& $py -Xutf8 "D:\DigitalBrain\_zip_web.py" 2>&1 | Tee-Object -FilePath "D:\DigitalBrain\data\_zip_web.log" -Append
"zip rc=$LASTEXITCODE"
if ($LASTEXITCODE -ne 0) { "GUARD: zip FAIL - ruk gaya"; Stop-Transcript | Out-Null; exit 1 }

"== 3) PUBLISH (release + push + pages + netlify) =="
powershell -NoProfile -ExecutionPolicy Bypass -File "D:\DigitalBrain\_publish_final.ps1" 2>&1 | Tee-Object -FilePath "D:\DigitalBrain\data\_publish_final.log" -Append
"publish rc=$LASTEXITCODE"

"== APPLY-REST-DONE =="
Stop-Transcript | Out-Null
