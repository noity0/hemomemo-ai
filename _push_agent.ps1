# _push_agent.ps1 — token-dimagh + agent-system + direct-link sab repo par
$ErrorActionPreference = "Stop"
$gh = "C:\Program Files\GitHub CLI\gh.exe"
$tok = (& $gh auth token).Trim()
$H = @{ Authorization = "token $tok"; Accept = "application/vnd.github+json";
        "X-GitHub-Api-Version" = "2022-11-28"; "User-Agent" = "hemomemo-deploy" }
$API = "https://api.github.com"
$repo = "noity0/hemomemo-ai"

$files = @(
  @{ local = "D:\DigitalBrain\model\tokenize.py";          remote = "model/tokenize.py" },
  @{ local = "D:\DigitalBrain\model\understand.py";        remote = "model/understand.py" },
  @{ local = "D:\DigitalBrain\model\memory.py";            remote = "model/memory.py" },
  @{ local = "D:\DigitalBrain\model\generate.py";         remote = "model/generate.py" },
  @{ local = "D:\DigitalBrain\model\cognition.py";        remote = "model/cognition.py" },
  @{ local = "D:\DigitalBrain\model\live_research.py";   remote = "model/live_research.py" },
  @{ local = "D:\DigitalBrain\model\live_plasticity.py";  remote = "model/live_plasticity.py" },
  @{ local = "D:\DigitalBrain\model\metacognition.py";    remote = "model/metacognition.py" },
  @{ local = "D:\DigitalBrain\model\autonomous.py";       remote = "model/autonomous.py" },
  @{ local = "D:\DigitalBrain\model\feelings.py";         remote = "model/feelings.py" },
  @{ local = "D:\DigitalBrain\model\deep_brain.py";       remote = "model/deep_brain.py" },
  @{ local = "D:\DigitalBrain\model\reasoning.py";        remote = "model/reasoning.py" },
  @{ local = "D:\DigitalBrain\model\learner.py";          remote = "model/learner.py" },
  @{ local = "D:\DigitalBrain\agent\orders.py";            remote = "agent/orders.py" },
  @{ local = "D:\DigitalBrain\agent\console_app.py";       remote = "agent/console_app.py" },
  @{ local = "D:\DigitalBrain\agent\pc_eye.py";            remote = "agent/pc_eye.py" },
  @{ local = "D:\DigitalBrain\agent\mc_bot.py";            remote = "agent/mc_bot.py" },
  @{ local = "D:\DigitalBrain\agent\modes.py";             remote = "agent/modes.py" },
  @{ local = "D:\DigitalBrain\agent\tasks.py";             remote = "agent/tasks.py" },
  @{ local = "D:\DigitalBrain\agent\browser_cloud.py";    remote = "agent/browser_cloud.py" },
  @{ local = "D:\DigitalBrain\agent\animation.py";        remote = "agent/animation.py" },
  @{ local = "D:\DigitalBrain\agent\video_gen.py";        remote = "agent/video_gen.py" },
  @{ local = "D:\DigitalBrain\core\hub.py";               remote = "core/hub.py" },
  @{ local = "D:\DigitalBrain\core\heart.py";            remote = "core/heart.py" },
  @{ local = "D:\DigitalBrain\core\owner.py";            remote = "core/owner.py" },
  @{ local = "D:\DigitalBrain\core\offline_oath.py";   remote = "core/offline_oath.py" },
  @{ local = "D:\DigitalBrain\core\state.py";            remote = "core/state.py" },
  @{ local = "D:\DigitalBrain\tests\test_tasks_system.py"; remote = "tests/test_tasks_system.py" },
  @{ local = "D:\DigitalBrain\data\corpus_big\gamebot_tasks.txt"; remote = "data/corpus_big/gamebot_tasks.txt" },
  @{ local = "D:\DigitalBrain\tests\test_token_brain.py";  remote = "tests/test_token_brain.py" },
  @{ local = "D:\DigitalBrain\tests\test_agent_powers.py"; remote = "tests/test_agent_powers.py" },
  @{ local = "D:\DigitalBrain\tests\test_code_gen.py";     remote = "tests/test_code_gen.py" },
  @{ local = "D:\DigitalBrain\tests\test_new_modules.py";  remote = "tests/test_new_modules.py" },
  @{ local = "D:\DigitalBrain\data\corpus_big\agent_orders.txt"; remote = "data/corpus_big/agent_orders.txt" },
  @{ local = "D:\DigitalBrain\Hemomemo-GameBot.spec";      remote = "Hemomemo-GameBot.spec" },
  @{ local = "D:\DigitalBrain\update_brain.ps1";           remote = "update_brain.ps1" },
  @{ local = "D:\DigitalBrain\_brain_publish.ps1";         remote = "scripts/brain_publish_owner.ps1" },
  @{ local = "D:\DigitalBrain\Hemomemo-Ultra-Brain.spec";  remote = "Hemomemo-Ultra-Brain.spec" },
  @{ local = "D:\DigitalBrain\scripts\make_package.py";    remote = "scripts/make_package.py" },
  @{ local = "D:\DigitalBrain\app\hemomemo_app.py";          remote = "app/hemomemo_app.py" },
  @{ local = "D:\DigitalBrain\server\hemomemo_server.py";    remote = "server/hemomemo_server.py" },
  @{ local = "D:\DigitalBrain\server\accounts.py";        remote = "server/accounts.py" },
  @{ local = "D:\DigitalBrain\security\guard.py";        remote = "security/guard.py" },
  @{ local = "D:\DigitalBrain\security\hmhz.py";         remote = "security/hmhz.py" },
  @{ local = "D:\DigitalBrain\tests\test_key_lifecycle.py"; remote = "tests/test_key_lifecycle.py" },
  @{ local = "D:\DigitalBrain\README.md";                  remote = "README.md" },
  @{ local = "D:\DigitalBrain\web\index.html";             remote = "index.html" },
  @{ local = "D:\DigitalBrain\web\index.html";             remote = "public/index.html" },
  @{ local = "D:\DigitalBrain\web\robots.txt";             remote = "robots.txt" },
  @{ local = "D:\DigitalBrain\web\robots.txt";             remote = "public/robots.txt" },
  @{ local = "D:\DigitalBrain\web\sitemap.xml";            remote = "sitemap.xml" },
  @{ local = "D:\DigitalBrain\web\sitemap.xml";            remote = "public/sitemap.xml" },
  @{ local = "D:\DigitalBrain\web\brain_manifest.json";    remote = "public/brain_manifest.json" },
  @{ local = "D:\DigitalBrain\web\og-image.png";           remote = "og-image.png" },
  @{ local = "D:\DigitalBrain\web\og-image.png";           remote = "public/og-image.png" },
  @{ local = "D:\DigitalBrain\web\404.html";               remote = "404.html" },
  @{ local = "D:\DigitalBrain\web\404.html";               remote = "public/404.html" },
  @{ local = "D:\DigitalBrain\web\site.webmanifest";       remote = "site.webmanifest" },
  @{ local = "D:\DigitalBrain\web\site.webmanifest";       remote = "public/site.webmanifest" },
  @{ local = "D:\DigitalBrain\web\icon-180.png";           remote = "icon-180.png" },
  @{ local = "D:\DigitalBrain\web\icon-180.png";           remote = "public/icon-180.png" },
  @{ local = "D:\DigitalBrain\web\icon-192.png";           remote = "icon-192.png" },
  @{ local = "D:\DigitalBrain\web\icon-192.png";           remote = "public/icon-192.png" },
  @{ local = "D:\DigitalBrain\web\icon-512.png";           remote = "icon-512.png" },
  @{ local = "D:\DigitalBrain\web\icon-512.png";           remote = "public/icon-512.png" },
  @{ local = "D:\DigitalBrain\data\corpus_big\trainer_knowledge_cmdshell.txt"; remote = "data/corpus_big/trainer_knowledge_cmdshell.txt" },
  @{ local = "D:\DigitalBrain\data\corpus_big\coding_ilm.txt"; remote = "data/corpus_big/coding_ilm.txt" },
  @{ local = "D:\DigitalBrain\data\corpus_big\sacred_facts.txt"; remote = "data/corpus_big/sacred_facts.txt" },
  @{ local = "D:\DigitalBrain\data\corpus_big\crawl_ilm.txt"; remote = "data/corpus_big/crawl_ilm.txt" },
  @{ local = "D:\DigitalBrain\data\corpus_big\search_gmail_ilm.txt"; remote = "data/corpus_big/search_gmail_ilm.txt" },
  @{ local = "D:\DigitalBrain\model\search_api.py";        remote = "model/search_api.py" },
  @{ local = "D:\DigitalBrain\model\gmail_link.py";        remote = "model/gmail_link.py" },
  @{ local = "D:\DigitalBrain\model\powers.py";            remote = "model/powers.py" },
  @{ local = "D:\DigitalBrain\model\code_exec.py";         remote = "model/code_exec.py" },
  @{ local = "D:\DigitalBrain\model\img_gen.py";           remote = "model/img_gen.py" },
  @{ local = "D:\DigitalBrain\model\deep_research.py";     remote = "model/deep_research.py" },
  @{ local = "D:\DigitalBrain\model\canvas_board.py";      remote = "model/canvas_board.py" },
  @{ local = "D:\DigitalBrain\model\gems.py";              remote = "model/gems.py" },
  @{ local = "D:\DigitalBrain\model\mcp_link.py";          remote = "model/mcp_link.py" },
  @{ local = "D:\DigitalBrain\model\gdrive_link.py";       remote = "model/gdrive_link.py" },
  @{ local = "D:\DigitalBrain\data\corpus_big\powers_ilm.txt"; remote = "data/corpus_big/powers_ilm.txt" },
  @{ local = "D:\DigitalBrain\harvest\net_guard.py";       remote = "harvest/net_guard.py" },
  @{ local = "D:\DigitalBrain\_apply_training_everywhere.py"; remote = "scripts/apply_training_everywhere.py" },
  @{ local = "D:\DigitalBrain\data\brain_map.json";        remote = "data/brain_map.json" },
  @{ local = "D:\DigitalBrain\_build_knowledge.py";        remote = "scripts/build_knowledge.py" },
  @{ local = "D:\DigitalBrain\scripts\make_desktop_package.py"; remote = "scripts/make_desktop_package.py" },
  @{ local = "D:\DigitalBrain\web\style.css";              remote = "style.css" },
  @{ local = "D:\DigitalBrain\web\style.css";              remote = "public/style.css" },
  @{ local = "D:\DigitalBrain\web\app.js";                 remote = "app.js" },
  @{ local = "D:\DigitalBrain\web\app.js";                 remote = "public/app.js" },
  @{ local = "D:\DigitalBrain\web\llms.txt";               remote = "llms.txt" },
  @{ local = "D:\DigitalBrain\web\llms.txt";               remote = "public/llms.txt" },
  @{ local = "D:\DigitalBrain\tests\test_api_endpoints.py"; remote = "tests/test_api_endpoints.py" }
)

