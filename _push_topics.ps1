# _push_topics.ps1 — sirf topics (tags)
$ErrorActionPreference = "Stop"
$gh = "C:\Program Files\GitHub CLI\gh.exe"
$tok = (& $gh auth token).Trim()
$H2 = @{ Authorization = "token $tok"; "User-Agent" = "hemomemo-deploy";
         Accept = "application/vnd.github.mercy-preview+json" }
$API = "https://api.github.com"
$repo = "noity0/hemomemo-ai"

$topics = @("hemomemo","offline-ai","local-ai","own-brain","numpy","lstm","not-an-llm",
            "minecraft-bot","game-agent","coding-ai","windows","python","no-api",
            "no-cloud","privacy","islamic-ai","hmhs","mit-license","offline-first","game-bot")
$tb = @{ names = $topics } | ConvertTo-Json
try {
  Invoke-RestMethod -Method Put -Uri "$API/repos/$repo/topics" `
    -Headers $H2 -ContentType "application/json" -Body $tb | Out-Null
  "TOPICS-OK ($($topics.Count) tags)"
} catch { "TOPICS-FAIL: " + $_.Exception.Message }
"TOPICS-DONE"
