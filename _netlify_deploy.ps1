# _netlify_deploy.ps1 — hemomemo-ai.netlify.app deploy (honest, no fake)
# Token ki jagah: (a) env NETLIFY_AUTH_TOKEN, ya (b) D:\DigitalBrain\.netlify_token.txt
$ErrorActionPreference = "Stop"

$siteDir = "D:\DigitalBrain\web_surge"
$siteArg = "hemomemo-ai.netlify.app"

# 1) Token dhoondo
$tok = $env:NETLIFY_AUTH_TOKEN
if (-not $tok -and (Test-Path "D:\DigitalBrain\.netlify_token.txt")) {
    $tok = (Get-Content "D:\DigitalBrain\.netlify_token.txt" -Raw).Trim()
}
if (-not $tok) {
    "NETLIFY-TOKEN-GHAIB - deploy skip (honest)."
    "Token banane ka tareeqa: https://app.netlify.com/user/applications#personal-access-tokens"
    "Phir paste karo: D:\DigitalBrain\.netlify_token.txt  (ya env NETLIFY_AUTH_TOKEN)"
    exit 2
}

# 2) npx netlify-cli se prod deploy
# (PS 5.1 me native-stderr 2>&1 + EAP=Stop 'npm warn' par NativeCommandError
#  deta tha — is liye: EAP=Continue + cmd /c: stderr khamosh-sach, rc sach.)
"NETLIFY-DEPLOY-SHURU: $siteDir -> $siteArg"
$ErrorActionPreference = "Continue"
$env:NETLIFY_AUTH_TOKEN = $tok

$ok = $false
for ($i = 1; $i -le 3; $i++) {
    "NETLIFY-ATTEMPT $i/3..."
    cmd /c "npx --yes netlify-cli@latest deploy --prod --dir `"$siteDir`" --site $siteArg --no-build 2>&1" 2>&1 |
        ForEach-Object { "$_" } | Select-Object -Last 12
    if ($LASTEXITCODE -eq 0) { $ok = $true; break }
    if ($i -lt 3) {
        "netlify attempt $i fail (exit=$LASTEXITCODE) - 30s baad dobara..."
        Start-Sleep -Seconds 30
    }
}
if ($ok) { "NETLIFY-UPLOAD-OK" } else { "NETLIFY-FAIL (3 koshish ke baad bhi)" }