$script:pushFails = 0
foreach ($f in $files) {
  $pushed = $false
  foreach ($att in 1..3) {
    $sha = $null
    try {
      $ex = Invoke-RestMethod -Uri "$API/repos/$repo/contents/$($f.remote)" -Headers $H
      $sha = $ex.sha
    } catch {}
    $b64 = [Convert]::ToBase64String([IO.File]::ReadAllBytes($f.local))
    $fb = @{ message = "agent: token-dimagh + Hemomemo-Agent (MC bot khud-join, chat-orders, duo, PC-aankh ESC-stop) - DIRECT system-link, no API-layer"; content = $b64 }
    if ($sha) { $fb.sha = $sha }
    try {
      Invoke-RestMethod -Method Put -Uri "$API/repos/$repo/contents/$($f.remote)" `
        -Headers $H -ContentType "application/json" -Body ($fb | ConvertTo-Json) | Out-Null
      "PUSHED: $($f.remote)"
      $pushed = $true
      break
    } catch {
      if ($att -lt 3) { Start-Sleep -Seconds (4 * $att) }
      else { "FAIL: $($f.remote) - " + $_.Exception.Message }
    }
  }
  if (-not $pushed) { $script:pushFails++ }
}

try {
  Invoke-RestMethod -Method Post -Uri "$API/repos/$repo/pages/builds" -Headers $H | Out-Null
  "PAGES-BUILD-TRIGGERED"
} catch { "TRIGGER-SKIP" }
"AGENT-PUSH-DONE (PUSH-FAILS: $script:pushFails)"
