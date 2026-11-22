$ErrorActionPreference = "Stop"
$lines = Get-Content "D:\HemomemoUltra-People\PROTECTED_MANIFEST.sha256"
$ok = $true
foreach ($line in $lines) {
    if ($line -match '^([0-9a-f]{64})  (.+)$') {
        $p = Join-Path "D:\HemomemoUltra-People" $Matches[2]
        if (-not (Test-Path $p)) {
            Write-Output ("GAYIB  " + $Matches[2])
            $ok = $false
            continue
        }
        $h = (Get-FileHash $p -Algorithm SHA256).Hash.ToLower()
        if ($h -eq $Matches[1]) {
            Write-Output ("SAABIT " + $Matches[2])
        } else {
            Write-Output ("TABDEELI " + $Matches[2] + "  expected=" + $Matches[1] + "  actual=" + $h)
            $ok = $false
        }
    }
}
if ($ok) {
    Write-Output "ALL OK - 0 GAYIB, 0 TABDEELI"
} else {
    Write-Output "PROBLEMS FOUND ABOVE"
}
