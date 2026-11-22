@echo off
title HEMOMEMO - STOP ALL (RAM free)
REM ============================================================
REM  HEMOMEMO AI - SAB TASKS/PROCESSES BAND + RAM FREE
REM  Ye "PAUSE" lagata hai: boot/logon par resume-chain bhi NAHI
REM  chalegi jab tak START-HEMOMEMO.bat na chalaya jaye.
REM ============================================================
cd /d D:\DigitalBrain

echo [1/5] PAUSE-FLAG lagaya (boot-resume bhi rukega)...
echo paused > data\_PAUSED.flag

echo [2/5] Scheduled tasks band...
schtasks /End /TN "HemomemoApplyNow" >nul 2>&1
schtasks /Change /TN "HemomemoApplyNow" /DISABLE >nul 2>&1

echo [3/5] App-EXEs band (agar khul hon)...
taskkill /IM "Hemomemo-Ultra-Brain.exe" /F >nul 2>&1
taskkill /IM "Hemomemo-GameBot.exe" /F >nul 2>&1

echo [4/5] Hemomemo ke python/pyinstaller/publish processes band...
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { $_.ProcessId -ne $PID -and ($_.CommandLine) -and ($_.CommandLine -notmatch 'STOP-HEMOMEMO|START-HEMOMEMO') -and ($_.Name -match 'python|pyinstaller|powershell|cmd') -and ($_.CommandLine -match 'DigitalBrain|_apply_training|_train_deep5h|make_package|make_desktop|_publish_final|_APPLY-NOW|hemomemo|hemomemo|Hemomemo-Ultra-Brain|Hemomemo-GameBot') } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue; 'killed PID ' + $_.ProcessId }"

echo [5/5] Ram-clear (kaam-ki processes ka kachra safai)...
powershell -NoProfile -Command "Get-Process | Where-Object { $_.ProcessName -match 'pyinstaller' } | Stop-Process -Force -ErrorAction SilentlyContinue"
powershell -NoProfile -Command "$os = Get-CimInstance Win32_OperatingSystem; 'FREE RAM ab: ' + [math]::Round($os.FreePhysicalMemory/1MB,1) + ' GB'"

echo.
echo Hemomemo ka sab kuch BAND - RAM free ho gaya.
echo Wapas chalane ke liye: D:\DigitalBrain\START-HEMOMEMO.bat
pause
