# _push_keyfix.ps1 — hemo-prefix key-system (code + sites + tests) repo-push
$ErrorActionPreference = "Stop"
$gh = "C:\Program Files\GitHub CLI\gh.exe"
$tok = (& $gh auth token).Trim()
$H = @{ Authorization = "token $tok"; Accept = "application/vnd.github+json";
        "X-GitHub-Api-Version" = "2022-11-28"; "User-Agent" = "hemomemo-deploy" }
$API = "https://api.github.com"
$repo = "noity0/hemomemo-ai"

$files = @(
  @{ local = "D:\DigitalBrain\server\accounts.py";           remote = "server/accounts.py" },
  @{ local = "D:\DigitalBrain\server\hemomemo_server.py";      remote = "server/hemomemo_server.py" },
  @{ local = "D:\DigitalBrain\app\hemomemo_app.py";            remote = "app/hemomemo_app.py" },
  @{ local = "D:\DigitalBrain\scripts\make_package.py";      remote = "scripts/make_package.py" },
  @{ local = "D:\DigitalBrain\tests\test_key_lifecycle.py";  remote = "tests/test_key_lifecycle.py" },
  @{ local = "D:\DigitalBrain\README.md";                    remote = "README.md" },
  @{ local = "D:\DigitalBrain\web\index.html";               remote = "index.html" },
  @{ local = "D:\DigitalBrain\web\index.html";               remote = "public/index.html" },
  @{ local = "D:\DigitalBrain\web\robots.txt";               remote = "robots.txt" },
  @{ local = "D:\DigitalBrain\web\robots.txt";               remote = "public/robots.txt" },
  @{ local = "D:\DigitalBrain\web\sitemap.xml";              remote = "sitemap.xml" },
  @{ local = "D:\DigitalBrain\web\sitemap.xml";              remote = "public/sitemap.xml" }
)

foreach ($f in $files) {
  $sha = $null
  try {
    $ex = Invoke-RestMethod -Uri "$API/repos/$repo/contents/$($f.remote)" -Headers $H
    $sha = $ex.sha
  } catch {}
  $b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($f.local))
  $fb = @{ message = "fix: API keys ab hemo-prefix (Hemomemo apni keys — gk_ purani auto-migrate) + key-lifecycle test"; content = $b64 }
  if ($sha) { $fb.sha = $sha }
  try {
    Invoke-RestMethod -Method Put -Uri "$API/repos/$repo/contents/$($f.remote)" `
      -Headers $H -ContentType "application/json" -Body ($fb | ConvertTo-Json) | Out-Null
    "PUSHED: $($f.remote)"
  } catch { "FAIL: $($f.remote) - " + $_.Exception.Message }
}

try {
  Invoke-RestMethod -Method Post -Uri "$API/repos/$repo/pages/builds" -Headers $H | Out-Null
  "PAGES-BUILD-TRIGGERED"
} catch { "TRIGGER-SKIP" }
"KEYFIX-PUSH-DONE"
