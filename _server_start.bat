@echo off
rem Hemomemo server ON (aap-ke hukum se) - OFF-flag hatao, phir starter
powershell -NoProfile -Command "Remove-Item 'D:\DigitalBrain\data\_server_OFF.flag' -Force -ErrorAction SilentlyContinue"
call "D:\DigitalBrain\_server_24x7.bat"
exit /b 0
