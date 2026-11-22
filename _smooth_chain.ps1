# _smooth_chain.ps1 - publish-chain IDLE-priority par (PC smooth rehta hai).
# Idle = python/zip/netlify sirf tab CPU lete hain jab PC khali ho (drama/game
# chalte to ye khud peeche hat-jate hain). Window Hidden - kuch nazar nahi aata.
$ErrorActionPreference = "Continue"
$p = Start-Process -FilePath "powershell.exe" `
    -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File','D:\DigitalBrain\_apply_rest.ps1') `
    -WindowStyle Hidden -PassThru
try { $p.PriorityClass = 'Idle' } catch { try { $p.PriorityClass = 'BelowNormal' } catch {} }
'CHAIN PID ' + $p.Id + ' (IDLE priority - PC smooth mode)'
Wait-Process -Id $p.Id -ErrorAction SilentlyContinue
try { 'CHAIN-FINISHED rc=' + $p.ExitCode } catch { 'CHAIN-FINISHED' }
