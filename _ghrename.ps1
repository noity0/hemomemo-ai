# GitHub repo rename: noity0/onegenultra -> noity0/hemomemo-ai
$ErrorActionPreference = "Stop"
$gh = "C:\Program Files\GitHub CLI\gh.exe"
$tok = (& $gh auth token).Trim()
$H = @{ Authorization = "token $tok"; Accept = "application/vnd.github+json";
        "X-GitHub-Api-Version" = "2022-11-28"; "User-Agent" = "hemomemo-deploy" }
$API = "https://api.github.com"
$me = Invoke-RestMethod -Uri "$API/user" -Headers $H
"user: $($me.login)"
$rs = Invoke-RestMethod -Uri "$API/users/$($me.login)/repos?per_page=100" -Headers $H
$old = $rs | Where-Object { $_.name -eq "onegenultra" }
if (-not $old) { "REPO-NOT-FOUND" } else {
  "OLD-FOUND: $($old.name) id=$($old.id) full=$($old.full_name)"
  $nr = Invoke-RestMethod -Method Patch -Uri "$API/repos/$($me.login)/onegenultra" -Headers $H -ContentType "application/json" -Body (@{ name = "hemomemo-ai" } | ConvertTo-Json)
  "RENAMED-OK -> $($nr.name) ($($nr.full_name))"
}
