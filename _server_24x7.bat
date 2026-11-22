@echo off
rem ============================================================
rem  HEMOMEMO LOCAL-SERVER 24/7 STARTER (idempotent, windowless)
rem  - port 8790 pehle-se chal raha ho to KUCH nahi karta
rem  - _server_OFF.flag maujood ho to START NAHI karta
rem    (user ne "band karo" kaha hota hai - izzat karo)
rem  - warna source-se server start (EXE-lock se azad, chain-safe)
rem ============================================================
powershell -NoProfile -Command "if (Test-Path 'D:\DigitalBrain\data\_server_OFF.flag') { exit 0 }; if (Get-NetTCPConnection -LocalPort 8790 -State Listen -ErrorAction SilentlyContinue) { exit 0 }; Start-Process 'C:\Users\user\AppData\Local\Programs\Python\Python312\pythonw.exe' -ArgumentList '-Xutf8','D:\DigitalBrain\server\hemomemo_server.py' -WorkingDirectory 'D:\DigitalBrain' -WindowStyle Hidden; ('[' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '] server-start (24x7)') | Out-File -Append -Encoding utf8 'D:\DigitalBrain\data\_server_24x7.log'"
exit /b 0
