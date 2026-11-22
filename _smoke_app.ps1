# _smoke_app.ps1 — 7-sec smoke-run: app bina-crash khulti hai?
$py = "C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe"
$p = Start-Process -FilePath $py -ArgumentList 'D:\DigitalBrain\app\hemomemo_app.py' `
     -WorkingDirectory 'D:\DigitalBrain' -PassThru -WindowStyle Hidden `
     -RedirectStandardError 'D:\DigitalBrain\data\_smoke_err.txt' `
     -RedirectStandardOutput 'D:\DigitalBrain\data\_smoke_out.txt'
Start-Sleep -Seconds 7
if ($p.HasExited) {
  'SMOKE-FAIL: rc=' + $p.ExitCode
  Get-Content 'D:\DigitalBrain\data\_smoke_err.txt' -Tail 15 -ErrorAction SilentlyContinue
} else {
  'SMOKE-OK: app zinda hai (PID ' + $p.Id + ') — ab band kar rahe'
  Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
  Start-Sleep -Seconds 2
  $err = Get-Content 'D:\DigitalBrain\data\_smoke_err.txt' -Tail 15 -ErrorAction SilentlyContinue
  if ($err) { '--- stderr (tail) ---'; $err } else { 'stderr saaf' }
}
