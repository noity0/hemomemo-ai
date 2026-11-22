# _watch_apply.ps1 — chain-khatam hone ka watcher (background)
$deadline = (Get-Date).AddMinutes(120)
while ((Get-Date) -lt $deadline) {
  $p = Get-CimInstance Win32_Process | Where-Object {
    ($_.Name -like 'python*' -or $_.Name -match 'pwsh|powershell') -and
    $_.ProcessId -ne $PID -and $_.CommandLine -and
    ($_.CommandLine -match 'apply_training|make_package|make_desktop|publish_final|upload_zip|push_agent|netlify_deploy|_APPLY-NOW')
  }
  if (-not $p) { break }
  Start-Sleep -Seconds 45
}
'=== CHAIN-KHATAM at ' + (Get-Date -Format 'HH:mm:ss') + ' ==='
Get-Content 'D:\DigitalBrain\data\_apply_training.log' -Tail 22 -ErrorAction SilentlyContinue
