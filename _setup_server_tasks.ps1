# _setup_server_tasks.ps1 - Hemomemo local-server 24/7 (sirf bat-se off)
$ErrorActionPreference = 'Continue'
$bat = 'D:\DigitalBrain\_server_24x7.bat'
$act = New-ScheduledTaskAction -Execute $bat
$set = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit ([TimeSpan]::FromMinutes(5))

# 1) logon par foran-start
$t1 = New-ScheduledTaskTrigger -AtLogOn
Register-ScheduledTask -TaskName 'HemomemoServer24x7' -Action $act -Trigger $t1 -Settings $set -Force | Out-Null
Write-Output 'task HemomemoServer24x7 (onlogon) OK'

# 2) har-5-min watch (crash auto-restart, idempotent)
$iv = New-TimeSpan -Minutes 5
$du = New-TimeSpan -Days 3650
$t2 = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval $iv -RepetitionDuration $du
Register-ScheduledTask -TaskName 'HemomemoServerWatch' -Action $act -Trigger $t2 -Settings $set -Force | Out-Null
Write-Output 'task HemomemoServerWatch (5-min) OK'

# 3) ApplyNow wapas enable (koi auto-trigger nahi - manual-only)
Enable-ScheduledTask -TaskName 'HemomemoApplyNow' -ErrorAction SilentlyContinue | Out-Null
Write-Output 'ApplyNow enabled'

# 4) registry AutoStart = 1
New-Item -Path 'HKCU:\Software\HemomemoAI-24-7' -Force | Out-Null
Set-ItemProperty -Path 'HKCU:\Software\HemomemoAI-24-7' -Name AutoStart -Value '1'
Write-Output 'AutoStart=1'
