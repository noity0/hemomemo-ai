# _audit_detail.ps1 - audit-detail IDLE-priority par (PC smooth, window hidden)
$ErrorActionPreference = "Continue"
$py = "C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe"
$out = "D:\DigitalBrain\data\_audit_detail.out"
$err = "D:\DigitalBrain\data\_audit_detail.err"
$p = Start-Process -FilePath $py `
    -ArgumentList @('-Xutf8','D:\DigitalBrain\_audit_detail.py') `
    -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput $out -RedirectStandardError $err
try { $p.PriorityClass = 'Idle' } catch { try { $p.PriorityClass = 'BelowNormal' } catch {} }
'DETAIL PID ' + $p.Id + ' (IDLE priority)'
Wait-Process -Id $p.Id -ErrorAction SilentlyContinue
'DETAIL-FINISHED rc=' + $p.ExitCode
