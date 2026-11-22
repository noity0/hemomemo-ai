@echo off
title HemomemoBootStop (silent - boot par AI band)
REM ============================================================
REM  HEMOMEMO BOOT-STOP (silent, koi pause nahi)
REM  Laptop start/logon par KHUD chalta hai (task: HemomemoBootStop):
REM  - pause-flag (koi chain/resume boot par na chale)
REM  - tasks DISABLE (ApplyNow + AutoLink) + AutoStart=0
REM  - app-exe + trainer + chain + builders + publisher sab band
REM  - agnes-video / snake-monitor ko nahi chhorta (Hemomemo nahi)
REM  Wapas ON karne ke liye (MANUAL): Desktop\START-HEMOMEMO.bat
REM ============================================================
cd /d D:\DigitalBrain

echo [%date% %time%] BOOT-STOP chala >> "D:\DigitalBrain\data\_boot_stop.log"

echo paused > "D:\DigitalBrain\data\_PAUSED.flag" 2>nul
echo paused > "D:\DigitalBrain\_PAUSED.flag" 2>nul

schtasks /End /TN "HemomemoApplyNow" >nul 2>&1
schtasks /Change /TN "HemomemoApplyNow" /DISABLE >nul 2>&1
schtasks /End /TN "HemomemoAutoLink" >nul 2>&1
schtasks /Change /TN "HemomemoAutoLink" /DISABLE >nul 2>&1
reg add "HKCU\Software\HemomemoAI-24-7" /v AutoStart /t REG_SZ /d "0" /f >nul 2>&1

taskkill /IM "Hemomemo-Ultra-Brain.exe" /F >nul 2>&1
taskkill /IM "Hemomemo-GameBot.exe" /F >nul 2>&1

powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID -and ($_.CommandLine) -and ($_.CommandLine -notmatch 'STOP-HEMOMEMO|START-HEMOMEMO|_boot_stop') -and ($_.Name -match 'python|pyinstaller|powershell|cmd') -and ($_.CommandLine -match 'DigitalBrain|_apply_training|_train_deep5h|make_package|make_desktop|_publish_final|_push_agent|_upload_zip|_netlify_deploy|_build_knowledge|_APPLY-NOW|START-HEMOMEMO|hemomemo|Hemomemo-Ultra-Brain|Hemomemo-GameBot') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"

powershell -NoProfile -Command "Get-Process | Where-Object { $_.ProcessName -match 'pyinstaller' } | Stop-Process -Force -ErrorAction SilentlyContinue"

exit /b 0
