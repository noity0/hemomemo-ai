@echo off
rem Hemomemo server OFF (SIRF aap-ke bat-se) - pehle OFF-flag (watcher izzat kare),
rem phir server ka shutdown-endpoint (grpc nahi - apna local HTTP)
powershell -NoProfile -Command "New-Item -Path 'D:\DigitalBrain\data\_server_OFF.flag' -ItemType File -Force | Out-Null; ('[' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + '] server-OFF (user hukum)') | Out-File -Append -Encoding utf8 'D:\DigitalBrain\data\_server_24x7.log'"
powershell -NoProfile -Command "try { & 'C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe' -Xutf8 'D:\DigitalBrain\server\hemomemo_server.py' stop 2>$null | Out-Null } catch { }; Get-NetTCPConnection -LocalPort 8790 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"
exit /b 0
