# _gaming_off.ps1 - Hemomemo ke SARE bhaari processes band (gaming ke liye RAM/CPU free)
# app + gamebot + server-8790 + watcher + trainer + builders + publishers + netlify
$ErrorActionPreference = "SilentlyContinue"
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}

$os = Get-CimInstance Win32_OperatingSystem
'RAM pehle: FREE {0:N1} GB / {1:N1} GB' -f ($os.FreePhysicalMemory/1MB), ($os.TotalVisibleMemorySize/1MB)

taskkill /IM "Hemomemo-Ultra-Brain.exe" /F | Out-Null
taskkill /IM "Hemomemo-GameBot.exe" /F | Out-Null
taskkill /FI "IMAGENAME eq netlify.exe" /F | Out-Null

$pat = 'make_package|make_desktop_package|_apply_rest|_apply_training|_zip_web|_publish_final|_upload_zip|_push_agent|netlify|_server_watch|hemomemo_server|train_deep5h|pyinstaller|_build_ilm|_build_knowledge|Hemomemo-Ultra-Brain|Hemomemo-GameBot'
$killed = 0
Get-CimInstance Win32_Process -Filter "Name='python.exe' or Name='pythonw.exe' or Name='pyinstaller.exe' or Name='node.exe'" | ForEach-Object {
    if ($_.CommandLine -and $_.CommandLine -match $pat) {
        'KILL PID ' + $_.ProcessId + ' (' + $_.Name + ')'
        Stop-Process -Id $_.ProcessId -Force
        $killed++
    }
}
'builder-kill total: ' + $killed + ' process'

Get-NetTCPConnection -LocalPort 8790 -State Listen | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force
    'port-8790 PID ' + $_.OwningProcess + ' band'
}

Start-Sleep -Seconds 2
$os2 = Get-CimInstance Win32_OperatingSystem
'RAM baad:  FREE {0:N1} GB / {1:N1} GB' -f ($os2.FreePhysicalMemory/1MB), ($os2.TotalVisibleMemorySize/1MB)
'DONE: gaming ke liye system saaf'
