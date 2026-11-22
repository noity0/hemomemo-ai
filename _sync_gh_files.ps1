# _sync_gh_files.ps1 — push index.html and robots.txt to both GitHub repos
$ErrorActionPreference = "Stop"
$gh = "C:\Program Files\GitHub CLI\gh.exe"
$tok = (& $gh auth token).Trim()
$H = @{ Authorization = "token $tok"; Accept = "application/vnd.github+json";
        "X-GitHub-Api-Version" = "2022-11-28"; "User-Agent" = "hemomemo-deploy" }
$API = "https://api.github.com"
$repos = @("noity0/hemomemo-ai", "noity0/noity0.github.io")

foreach ($r in $repos) {
  foreach ($f in @("index.html", "robots.txt")) {
    $local = "D:\DigitalBrain\web\$f"
    $sha = $null
    try {
      $ex = Invoke-RestMethod -Uri "$API/repos/$r/contents/$f" -Headers $H
      $sha = $ex.sha
    } catch {}
    $b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($local))
    $fb = @{ message = "sync: $f with meta verification & clean sitemap ref"; content = $b64 }
    if ($sha) { $fb.sha = $sha }
    Invoke-RestMethod -Method Put -Uri "$API/repos/$r/contents/$f" `
      -Headers $H -ContentType "application/json" -Body ($fb | ConvertTo-Json) | Out-Null
    "PUSHED: $r/$f"
  }
}
"GH-SYNC-DONE"
