$ErrorActionPreference = "Continue"
Set-Location "D:\DigitalBrain"
for ($i = 1; $i -le 10; $i++) {
    Write-Output "ATTEMPT $i VIDEO"
    gh release upload v4.2.1-people "data\videos\ultra_photoreal\ultra_photoreal_ultra_photoreal_mountain_bike_downhill_20261119_201253.mp4#ultra_photoreal_mountain_bike_downhill_4k.mp4" --clobber
    if ($LASTEXITCODE -eq 0) { Write-Output "VIDEO-UPLOAD-OK"; exit 0 }
    Start-Sleep -Seconds 20
}
Write-Output "VIDEO-UPLOAD-FAILED"
exit 1
