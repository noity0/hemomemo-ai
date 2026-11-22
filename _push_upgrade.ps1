# _push_upgrade.ps1 — README, LICENSE, naye modules, tests, build-script push
$ErrorActionPreference = "Stop"
$gh = "C:\Program Files\GitHub CLI\gh.exe"
$tok = (& $gh auth token).Trim()
$H = @{ Authorization = "token $tok"; Accept = "application/vnd.github+json";
        "X-GitHub-Api-Version" = "2022-11-28"; "User-Agent" = "hemomemo-deploy" }
$API = "https://api.github.com"
$repo = "noity0/hemomemo-ai"

$files = @(
  @{ local = "D:\DigitalBrain\README.md";              remote = "README.md" },
  @{ local = "D:\DigitalBrain\LICENSE";                remote = "LICENSE" },
  @{ local = "D:\DigitalBrain\model\memory.py";        remote = "model/memory.py" },
  @{ local = "D:\DigitalBrain\model\reasoning.py";     remote = "model/reasoning.py" },
  @{ local = "D:\DigitalBrain\agent\__init__.py";      remote = "agent/__init__.py" },
  @{ local = "D:\DigitalBrain\agent\mc_bot.py";        remote = "agent/mc_bot.py" },
  @{ local = "D:\DigitalBrain\agent\modes.py";         remote = "agent/modes.py" },
  @{ local = "D:\DigitalBrain\tests\test_new_modules.py"; remote = "tests/test_new_modules.py" },
  @{ local = "D:\DigitalBrain\BUILD-WINDOWS.bat";      remote = "BUILD-WINDOWS.bat" },
  @{ local = "D:\DigitalBrain\scripts\make_package.py"; remote = "scripts/make_package.py" }
)

foreach ($f in $files) {
  $sha = $null
  try {
    $ex = Invoke-RestMethod -Uri "$API/repos/$repo/contents/$($f.remote)" -Headers $H
    $sha = $ex.sha
  } catch {}
  $b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($f.local))
  $fb = @{ message = "upgrade: $($f.remote) (own-brain architecture, 3-modes, mc-bot, tests, MIT)"; content = $b64 }
  if ($sha) { $fb.sha = $sha }
  try {
    Invoke-RestMethod -Method Put -Uri "$API/repos/$repo/contents/$($f.remote)" `
      -Headers $H -ContentType "application/json" -Body ($fb | ConvertTo-Json) | Out-Null
    "PUSHED: $($f.remote)"
  } catch { "FAIL: $($f.remote) - " + $_.Exception.Message }
}

"=== repo metadata: description + homepage + topics ==="
$desc = "Hemomemo AI - 100% local offline AI with its OWN brain (pure-NumPy 2-layer LSTM, 7M params). NOT an LLM app, NO external model, NO AI-API, NO cloud. Three works: Text chat, Coding AI, and a Game-Agent Minecraft bot-player. Windows 7-11 Pro. By HMHS."
$body = @{ description = $desc; homepage = "https://hemomemo-ai.netlify.app/" } | ConvertTo-Json
try {
  Invoke-RestMethod -Method Patch -Uri "$API/repos/$repo" -Headers $H -ContentType "application/json" -Body $body | Out-Null
  "METADATA-OK (detailed about + homepage)"
} catch { "METADATA-FAIL: " + $_.Exception.Message }

$topics = @("hemomemo","offline-ai","local-ai","own-brain","numpy","lstm","not-an-llm",
            "minecraft-bot","game-agent","coding-ai","windows","python","no-api",
            "no-cloud","privacy","islamic-ai","hmhs","mit-license","offline-first","game-bot")
$tb = @{ names = $topics } | ConvertTo-Json
try {
  Invoke-RestMethod -Method Put -Uri "$API/repos/$repo/topics" `
    -Headers ($H + @{ Accept = "application/vnd.github.mercy-preview+json" }) `
    -ContentType "application/json" -Body $tb | Out-Null
  "TOPICS-OK ($($topics.Count) tags)"
} catch { "TOPICS-FAIL: " + $_.Exception.Message }

"=== Pages build trigger ==="
try {
  Invoke-RestMethod -Method Post -Uri "$API/repos/$repo/pages/builds" -Headers $H | Out-Null
  "BUILD-TRIGGERED"
} catch { "TRIGGER-SKIP" }
"PUSH-UPGRADE-DONE"
