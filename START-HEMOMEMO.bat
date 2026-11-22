@echo off
title HEMOMEMO - START / RESUME (sirf zaroori)
REM ============================================================
REM  HEMOMEMO AI - SIRF ZAROORI CHEEZEIN WAPAS ON
REM  (apply-chain + 24/7 connection-hub + app GUI)
REM  Band karne ke liye: STOP-HEMOMEMO.bat
REM ============================================================
cd /d D:\DigitalBrain

echo [1/4] PAUSE hata rahe hain...
del /f /q "D:\DigitalBrain\data\_PAUSED.flag" >nul 2>&1
schtasks /Change /TN "HemomemoApplyNow" /ENABLE >nul 2>&1

echo [2/4] Apply-chain resume (EXE/packages/zips/publish (50M final))...
start "Hemomemo-Apply-Chain" cmd /c "D:\DigitalBrain\_APPLY-NOW.bat"

echo [3/4] 24/7 Connection-hub ON (DigitalBrain live-link)...
start "Hemomemo-24-7-Hub" /min cmd /c "D:\DigitalBrain\24-7-CONNECT.bat"

echo [4/4] App GUI ON...
start "Hemomemo-App" /min cmd /c "D:\DigitalBrain\Hemomemo-AI.bat"

echo.
echo Hemomemo AI wapas ON: chain + hub + app chal pade.
echo Band karne ke liye: D:\DigitalBrain\STOP-HEMOMEMO.bat
pause
