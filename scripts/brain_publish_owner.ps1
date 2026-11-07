# ============================================================
#  _brain_publish.ps1 - OWNER-TOOL (sirf HMHS ke PC par)
#  Naya-tareen genmaster brain -> GitHub-release (tag: brain) par publish
#  + brain_manifest.json repo/sites par - 24/7 available (owner-PC off bhi
#  ho to bhi). Downloader UPDATE-BRAIN.bat isi manifest se taza dimagh
#  le leta hai. Yeh FILE-sync hai - koi AI/model/platform API nahi.
# ============================================================
$ErrorActionPreference = "Stop"
$gh = "C:\Program Files\GitHub CLI\gh.exe"
$tok = (& $gh auth token).Trim()
$H = @{ Authorization = "token $tok"; Accept = "application/vnd.github+json";
        "X-GitHub-Api-Version" = "2022-11-28"; "User-Agent" = "hemomemo-brain" }
$API = "https://api.github.com"
$repo = "noity0/hemomemo-ai"
$tag = "brain"

# --- 1) naya-tareen FINAL brain ---
$npz = Get-ChildItem "D:\DigitalBrain\model\checkpoints\genmaster_*.npz" |
       Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $npz) { "koi genmaster npz nahi - FAIL (honest)"; exit 1 }
$ver = if ($npz.BaseName -match "(\d+)$") { $Matches[1] } else { "0" }
$sha = (Get-FileHash $npz.FullName -Algorithm SHA256).Hash.ToLower()
$size = $npz.Length
Write-Host ("BRAIN: {0} | {1:N1} MB | v{2} | sha {3}..." -f $npz.Name, ($size/1MB), $ver, $sha.Substring(0,12))

# --- 2) manifest (dono-mirror URL) ---
$assetName = "Hemomemo-Brain-$ver.npz"
$man = [ordered]@{
  brain   = "hemomemo-master"
  version = $ver
  file    = $npz.Name
  file_path = "model/checkpoints/$($npz.Name)"
  size    = $size
  sha256  = $sha
  updated = (Get-Date -AsUTC -Format "yyyy-MM-ddTHH:mm:ssZ")
  url     = "https://github.com/$repo/releases/download/$tag/$assetName"
  note    = "owner-published brain (HMHS) - sirf file-sync, koi AI/model/platform API nahi; app bina iske bhi 100% local chalti hai"
}
$manJson = $man | ConvertTo-Json -Depth 3
foreach ($d in @("D:\DigitalBrain", "D:\DigitalBrain\web", "D:\DigitalBrain\web_surge", "D:\DigitalBrain\public")) {
  $manJson | Set-Content (Join-Path $d "brain_manifest.json") -Encoding UTF8
}
Write-Host "manifest likh diya (root + web + web_surge + public)"

# --- 3) release tag 'brain' (banao ya lo) ---
$rel = $null
try { $rel = Invoke-RestMethod -Uri "$API/repos/$repo/releases/tags/$tag" -Headers $H } catch {}
if (-not $rel) {
  $rel = Invoke-RestMethod -Method Post -Uri "$API/repos/$repo/releases" -Headers $H `
    -ContentType "application/json" `
    -Body (@{ tag_name = $tag; name = "Hemomemo Brain (owner-published)";
              body = "Naya-tareen Hemomemo master-brain (owner: HMHS). UPDATE-BRAIN.bat isi se dimagh taza karta hai. 100% local system - koi AI-API nahi."; draft = $false; prerelease = $false } | ConvertTo-Json)
  "release tag 'brain' ban gaya"
} else { "release tag 'brain' pehle se hai" }

# purana asset hatao
foreach ($a in @($rel.assets)) {
  if ($a.name -like "Hemomemo-Brain-*.npz") {
    Invoke-RestMethod -Method Delete -Uri "$API/repos/$repo/releases/assets/$($a.id)" -Headers $H
    "purana asset hata: $($a.name)"
  }
}

# --- 4) npz upload (release asset) ---
$uri = "$($rel.upload_url.Split("{")[0])?name=$assetName"
Invoke-RestMethod -Method Post -Uri $uri -Headers $H `
  -ContentType "application/octet-stream" -InFile $npz.FullName | Out-Null
Write-Host ("BRAIN-UP: {0} | state=uploaded" -f $assetName) -ForegroundColor Green

# --- 5) manifest repo par + Pages build ---
$shaEx = $null
try { $shaEx = (Invoke-RestMethod -Uri "$API/repos/$repo/contents/brain_manifest.json" -Headers $H).sha } catch {}
$fb = @{ message = "brain-publish: v$ver (owner HMHS) - file-sync manifest, no AI-API"; content = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($manJson)) }
if ($shaEx) { $fb.sha = $shaEx }
Invoke-RestMethod -Method Put -Uri "$API/repos/$repo/contents/brain_manifest.json" `
  -Headers $H -ContentType "application/json" -Body ($fb | ConvertTo-Json) | Out-Null
"PUSHED: brain_manifest.json"
try { Invoke-RestMethod -Method Post -Uri "$API/repos/$repo/pages/builds" -Headers $H | Out-Null; "PAGES-BUILD-TRIGGERED" } catch {}
"BRAIN-PUBLISH-DONE (ab downloader ka UPDATE-BRAIN.bat v$ver utha lega - chahe aap ka PC off ho)"
