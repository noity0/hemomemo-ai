$ErrorActionPreference = "Stop"
$rels = @(
    'agent\prompt_understanding_interface.py',
    'model\prompt_understanding.py',
    'tests\test_prompt_understanding.py'
)
$man = 'D:\HemomemoUltra-People\PROTECTED_MANIFEST.sha256'
$lines = Get-Content $man
foreach ($rel in $rels) {
    $src = Join-Path 'D:\DigitalBrain' $rel
    $dst = Join-Path 'D:\HemomemoUltra-People' $rel
    if (Test-Path $dst) { Set-ItemProperty $dst -Name IsReadOnly -Value $false -ErrorAction SilentlyContinue }
    Copy-Item $src $dst -Force
    $h = (Get-FileHash $dst -Algorithm SHA256).Hash.ToLower()
    $pat = '  ' + [regex]::Escape($rel) + '$'
    $lines = $lines | ForEach-Object { if ($_ -match $pat) { "$h  $rel" } else { $_ } }
    Write-Output "PATCHED $rel -> $h"
}
Set-Content -Path $man -Value $lines -NoNewline
Write-Output "MANIFEST-UPDATED"
