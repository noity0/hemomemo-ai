# ============================================================
#  UPDATE-BRAIN.ps1 - Hemomemo BRAIN-LINK (owner-published dimagh)
#  Ye sirf OWNER ki khud-publish-ki-hui brain-file ka sync hai -
#  koi AI/model/platform API NAHI. Bina iske bhi app 100% chalti hai.
# ============================================================
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host "=== HEMOMEO BRAIN-LINK (sirf owner ki published files - no AI-API) ===" -ForegroundColor Cyan

# --- 1) local version ---
$verPath = Join-Path $root "data\brain_version.json"
$local = $null
if (Test-Path $verPath) {
    try { $local = Get-Content $verPath -Raw | ConvertFrom-Json } catch {}
}
if ($local) {
    Write-Host ("local brain : v{0} ({1})" -f $local.version, $local.file)
} else {
    Write-Host "local brain : nahi mila (pehli baar update)"
}

# --- 2) owner-published manifest (GitHub Pages -> Netlify mirror) ---
$urls = @("https://noity0.github.io/hemomemo-ai/brain_manifest.json",
          "https://hemomemo-ai.netlify.app/brain_manifest.json")
$man = $null
foreach ($u in $urls) {
    try {
        $raw = (Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 20).Content
        $man = $raw | ConvertFrom-Json
        Write-Host ("manifest    : v{0} ({1}) - {2}" -f $man.version, $man.file, $u) -ForegroundColor Green
        break
    } catch { Write-Host "manifest try fail: $u" }
}
if (-not $man) {
    Write-Host "manifest NAHI mila - internet/owner-publish dekho. App waise bhi apne local dimagh se 100% chalti hai." -ForegroundColor Yellow
    exit 1
}

# --- 3) naya hai? ---
if ($local -and ([string]$local.version) -eq ([string]$man.version)) {
    Write-Host "dimagh pehle se TAZA hai (v$($man.version)) - kuch nahi karna." -ForegroundColor Green
    exit 0
}

# --- 4) download + SHA-256 tasdeeq (koi shak nahi - verify pakka) ---
$dst = Join-Path $root $man.file_path
$tmp = Join-Path $env:TEMP $man.file
Write-Host ("download     : {0} ({1:N1} MB)…" -f $man.file, ($man.size / 1MB))
& curl.exe -sL -o $tmp $man.url
if (-not (Test-Path $tmp)) { Write-Host "download FAIL (honest)" -ForegroundColor Red; exit 1 }
$hash = (Get-FileHash $tmp -Algorithm SHA256).Hash.ToLower()
if ($hash -ne $man.sha256) {
    Write-Host "SHA-256 MISMATCH - file maana (fail-closed, koi jhoot nahi)" -ForegroundColor Red
    Remove-Item $tmp -Force
    exit 1
}
Write-Host "SHA-256 OK   : $hash" -ForegroundColor Green

# --- 5) install (read-only hatao -> naya rakho -> wapas protect) ---
$ckDir = Join-Path $root "model\checkpoints"
New-Item $ckDir -ItemType Directory -Force | Out-Null
if (Test-Path $dst) { attrib -r $dst | Out-Null; Remove-Item $dst -Force }
Move-Item $tmp $dst -Force
attrib +r $dst | Out-Null

# purane extra genmaster (wahi version ke ilawa) ko archive nahi - seedha rehne do
$verObj = [ordered]@{ version = [string]$man.version; file = $man.file;
                      sha256 = $hash; updated = (Get-Date -Format s) }
$verPath2 = Join-Path $root "data\brain_version.json"
$verObj | ConvertTo-Json -Compress | Set-Content $verPath2 -Encoding UTF8

Write-Host ("BRAIN-UPDATED: v{0} - ab app (ya agent) dobara chalao, naya dimagh lag jayega." -f $man.version) -ForegroundColor Green
Write-Host "Yaad rahe: yeh OWNER ki apni publish-ki-hui file thi - kisi AI-API se koi taluq nahi."
exit 0
