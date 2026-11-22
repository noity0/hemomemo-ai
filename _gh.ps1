# GitHub pipeline: repo -> files -> Pages -> release+zip -> hifazat -> checks
$ErrorActionPreference = "Stop"
$gh = "C:\Program Files\GitHub CLI\gh.exe"
$tok = (& $gh auth token).Trim()
$H = @{ Authorization = "token $tok"; Accept = "application/vnd.github+json";
        "X-GitHub-Api-Version" = "2022-11-28"; "User-Agent" = "hemomemo-deploy" }
$repo = "hemomemo-ai"
$tag  = "v4.2.0-people"
$zipPath = "D:\DigitalBrain\web\HemomemoUltra-People.zip"
$API = "https://api.github.com"
$UP  = "https://uploads.github.com"

$me = Invoke-RestMethod -Uri "$API/user" -Headers $H
"user: $($me.login)"

try {
  $body = @{ name = $repo; description = "Hemomemo AI - 100% local AI for Windows (official download)";
             homepage = "https://$($me.login).github.io/$repo/"; private = $false;
             has_wiki = $false; auto_init = $true } | ConvertTo-Json
  Invoke-RestMethod -Method Post -Uri "$API/user/repos" -Headers $H `
    -ContentType "application/json" -Body $body | Out-Null
  "REPO-BANA: $repo"
} catch {
  if ($_.Exception.Response.StatusCode.value__ -eq 422) { "REMOOJOOD: $repo" }
  else { throw }
}
try {
  $pu = Invoke-RestMethod -Method Patch -Uri "$API/repos/$($me.login)/$repo" -Headers $H `
          -ContentType "application/json" -Body (@{ description = "Hemomemo AI - 100% local Muslim AI for Windows (official download)"; homepage = "https://$($me.login).github.io/$repo/"; private = $false } | ConvertTo-Json)
  "REPO-MOMBAN: desc=$($pu.description) hp=$($pu.homepage)"
} catch { "REPO-META-FAIL: " + $_.Exception.Message }

foreach ($f in @("index.html", "app.js", "style.css", "sitemap.xml", "robots.txt", ".nojekyll")) {
  $p = "D:\DigitalBrain\web\$f"
  if (-not (Test-Path $p)) { continue }
  $sha = $null
  try {
    $ex = Invoke-RestMethod -Uri "$API/repos/$($me.login)/$repo/contents/$f" -Headers $H
    $sha = $ex.sha
  } catch {}
  $b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($p))
  $fb = @{ message = "site: $f"; content = $b64 }
  if ($sha) { $fb.sha = $sha }
  Invoke-RestMethod -Method Put -Uri "$API/repos/$($me.login)/$repo/contents/$f" `
    -Headers $H -ContentType "application/json" -Body ($fb | ConvertTo-Json) | Out-Null
  "FILE-UP: $f"
}

$pReadme = "D:\DigitalBrain\README.md"
$shaR = $null
try {
  $exR = Invoke-RestMethod -Uri "$API/repos/$($me.login)/$repo/contents/README.md" -Headers $H
  $shaR = $exR.sha
} catch {}
$b64R = [Convert]::ToBase64String([IO.File]::ReadAllBytes($pReadme))
$fbR = @{ message = "site: README.md"; content = $b64R }
if ($shaR) { $fbR.sha = $shaR }
Invoke-RestMethod -Method Put -Uri "$API/repos/$($me.login)/$repo/contents/README.md" `
  -Headers $H -ContentType "application/json" -Body ($fbR | ConvertTo-Json) | Out-Null
"FILE-UP: README.md"

