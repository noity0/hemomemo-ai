# _publish_final.ps1 — SAB-JAGAH apply (usa-ki-order):
# zip → GitHub-release (replace) → repo-push (agent + sites) → Netlify.
# Pehle _rebuild_final.ps1 chal chuka ho aur QA numbers le liye hon (README).
param()
$ErrorActionPreference = "Continue"
cd D:\DigitalBrain

"== 1) WEB-ZIP (complete-final copy - desktop-app final zip, qanoon ke mutabiq) =="
# Qanoon: users ko sirf desktop-app ki final zip jati hai. Root-folder ka doobara
# re-zip 2GB+ ban jata hai (GitHub 2GB asset limit se barh jata hai) - is liye
# Web/HemomemoUltra-People.zip jo apply-chain ne complete-final zip se copy kiya
# (419MB) usi ko upload kiya jata hai. NOTE: is file me SIRF ASCII (em-dash etc.
# PowerShell 5.1 ke no-BOM ANSI-parse ko tor deta hai - 23:19 wala fail).
$z = Get-Item "D:\DigitalBrain\web\HemomemoUltra-People.zip"
"WEB-ZIP: $z.Name | $([math]::Round($z.Length / 1MB,1)) MB | $z.LastWriteTime"

"== 2) RELEASE-UPLOAD (same download-link, naya zip) =="
powershell -ExecutionPolicy Bypass -File "D:\DigitalBrain\_upload_zip.ps1" 2>&1 | Select-Object -Last 5

"== 3) REPO-PUSH (source + sites + manifest) =="
powershell -ExecutionPolicy Bypass -File "D:\DigitalBrain\_push_agent.ps1" 2>&1 | Select-Object -Last 8

"== 4) PAGES-BUILD-TRIGGER (GitHub Pages) =="
try {
    Invoke-RestMethod -Method Post `
        -Uri "https://api.github.com/repos/noity0/hemomemo-ai/pages/builds" `
        -Headers @{ Authorization = "token $((& 'C:\Program Files\GitHub CLI\gh.exe' auth token).Trim())"; Accept = "application/vnd.github+json"; "User-Agent" = "hemomemo-deploy" } | Out-Null
    "PAGES-BUILD-TRIGGERED"
} catch { "PAGES-SKIP: $($_.Exception.Message)" }

"== 4b) WEB-SURGE-SYNC (web -> web_surge - Netlify par hamesha latest) =="
# .md QA-files aur 244MB zip Netlify par NAHI jate (download-link GitHub
# release se aata hai); .nojekyll + netlify.toml web_surge me qaim rehte hain.
robocopy "D:\DigitalBrain\web" "D:\DigitalBrain\web_surge" /E /NFL /NDL /NJH /NJS /XF "LIVE-KARO.md" "DEPLOY.md" "*.zip" | Out-Null
if ($LASTEXITCODE -ge 8) { "SURGE-SYNC-WARN rc=$LASTEXITCODE" } else { "SURGE-SYNC-OK rc=$LASTEXITCODE" }

"== 5) NETLIFY-DEPLOY (hemomemo-ai.netlify.app) =="
if (Test-Path "D:\DigitalBrain\_netlify_deploy.ps1") {
    powershell -ExecutionPolicy Bypass -File "D:\DigitalBrain\_netlify_deploy.ps1" 2>&1 | Select-Object -Last 6
} else { "NETLIFY-SCRIPT-GHAIB - skip (honest)" }

"== PUBLISH-SAB-DONE =="
