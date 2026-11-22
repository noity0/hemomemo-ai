$ErrorActionPreference = "Stop"
$lines = Get-Content "$PSScriptRoot\PROTECTED_MANIFEST.sha256"
foreach ($line in $lines) {
    Write-Output $line
}
