# _rebuild_exe.ps1 — Hemomemo-Ultra-Brain EXE rebuild (hub dist) + package-copy
Set-Location 'D:\DigitalBrain'
& "C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" -m PyInstaller --noconfirm "Hemomemo-Ultra-Brain.spec" 2>&1 | Select-Object -Last 3
if (Test-Path 'D:\DigitalBrain\dist\Hemomemo-Ultra-Brain.exe') {
  Copy-Item 'D:\DigitalBrain\dist\Hemomemo-Ultra-Brain.exe' 'D:\HemomemoUltra-People\Hemomemo-Ultra-Brain.exe' -Force
  $e = Get-Item 'D:\HemomemoUltra-People\Hemomemo-Ultra-Brain.exe'
  $mb = [int]($e.Length / 1MB)
  'EXE-COPY-OK: ' + $mb + ' MB | built ' + $e.LastWriteTime.ToString('HH:mm:ss')
} else {
  'DIST-EXE-GAIB - build-fail?'
}