try {
  $pb = @{ source = @{ branch = "main"; path = "/" } } | ConvertTo-Json
  $pg = Invoke-RestMethod -Method Post -Uri "$API/repos/$($me.login)/$repo/pages" `
          -Headers $H -ContentType "application/json" -Body $pb
  "PAGES-ON: $($pg.html_url)"
} catch {
  if ($_.Exception.Response.StatusCode.value__ -eq 409) { "PAGES-PEHLE-SE-ON" } else { throw }
}

$live = $false
for ($i = 0; $i -lt 40; $i++) {
  Start-Sleep 6
  try {
    $b = Invoke-RestMethod -Uri "$API/repos/$($me.login)/$repo/pages/builds/latest" -Headers $H
    "build[$i]: $($b.status)"
    if ($b.status -eq "built") { $live = $true; break }
    if ($b.status -eq "errored") { break }
  } catch { "build-check: " + $_.Exception.Message }
}
if ($live) {
  try {
    $r = Invoke-WebRequest "https://$($me.login).github.io/$repo/" -UseBasicParsing -TimeoutSec 30
    "SITE-LIVE status=$($r.StatusCode) Hemomemo: " + ($r.Content -match "Hemomemo")
  } catch { "SITE-CHECK-FAIL: " + $_.Exception.Message }
}

$rel = $null
try {
  $rb = @{ tag_name = $tag; target_commitish = "main"; name = "Hemomemo AI $tag";
           body = "Official package (Windows 7 se 11 Pro, 64-bit). 100% local - koi cloud AI nahi.`nInstall: zip nikalen -> START-HEMOMO.bat chalayen." } | ConvertTo-Json
  $rel = Invoke-RestMethod -Method Post -Uri "$API/repos/$($me.login)/$repo/releases" `
           -Headers $H -ContentType "application/json" -Body $rb
  "RELEASE-BANA: $tag (id $($rel.id))"
} catch {
  if ($_.Exception.Response.StatusCode.value__ -eq 422) {
    $rel = Invoke-RestMethod -Uri "$API/repos/$($me.login)/$repo/releases/tags/$tag" -Headers $H
    "RELEASE-MOOJOOD: $tag (id $($rel.id))"
  } else { throw }
}

foreach ($a in $rel.assets) {
  if ($a.name -eq "HemomemoUltra-People.zip") {
    Invoke-RestMethod -Method Delete -Uri "$API/repos/$($me.login)/$repo/releases/assets/$($a.id)" -Headers $H | Out-Null
    "PURANA-ASSET-DELA"
  }
}

"UPLOAD-SHURU (124 MB - thoda waqt lag sakta)..."
$up = Invoke-RestMethod -Method Post `
      -Uri "$UP/repos/$($me.login)/$repo/releases/$($rel.id)/assets?name=HemomemoUltra-People.zip" `
      -Headers $H -ContentType "application/zip" -InFile $zipPath -TimeoutSec 3600
"ASSET-UP: $($up.name) | {0:N1} MB | state=$($up.state)" -f ($up.size / 1MB)

try {
  $rb2 = @{ name = "hifazat-main"; target = "branch"; enforcement = "active";
            conditions = @{ ref_name = @{ include = @("refs/heads/main"); exclude = @() } };
            rules = @(@{ type = "deletion" }, @{ type = "non_fast_forward" }) } | ConvertTo-Json -Depth 6
  Invoke-RestMethod -Method Post -Uri "$API/repos/$($me.login)/$repo/rulesets" `
    -Headers $H -ContentType "application/json" -Body $rb2 | Out-Null
  "HIFAZAT-ON: main delete/force-push band"
} catch {
  if ($_.Exception.Response.StatusCode.value__ -eq 422) { "HIFAZAT-PEHLE-SE" }
  else { "HIFAZAT-SKIP: " + $_.Exception.Message }
}

try {
  $hd = Invoke-WebRequest "https://github.com/$($me.login)/$repo/releases/download/$tag/HemomemoUltra-People.zip" `
          -Method Head -UseBasicParsing -TimeoutSec 60 -MaximumRedirection 5
  "DOWNLOAD-URL OK status=$($hd.StatusCode) size=$($hd.Headers['Content-Length'])"
} catch { "DOWNLOAD-CHECK-FAIL: " + $_.Exception.Message }
"GH-PIPELINE-DONE"
