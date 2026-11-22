# _restart_games.ps1 — purana collector band, file saaf, compile-check
$patG = '_games' + 'data.py'
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
  Where-Object { $_.ProcessId -ne $PID -and $_.CommandLine -and $_.CommandLine.Contains($patG) } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; "COLLECTOR-KILLED pid=$($_.ProcessId)" }
Start-Sleep -Seconds 2
Remove-Item "D:\DigitalBrain\data\corpus_big\games_knowledge.txt" -Force -ErrorAction SilentlyContinue
Remove-Item "D:\DigitalBrain\harvest\seen_games.json" -Force -ErrorAction SilentlyContinue
py -3 -m py_compile _gamesdata.py 2>&1
"COMPILE-OK - file saaf, naya collector tayar"
