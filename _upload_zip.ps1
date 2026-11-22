$ErrorActionPreference = "Continue"
Set-Location "D:\DigitalBrain"
for ($i = 1; $i -le 10; $i++) {
    Write-Output "ATTEMPT $i ZIP"
    gh release upload v4.2.1-people "HemomemoUltra-People.zip" --clobber
    if ($LASTEXITCODE -eq 0) { Write-Output "ZIP-UPLOAD-OK"; exit 0 }
    Start-Sleep -Seconds 20
}
Write-Output "ZIP-UPLOAD-FAILED"
exit 1
