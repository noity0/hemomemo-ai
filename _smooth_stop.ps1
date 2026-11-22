# _smooth_stop.ps1 - chalte-hue heavy-kaam freeze (lag-ilaaj step-1)
$ErrorActionPreference = "SilentlyContinue"
$pat = '_apply_rest|make_desktop_package|_zip_web|_publish_final|_upload_zip|_push_agent|_netlify|_audit_run'
$killed = 0
Get-CimInstance Win32_Process -Filter "Name='python.exe' or Name='pythonw.exe' or Name='powershell.exe' or Name='pwsh.exe' or Name='node.exe' or Name='cmd.exe'" | ForEach-Object {
    if ($_.CommandLine -and $_.CommandLine -match $pat -and $_.ProcessId -ne $PID) {
        Stop-Process -Id $_.ProcessId -Force
        'KILL ' + $_.ProcessId + ' ' + $_.Name
        $killed++
    }
}
'frozen total: ' + $killed + ' process'
