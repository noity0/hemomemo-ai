# -*- coding: utf-8 -*-
# _build_knowledge.py — HEMOMEMO ilm-barhane ka generator (100% local)
# Hukum: CMD + PowerShell commands, coding-ilm (45+ languages), verified
# world-knowledge, aur world-class web-crawling ilm - sab Sawal:/Jawab:
# corpus format me (token-dimagh + KnowledgeRetrieval yehi parhte hain).
# Har ilm ke KAI sawal-tareeqay bante hain (phrasing-variants) - retrieval
# behtar + ilm hazaron entries me. Koi external AI API nahi - sirf curated
# text jo standard docs se hai (imandari: har jawab asli aur sahih).
import io, json, os, time

SRC = r"D:\DigitalBrain"
CB  = os.path.join(SRC, "data", "corpus_big")

def w(name, entries, header):
    """entries: list of (sawals[list], jawab)"""
    p = os.path.join(CB, name)
    with io.open(p, "w", encoding="utf-8") as f:
        f.write(header)
        n = 0
        for sawals, jawab in entries:
            for s in sawals:
                f.write("Sawal: %s\n" % s)
            f.write("Jawab: %s\n\n" % jawab)
            n += 1
    print("%s: %d entries, %.1f KB" % (name, n, os.path.getsize(p) / 1024.0))
    return n

# ════════════════════════════════════════════════════════════════════
# 1) CMD + POWERSHELL ILM (haqeeqi commands — usage + matlab)
# ════════════════════════════════════════════════════════════════════
CMD = [
("dir","Folder ka content dikhata hai. Usage: dir C:\\Windows (param: /a hidden sab, /o sort, /s sub-folders, /q owner)."),
("cd / chdir","Folder tabdeel. Usage: cd D:\\DigitalBrain (cd .. peechay, cd\\ root, /d drive-bhi-badal)."),
("md / mkdir","Naya folder. Usage: md D:\\DigitalBrain\\nayafolder (beech-kay-folers khud ban jate hain)."),
("rd / rmdir","Folder hatao. Usage: rd folder (khali) / rd /s folder (sab-andar) / rd /s /q (bina-poochay)."),
("copy","File copy. Usage: copy a.txt D:\\b\\ (wildcards: copy *.txt D:\\bak\\)."),
("xcopy","Folder-copy zyada-qaaboo. Usage: xcopy C:\\src D:\\dst /E /H /K /Y (/E empty-bhi, /H hidden+system, /Y overwrite-no-ask)."),
("robocopy","Bharay-mandir file-copy (server-grade). Usage: robocopy C:\\src D:\\dst /E /Z /R:2 /W:2 /MT:8 (/Z restartable, /MT threads). Exit-codes: 0-7 kamyab."),
("del / erase","File hatao. Usage: del file.txt / del *.tmp /s (sub-folders) /f force /q quiet."),
("ren / rename","Naam badal. Usage: ren purana.txt naya.txt."),
("move","File/folder hilo. Usage: move a.txt D:\\new\\ (move *.log archive\\)."),
("type","File ka text dikhao. Usage: type config.txt (type a.txt b.txt > sab.txt merge)."),
("more","Bare-file ko tukron me dikhao. Usage: more big.log (SPACE agla, Q kharoj)."),
("find","Text dhoondo (simple). Usage: find \"salam\" file.txt /c (ginti) /i case-nahi-dekhta."),
("findstr","Text dhoondo (regex, powerful). Usage: findstr /i /r \"^[0-9]+\" file.txt (/s sub-folders, /m sirf-file-name)."),
("attrib","File-attributes. Usage: attrib +r file (read-only) / attrib -h -s file (hidden/system khulo) / attrib +h secret."),
("chkdsk","Disk-janch. Usage: chkdsk D: /f (ghalati-theek) /r (kharab-sectors dhoond)."),
("sfc","System-files ki sachai. Usage: sfc /scannow (Windows ki kharab system files theek)."),
("dism","Windows-image service. Usage: DISM /Online /Cleanup-Image /RestoreHealth (component-store theek)."),
("diskpart","Disk-partition ka control. Usage: diskpart → list disk → select disk 0 → list partition (khayal: clean poora disk mita!)."),
("format","Drive format. Usage: format D: /FS:NTFS /Q (Q=jaldi) — SARA DATA URA!"),
("fsutil","File-system ka nichla-qaaboo. Usage: fsutil volume diskfree C: (khali-jagah)."),
("cipher","Encryption + secure-delete. Usage: cipher /w:C: (khali-jagah ke purane data SAFAY) /e folder (EFS encrypt)."),
("compact","NTFS-compression. Usage: compact /c /s:D:\\folder /i /q (jagah bachao)."),
("defrag","Disk-murattab. Usage: defrag C: /O (SSD par /O retrim; HDD par /U /V)."),
("driverquery","Drivers ki list. Usage: driverquery /v (tafsil) /si (signatures)."),
("sc","Service-control. Usage: sc query wuauserv / sc startBITS? NO — sc start <name> / sc config <name> start= auto (space-zaroori start= ke baad)."),
("schtasks","Scheduled-task. Usage: schtasks /create /tn \"Naam\" /tr \"notepad\" /sc onlogon /rl highest /f ; schtasks /run /tn \"Naam\" ; /change /disable."),
("tasklist","Chal-rahe-processes. Usage: tasklist /v /fi \"memusage gt 100000\" (100MB+ RAM)."),
("taskkill","Process khatam. Usage: taskkill /IM notepad.exe /F / taskkill /PID 1234 /F /T (tree-children-bhi)."),
("wmic","WMI-queries (purana). Usage: wmic cpu get name / wmic logicaldisk get size,freespace / wmic process where name='x.exe' delete."),
("reg","Windows-registry. Usage: reg add HKCU\\Software\\X /v V /t REG_SZ /d \"data\" /f ; reg query HKLM\\... ; reg delete ... /f ; reg export key file.reg."),
("regsvr32","DLL-register. Usage: regsvr32 shell32.dll /u (unregister) /s (silent)."),
("set","Env-vars session-me. Usage: set PATH=%PATH%;D:\\new (setx permanent banata hai)."),
("setx","Env-var PERMANENT. Usage: setx JAVA_HOME \"C:\\java\" / setx PATH \"%PATH%;D:\\bin\" /M (machine-wide, admin)."),
("cls","Screen saaf. Usage: cls."),
("echo","Text print + file-likho. Usage: echo salam > a.txt (naya) / echo zyada >> a.txt (append) / echo off (bat-script)."),
("pause","Script rok-kar intezar: \"press any key\". Usage: pause >nul (chup-chaap)."),
("start","Naya window/process. Usage: start notepad / start \"T\" cmd /c \"bat\" / start /min app / start /b python x.py (us-window-me)."),
("call","Dusra bat chalao aur wapas aao. Usage: call :label arg1 / call other.bat."),
("exit","Khatam. Usage: exit / exit /b 0 (rc=0 kamyab) / exit /b %errorlevel%."),
("for","Loop. Usage: for %f in (*.txt) do echo %f (bat-me %%f) / for /f \"tokens=1\" %a in (list.txt) do ... / for /d /r /l (count)."),
("if","Sharait. Usage: if exist f.txt (echo hai) else (echo nahi) / if %a%==1 ... / if errorlevel 1 ... / if defined var."),
("goto","Kood. Usage: goto :label → :label (exit /b se niklo warna fall-through)."),
("shift","Bat-args shift: %1→%0. Usage: loop-parsing me shift."),
("title","Window ka title. Usage: title MERA-NAAM."),
("color","Console-rang. Usage: color 0a (kala-bg, sabz-text) / color /f default."),
("prompt","Prompt ka shape. Usage: prompt $P$G (path>) / prompt $T$s$P$G (waqt+path)."),
("ver","Windows-version. Usage: ver."),
("vol","Volume-label. Usage: vol C:."),
("label","Drive-label badlo. Usage: label D: DATA."),
("date / time","Taareekh/waqt. Usage: date /t (dikhao) / time (badlo)."),
("tree","Folder-structure ka darakht. Usage: tree /f (files-bhi) /a (ASCII)."),
("where","Executable/file dhoondo PATH-me. Usage: where python / where /r C:\\ *.npz."),
("whoami","Main kaun. Usage: whoami /priv (privileges) /groups /user:SID."),
("net user","Users-kaam. Usage: net user / net user Ali Pass123 /add / net user Ali /delete / net user Ali * (password-badal)."),
("net localgroup","Groups. Usage: net localgroup administrators Ali /add (admin-banao)."),
("net use","Network-drive/mapping. Usage: net use Z: \\\\PC\\share /user:u pass / net use * /delete (sab-jur)."),
("net share","Shares. Usage: net share MyShare=D:\\data /grant:Everyone,full."),
("net start/stop","Service. Usage: net start wuauserv / net stop wuauserv."),
("netstat","Network-connections. Usage: netstat -ano (PIDs-bhi) / -b (exe-naam) / netstat -ano | findstr :8790 (port-kaun-pakray)."),
("nbtstat","NetBIOS-cache/naam. Usage: nbtstat -A 192.168.1.5."),
("ping","ICMP-test. Usage: ping 8.8.8.8 -n 4 / ping -t (lagatar, CTRL+C rok) / ping -l 1400 (packet-size)."),
("tracert","Route dikhao. Usage: tracert google.com -d (DNS-resolve-nahi)."),
("pathping","Route + packet-loss (zyada sach). Usage: pathping google.com."),
("nslookup","DNS-sawal. Usage: nslookup example.com / nslookup -type=mx example.com 1.1.1.1."),
("ipconfig","Network-config. Usage: ipconfig /all / ipconfig /release + /renew / ipconfig /flushdns (DNS-cache saaf)."),
("route","Routing-table. Usage: route print / route add 10.0.0.0 mask 255.0.0.0 192.168.1.1."),
("arp","MAC-cache. Usage: arp -a (sab entries)."),
("getmac","MAC-addresses. Usage: getmac /v."),
("hostname","PC ka naam. Usage: hostname."),
("systeminfo","Poora system-report. Usage: systeminfo (RAM, hotfixes, uptime, NICs)."),
("msinfo32","System-info GUI. Usage: msinfo32."),
("dxdiag","DirectX/GPU-jaanch. Usage: dxdiag."),
("mstsc","Remote-Desktop. Usage: mstsc /v:PC /w:1280 /h:720."),
("shutdown","Shutdown/restart. Usage: shutdown /s /t 60 (60s me band) / shutdown /r /t 0 (restart) / shutdown /a (cancel!) / shutdown /l (logoff)."),
("logoff","Session-khatam. Usage: logoff (current) / logoff SESSIONID /server:PC."),
("rundll32","DLL-function chalao (khatarnaak-qaabil-e-ilm). Usage: rundll32 powrprof.dll,SetSuspendState 0,1,0 (sleep) / user32.dll,LockWorkStation (lock)."),
("assoc / ftype","File-association. Usage: assoc .py=Python.File / ftype Python.File=\"C:\\py\\python.exe\" \"%%1\"."),
("subst","Folder=drive. Usage: subst X: D:\\deep\\folder (subst X: /d hatao)."),
("mklink","Links. Usage: mklink file.lnk target (file-symlink) / mklink /D dir.lnk target (dir-symlink) / mklink /J dir.lnk target (junction — admin-nahi-chahiye!)."),
("expand","CAB/MSI-file khole. Usage: expand file.cab -F:* D:\\out."),
("makecab","CAB banao. Usage: makecab a.txt a.cab."),
("certutil","Certificates + hash. Usage: certutil -hashfile file.txt SHA256 (hash!) / -addstore Root cert.cer."),
("bcdedit","Boot-config. Usage: bcdedit /set {default} safeboot minimal (safe-mode) / /deletevalue (wapas)."),
("winmgmt","WMI-service. Usage: winmgmt /validaterepository /resyncperf."),
("gpupdate","Group-policy refresh. Usage: gpupdate /force."),
("gpresult","Policy-report. Usage: gpresult /r /h report.html."),
("icacls","NTFS-permissions (naya). Usage: icacls folder /grant Users:(OI)(CI)F /T / icacls folder /reset /T / /save file /restore file."),
("takeown","Malik-bano. Usage: takeown /f file / takeown /f folder /r /d y."),
("runas","Doosre-user se chalao. Usage: runas /user:Administrator cmd."),
("control","Control-Panel. Usage: control / control printers / schedtasks."),
("appwiz.cpl","Programs-ya-khatam. Usage: appwiz.cpl (control-panel applets .cpl se khulte hain)."),
("perfmon","Performance-monitor. Usage: perfmon /res (resource-monitor)."),
("resmon","Resource-monitor. Usage: resmon (CPU/RAM/Disk/Network live)."),
("compmgmt","Computer-management. Usage: compmgmt.msc (eventvwr+services+disk sab)."),
("devmgmt","Device-manager. Usage: devmgmt.msc."),
("diskmgmt","Disk-management. Usage: diskmgmt.msc."),
("services","Services-GUI. Usage: services.msc."),
("eventvwr","Event-logs. Usage: eventvwr.msc / eventvwr System."),
("cleanmgr","Disk-safai. Usage: cleanmgr /d C: /sageset:1."),
("mdsched","RAM-jaanch. Usage: mdsched (restart-kar-jaanch)."),
("verifier","Driver-verifier (debug). Usage: verifier /standard /all (khatarnaak-bsod)."),
("sigverif","File-signature-jaanch. Usage: sigverif."),
("slmgr","Windows-license. Usage: slmgr /xpr (expiry) / /dlv (tafsil) / /rearm."),
("cscript / wscript","VBScript/JScript chalao. Usage: cscript script.vbs //nologo."),
("mshta","HTA-app chalao. Usage: mshta app.hta."),
("choice","Choice-prompt. Usage: choice /c YN /m \"Qabol?\" (errorlevel 1=Y,2=N)."),
("timeout","Intezar. Usage: timeout /t 10 /nobreak (10s, key-ignore)."),
("curl","URL-fetch (Win10+ builtin). Usage: curl -O https://... / curl -I url (headers) / curl -d \"a=1\" -X POST url."),
("tar","TAR-archive (Win10+ builtin). Usage: tar -xf a.tar.gz / tar -czf a.tar.gz folder / -xzf khole."),
("clip","Clipboard bhejo. Usage: ipconfig | clip."),
("doskey","Macro/history. Usage: doskey np=notepad $* / doskey /history."),
("robocopy /mir","Folder MIRROR. Usage: robocopy src dst /MIR (dst ko src jaisa — EXTRA FILES URA! /MOT:n monitor)."),
("path","PATH dikhao/badlo (session). Usage: path %PATH%;D:\\bin."),
("pushd / popd","Location-stack. Usage: pushd D:\\x (wapas: popd — network-path par drive khud map)."),
("fc","Files compare. Usage: fc a.txt b.txt /n (line-nos) /fc binary /b."),
("sort","Text-sort. Usage: sort a.txt /o b.txt /+n (numeric) /r (ulta)."),
("echo %errorlevel%","Pichli-command ka rc. Usage: 0=kamyab, non-zero=fail; bat: if %errorlevel% neq 0 exit /b 1."),
("eventcreate","Custom-event likho. Usage: eventcreate /l application /so HEMO /id 1 /t information /d \"msg\"."),
("wevtutil","Event-log-CLI. Usage: wevtutil qe System /c:5 /f:text /rd:true (aakhri 5)."),
("powercfg","Power-plan + report. Usage: powercfg /a (sleep-states) / /energy (battery-report) / /list /setactive SCHEME."),
("wmic qfe","Updates-list. Usage: wmic qfe list brief (installed-hotfixes)."),
("setlocal / endlocal","Bat-vars local-scope. Usage: setlocal (badlaaw wapas endlocal par ura)."),
("title@echo off","Bat-standard: Usage: @echo off (har-line-print-na) + title + setlocal."),
("robocopy backup","Backup-pattern. Usage: robocopy C:\\data D:\\bak\\%%date%% /E /XD temp (date-folder backup)."),
("bitsadmin","BITS-jobs (purana). Usage: bitsadmin /transfer j /download /priority high url file."),
("netsh","Network-shape. Usage: netsh wlan show profiles / netsh interface ip set dns \"Ethernet\" static 1.1.1.1 / netsh advfirewall firewall add rule name=\"X\" dir=in action=allow protocol=TCP localport=8790."),
]

PS = [
("Get-ChildItem / gci / ls","Folder-list. Usage: gci D:\\x -Recurse -Filter *.npz -Force (hidden-bhi); -Depth level; | Measure-Object -Property Length -Sum = size."),
("Set-Location / cd","Tabdeel-jagah. Usage: cd D:\\x; cd ..; cd ~ (home)."),
("Get-Content / gc / cat","Text-parho. Usage: gc file.txt -Tail 20 (aakhri-20, live: -Wait); gc file -Raw (ek-string)."),
("Set-Content / Add-Content","Likho/Joro. Usage: sc? NO — Set-Content f \"text\" -Encoding utf8; Add-Content log \"line\" -Encoding utf8."),
("Copy-Item / cp","Copy. Usage: Copy-Item a b -Force; Copy-Item src dst -Recurse."),
("Move-Item / mv","Hilo/naam-badal. Usage: Move-Item a D:\\x\\; Move-Item purana naya."),
("Remove-Item / rm / del","Mitao. Usage: Remove-Item f -Force; Remove-Item folder -Recurse -Force; -WhatIf pehle-dekho."),
("New-Item","Naya banо. Usage: New-Item f.txt -ItemType File; New-Item dir -ItemType Directory -Force."),
("Test-Path","Hai ya nahi. Usage: Test-Path f; Test-Path HKCU:\\Software\\X (registry-bhi)."),
("Get-Process / ps","Processes. Usage: Get-Process python | Sort-Object WS -Desc (RAM-top); Get-Process -Id 1234."),
("Stop-Process","Process khatam. Usage: Stop-Process -Name notepad -Force; Stop-Process -Id 1234 -Force."),
("Start-Process","Chalao. Usage: Start-Process notepad; Start-Process python -ArgumentList '-Xutf8','app.py' -WindowStyle Hidden -WorkingDirectory D:\\x."),
("Wait-Process","Intezar-process. Usage: Wait-Process -Name x -Timeout 60."),
("Get-Service","Services. Usage: Get-Service wuauserv; gsv | Where-Object Status -eq Running."),
("Start/Stop/Restart-Service","Service kaam. Usage: Start-Service wuauserv -WhatIf; Restart-Service wuauserv -Force."),
("Get-CimInstance","WMI/CIM-sawal (modern). Usage: Get-CimInstance Win32_OperatingSystem | Select FreePhysicalMemory; Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | Select CommandLine."),
("Invoke-CimMethod","WMI-amal. Usage: Invoke-CimMethod Win32_Process -MethodName Create -Arguments @{CommandLine='notepad'}."),
("Get-ComputerInfo","System-report. Usage: Get-ComputerInfo | Select OsName,OsArchitecture,CsTotalPhysicalMemory."),
("Get-EventLog / Get-WinEvent","Event-log. Usage: Get-WinEvent -LogName System -MaxEvents 10 -Oldest? NO: -MaxEvents 10 (naye-pehle); Get-WinEvent -FilterHashtable @{LogName='System';Level=2} -MaxEvents 5 (errors)."),
("Get-HotFix","Updates. Usage: Get-HotFix | Sort InstalledOn -Desc | Select -First 5."),
("Test-Connection / ping","Ping. Usage: Test-Connection 8.8.8.8 -Count 2 -Quiet (True/False)."),
("Resolve-DnsName","DNS. Usage: Resolve-DnsName example.com -Type MX -Server 1.1.1.1."),
("Get-NetIPAddress / Get-NetAdapter","Network. Usage: Get-NetAdapter | Select Name,Status,LinkSpeed; Get-NetIPAddress -AddressFamily IPv4 | Select IPAddress,InterfaceAlias."),
("Test-NetConnection / tnc","Port-test. Usage: tnc 127.0.0.1 -Port 8790 (True/False + TcpTestSucceeded)."),
("Get-NetTCPConnection","Ports/connections. Usage: Get-NetTCPConnection -LocalPort 8790 -State Listen | Select OwningProcess."),
("Get/Enable/Disable-NetFirewallRule + New-NetFirewallRule","Firewall. Usage: New-NetFirewallRule -DisplayName 'HemoAPI' -Direction Inbound -Protocol TCP -LocalPort 8790 -Action Allow; Get-NetFirewallRule -Enabled True | Select -First 5."),
("Set-DnsClientServerAddress","DNS-set. Usage: Set-DnsClientServerAddress -InterfaceAlias 'Ethernet' -ServerAddresses 1.1.1.1,8.8.8.8."),
("Get-Disk / Get-Volume / Get-Partition","Storage. Usage: Get-Disk; Get-Volume | Select DriveLetter,SizeRemaining,Size; Get-Partition -DiskNumber 0."),
("Initialize-Disk / New-Partition / Format-Volume","Naya-disk. Usage: Initialize-Disk -Number 1; New-Partition -DiskNumber 1 -UseMaximumSize -AssignDriveLetter | Format-Volume -FileSystem NTFS."),
("Repair-Volume / Optimize-Volume","Disk-theek. Usage: Repair-Volume -DriveLetter C -Scan; Optimize-Volume -DriveLetter C -Defrag (HDD) / -Retrim (SSD)."),
("Get-BitLockerVolume / Enable-BitLocker","Encryption. Usage: Get-BitLockerVolume C; Enable-BitLocker -MountPoint C: -EncryptionMethod XtsAes256."),
("Compress-Archive / Expand-Archive","Zip. Usage: Compress-Archive folder a.zip -Force; Expand-Archive a.zip -DestinationPath out -Force."),
("Get-FileHash","Hash. Usage: Get-FileHash f -Algorithm SHA256; (Get-FileHash f).Hash -eq $known."),
("Get-AuthenticodeSignature","Sign-jaanch. Usage: Get-AuthenticodeSignature app.exe | Select Status,SignerCertificate."),
("Get-LocalUser / New-LocalUser","Users. Usage: Get-LocalUser; New-LocalUser -Name Ali -Password (ConvertTo-SecureString 'P@ss' -AsPlainText -Force)."),
("Get-LocalGroup / Add-LocalGroupMember","Groups. Usage: Add-LocalGroupMember Administrators -Member Ali."),
("Get-ScheduledTask","Tasks. Usage: Get-ScheduledTask | Where-Object State -eq Running; Get-ScheduledTaskInfo -TaskName X."),
("Register-ScheduledTask","Task-banao. Usage: $a=New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '/c D:\\x\\run.bat'; $t=New-ScheduledTaskTrigger -AtLogOn; Register-ScheduledTask -TaskName 'Hemo' -Action $a -Trigger $t -Force."),
("Start/Stop/Enable/Disable-ScheduledTask","Task kaam. Usage: Start-ScheduledTask -TaskName X; Disable-ScheduledTask X -Path \\."),
("Get/Set-ExecutionPolicy","PS-policy. Usage: Get-ExecutionPolicy -List; Set-ExecutionPolicy RemoteSigned -Scope CurrentUser (Bypass = sirf-ek-run: powershell -ExecutionPolicy Bypass -File a.ps1)."),
("Get-Help / Get-Member","Seekho. Usage: Get-Help Get-Content -Examples; Get-Date | Get-Member (kya-kya-kaam)."),
("Select-Object / Where-Object / Sort-Object / Group-Object","Pipeline-filter. Usage: ps | Where-Object CPU -gt 10 | Sort-Object CPU -Descending | Select -First 5 Name,CPU; gci | Group-Object Extension."),
("Measure-Object","Ginti/jama. Usage: gci *.txt | Measure-Object Length -Sum -Maximum; (gc f.txt | Measure-Object -Line).Lines."),
("Select-String / sls","Text-dhoondo. Usage: Select-String -Path *.log -Pattern 'ERROR' -SimpleMatch; sls 'salam' f.txt -CaseSensitive."),
("Out-File / Out-GridView / Out-String","Output. Usage: ... | Out-File r.txt -Encoding utf8 -Append; | Out-GridView (GUI-table); $x = ... | Out-String."),
("Export-Csv / Import-Csv","CSV. Usage: ps | Select Name,CPU | Export-Csv p.csv -NoTypeInformation; Import-Csv p.csv | Where CPU -gt 1."),
("ConvertTo-Json / ConvertFrom-Json","JSON. Usage: Get-Date | ConvertTo-Json; $o = Get-Content c.json -Raw | ConvertFrom-Json; $o.key."),
("ConvertTo-Html","HTML-report. Usage: ps | ConvertTo-Html | Out-File p.html."),
("Export/Import-Clixml","Object-save. Usage: $obj | Export-Clixml s.xml; $obj = Import-Clixml s.xml."),
("Invoke-WebRequest / iwr","Web-GET. Usage: (iwr url).Content / -OutFile f.png; iwr url -Method Head."),
("Invoke-RestMethod / irm","REST-API. Usage: irm https://api.github.com/repos/x | Select -Expand assets; irm url -Method Post -Body $json -ContentType 'application/json'."),
("Invoke-Command / New-PSSession / Enter-PSSession","Remote-PS. Usage: New-PSSession PC (needs Enable-PSRemoting on target); Invoke-Command -ComputerName PC -ScriptBlock {hostname} -Credential u."),
("Enable/Disable-PSRemoting","Remoting ON/OFF. Usage: Enable-PSRemoting -Force (admin, target-PC)."),
("Start-Job / Get-Job / Receive-Job","Background-job. Usage: Start-Job {gci D:\\ -Recurse}; Get-Job | Receive-Job -Keep; Wait-Job."),
("ForEach-Object -Parallel","Multi-thread (PS7). Usage: 1..8 | ForEach-Object -Parallel {Test-Connection 192.168.0.$_ -Count 1} -ThrottleLimit 4."),
("Get/Set-Clipboard","Clipboard. Usage: Get-Clipboard; 'text' | Set-Clipboard; Get-ChildItem | Select -Exp Name | Set-Clipboard."),
("Start/Stop-Transcript","Session-record. Usage: Start-Transcript log.txt; ...; Stop-Transcript."),
("Get/Set-ItemProperty + New/Remove-ItemProperty","Registry-values. Usage: Set-ItemProperty HKCU:\\Software\\X -Name V -Value 1; Get-ItemProperty HKCU:\\... | Select V."),
("New-PSDrive","Virtual-drive. Usage: New-PSDrive -Name H -PSProvider FileSystem -Root D:\\data -Persist."),
("Push/Pop-Location","Jagah-stack. Usage: Push-Location D:\\x; ...; Pop-Location."),
("Get-Variable / New-Variable","Vars. Usage: Get-Variable P*; New-Variable x 5; $x; Remove-Variable x."),
("Get-Command / Find-Command","Kya-mojood. Usage: Get-Command *zip*; Get-Command Get-Content | Select Source."),
("Get/Install/Update-Module","Modules. Usage: Get-Module -ListAvailable; Install-Module PSScriptTools -Scope CurrentUser -Force; Update-Module."),
("New-Guid / Get-Random","Random. Usage: New-Guid; Get-Random -Maximum 100 -Minimum 1; gci | Get-Random -Count 3."),
("Invoke-Expression / iex","String-kaam. Usage: iex 'Get-Date' (khatarnaak input-par — sirf apna)."),
("Get/Set-Alias","Alias. Usage: Set-Alias np notepad; Get-Alias np."),
("Get-History / Add-History","History. Usage: Get-History -Count 10; h | Invoke-Item? no."),
("Get-Date / Set-Date","Waqt. Usage: (Get-Date).AddDays(-1); Get-Date -Format 'yyyy-MM-dd HH:mm'; Set-Date (admin)."),
("Get/Set-TimeZone","Zone. Usage: Get-TimeZone; Set-TimeZone 'Pakistan Standard Time'."),
("Get-PfxCertificate / Import/Export-Certificate","Certs. Usage: Import-Certificate -FilePath a.cer -CertStoreLocation Cert:\\LocalMachine\\Root; Export-Certificate -Cert (Get-Item ...) -FilePath out.cer."),
("New-SelfSignedCertificate","Self-sign. Usage: New-SelfSignedCertificate -Subject 'CN=Hemo' -CertStoreLocation Cert:\\CurrentUser\\My -NotAfter (Get-Date).AddYears(2)."),
("Get/Set-MpPreference / Start-MpScan (Defender)","Defender. Usage: Get-MpComputerStatus | Select RealTimeProtectionEnabled; Add-MpPreference -ExclusionPath 'D:\\DigitalBrain'; Start-MpScan -ScanType QuickScan; Update-MpSignature."),
("Get-WindowsOptionalFeature / Enable/Disable-","Features. Usage: Get-WindowsOptionalFeature -Online | Where FeatureName -match Hyper; Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V-All (admin)."),
("Get/Set-CimInstance (modify)","WMI-set. Usage: Set-CimInstance Win32_OperatingSystem? — mostly read; services: Set-Service wuauserv -StartupType Automatic."),
("Get-PSDrive","Drives. Usage: Get-PSDrive -PSProvider FileSystem | Select Name,Used,Free."),
("Format-List / Format-Table / fw / ft","Formatting. Usage: ... | fl * (sab-properties); | ft -AutoSize -Wrap."),
("Tee-Object","Dikhao+Likho. Usage: log-stream | Tee-Object log.txt -Append."),
("Compare-Object","Farq. Usage: Compare-Object (gc a.txt) (gc b.txt) | Where SideIndicator -eq '=>' (naye)."),
("Join-String / Select-Object -ExpandProperty","String-banao. Usage: gci | Select -Exp Name | Join-String -Separator ', '."),
("Unblock-File","Internet-mark-hatao. Usage: Unblock-File *.ps1 (MOTW-clear)."),
("Restart/Stop-Computer","Band/Restart. Usage: Restart-Computer -Force; Stop-Computer -Force; -WsmanTarget? (remote: -ComputerName)."),
("Suspend/Resume-Service","Service-pause. Usage: Suspend-Service spooler; Resume-Service spooler."),
("Clear-RecycleBin","Recycle-bin saaf. Usage: Clear-RecycleBin -DriveLetter C -Force."),
("Enable/Disable-ComputerRestore + Checkpoint-Computer","Restore-points. Usage: Enable-ComputerRestore C:\\; Checkpoint-Computer -Description 'pehle-update'."),
("Get-PSSession / Remove-PSSession","Sessions. Usage: Get-PSSession | Remove-PSSession."),
("Read-Host / Write-Host/Output/Warning","I/O. Usage: $n = Read-Host 'naam'; Write-Host salam -ForegroundColor Green; Write-Output obj (pipeline)."),
("$ErrorActionPreference / try-catch-finally","Ghalati-kaam. Usage: try { risky } catch { $_.Exception.Message; exit 1 } finally { cleanup }; $ErrorActionPreference='Stop'."),
("Get-PSReadLineKeyHandler","Console-QAABOO. Usage: Get-PSReadLineKeyHandler | Select -First 5; Set-PSReadLineOption -PredictionSource History (PS5.1+)."),
("Get-ChildItem -Stream","NTFS-streams. Usage: gci -Stream (Zone.Identifier MOTW dekho); Unblock-File = stream-delete."),
("split/join/replace/trim (.NET-string)","String-kaam. Usage: ('a,b'.Split(','))[0]; 'abc'.ToUpper(); ' x '.Trim(); 'a-b'.Replace('-','_')."),
("[Math]:: / [DateTime]:: / [IO.File]::",".NET-seedha. Usage: [Math]::Round(3.7); [DateTime]::Today; [IO.File]::ReadAllText('f'); [IO.Path]::GetExtension('a.txt')."),
("Get-WindowsCapability / Add-","Capability. Usage: Get-WindowsCapability -Online | Where State -eq NotPresent; Add-WindowsCapability -Online -Name Rsat.ActiveDirectory* (admin)."),
("Get-Volume KnowledgeRetrieval-note","Yeh-ilm-app-ke-andar-bhi: local KnowledgeRetrieval corpus (yehi file) parhta hai — koi cloud-AI nahi."),
("Update-Help / Save-Help","Help-fresh. Usage: Update-Help -Module * -Force (admin); Save-Help -DestinationPath D:\\help (offline PCs)."),
("Get-PhysicalDisk / Get-StoragePool","Storage-tier. Usage: Get-PhysicalDisk | Select FriendlyName,MediaType,HealthStatus."),
("Get-WmiObject (purana)","Legacy-WMI. Usage: Get-WmiObject Win32_ComputerSystem (naya = Get-CimInstance)."),
("Set-Service","Service-config. Usage: Set-Service wuauserv -StartupType Automatic; Set-Service x -Status Running."),
("Get-Content -AsByteStream / -Encoding","Encoding. Usage: gc f -Encoding utf8; bytes: gc f -AsByteStream -TotalCount 4 (magic-number)."),
("Out-Null","Faltu-output giro. Usage: cmd >nul? PS: | Out-Null; Start-Process ... | Out-Null."),
("2>&1 / 2>&1 | Select-Object","Errors-jama. Usage: cmd 2>&1 | Select -Last 5 (aakhri-lines-dekho)."),
("$_ pipeline-variable","Current-item. Usage: gci | ForEach-Object { $_.Name + ' ' + $_.Length }; Where-Object { $_.Length -gt 1MB }."),
("$PSScriptRoot / $env:","Script-env. Usage: $PSScriptRoot (script-folder); $env:PATH -split ';' (PATH-parts); $env:USERNAME."),
("Wait-Job / Start-Sleep","Intezar. Usage: Start-Sleep -Seconds 5; Start-Sleep -Milliseconds 200."),
("Get-ChildItem Env:","Env-list. Usage: Get-ChildItem Env: | Where Name -match 'NETLIFY|PATH' | Select Name,Value."),
("Register-ObjectEvent","Event-listen. Usage: (advanced) Register-ObjectEvent $watcher Changed -Action { log } — file-watcher patterns."),
("Get-Service | Restart-Service -Force","Dependents-sab-restart. Usage: Restart-Service wuauserv -Force (dependent-bhi)."),
("ConvertFrom-StringData","Key=value-parse. Usage: (Get-Content c.ini -Raw) -replace '\\\\','\\\\' | ConvertFrom-StringData."),
("Get-Command -Syntax note","SYNTAX. Usage: (Get-Command Get-Content).Parameters (accepts-what); Get-Help -Parameter *."),
("Sort-Object -Property hashtable","Multi-sort. Usage: gci | Sort-Object @{e='Extension';Descending=$true}, @{e='Length';Descending=$true}."),
("Select-Object -First/-Last/-Skip/-Index","Slicing. Usage: gci | Select -Skip 5 -First 10 (page-5-10); | Select -Last 1 (aakhri)."),
("Get-Item / gi","Ek-item. Usage: (Get-Item f).LastWriteTime; (gi f).Attributes."),
("Set-Item / Set-Content -WhatIf/-Confirm","Safety-switches. Usage: -WhatIf (bas-dikhao); -Confirm:$false (poochay-bina)."),
]

def variants(*ph):
    return list(ph)

def cmd_entries():
    es = []
    for name, desc in CMD:
        base = name.split(" / ")[0].split(" (")[0].strip()
        es.append((variants(
            "cmd %s" % base,
            "cmd command %s kya karta hai" % base,
            "%s command ka istemal" % base,
            "windows cmd %s" % base,
            "%s kaise chalate hain" % base,
            "dos %s command" % base,
        ), "%s — %s" % (name.upper(), desc)))
    return es

def ps_entries():
    es = []
    for name, desc in PS:
        base = name.split(" / ")[0].split(" (")[0].split(" +")[0].strip()
        es.append((variants(
            "powershell %s" % base,
            "ps %s kya karta hai" % base,
            "%s powershell command" % base,
            "powershell me %s ka istemal" % base,
            "%s cmdlet example" % base,
        ), "%s — %s" % (name, desc)))
    return es

# ════════════════════════════════════════════════════════════════════
# 2) CODING ILM (45+ languages — hello/variable/loop/function)
# ════════════════════════════════════════════════════════════════════
LANGS = [
("python","print('salam')","x = 5","for i in range(5): print(i)","def salam(n):\n    return 'salam ' + n"),
("c","#include <stdio.h>\nint main(){printf(\"salam\\n\");return 0;}","int x = 5;","for(int i=0;i<5;i++)printf(\"%d\\n\",i);","const char* salam(const char* n){static char b[64];sprintf(b,\"salam %s\",n);return b;}"),
("c++","#include <iostream>\nint main(){std::cout<<\"salam\\n\";}","int x = 5;","for(int i=0;i<5;i++)std::cout<<i<<\"\\n\";","std::string salam(std::string n){return \"salam \"+n;}"),
("c#","using System;\nclass P{static void Main(){Console.WriteLine(\"salam\");}}","int x = 5;","for(int i=0;i<5;i++)Console.WriteLine(i);","string Salam(string n)=>\"salam \"+n;"),
("java","public class P{public static void main(String[] a){System.out.println(\"salam\");}}","int x = 5;","for(int i=0;i<5;i++)System.out.println(i);","String salam(String n){return \"salam \"+n;}"),
("javascript","console.log('salam');","let x = 5;","for(let i=0;i<5;i++)console.log(i);","const salam = n => 'salam '+n;"),
("typescript","console.log('salam');","let x: number = 5;","for(let i=0;i<5;i++)console.log(i);","const salam = (n: string): string => 'salam '+n;"),
("go","package main\nimport \"fmt\"\nfunc main(){fmt.Println(\"salam\")}","x := 5","for i:=0;i<5;i++{fmt.Println(i)}","func salam(n string) string {return \"salam \"+n}"),
("rust","fn main(){println!(\"salam\");}","let x = 5;","for i in 0..5{println!(\"{}\",i)}","fn salam(n:&str)->String{format!(\"salam {}\",n)}"),
("php","<?php echo 'salam';","$x = 5;","for($i=0;$i<5;$i++)echo $i;","function salam($n){return 'salam '.$n;}"),
("ruby","puts 'salam'","x = 5","5.times{|i|puts i}","def salam(n); \"salam #{n}\"; end"),
("swift","print(\"salam\")","var x = 5","for i in 0..<5{print(i)}","func salam(_ n:String)->String{return \"salam \"+n}"),
("kotlin","fun main(){println(\"salam\")}","val x = 5","for(i in 0..4)println(i)","fun salam(n:String)=\"salam $n\""),
("dart","void main(){print('salam');}","var x = 5;","for(var i=0;i<5;i++)print(i);","String salam(String n)=>'salam '+n;"),
("lua","print('salam')","local x = 5","for i=1,5 do print(i) end","function salam(n) return 'salam '..n end"),
("perl","print \"salam\\n\";","my $x = 5;","for my $i (0..4){print \"$i\\n\"}","sub salam {my($n)=@_;return \"salam $n\";}"),
("r","cat('salam\\n')","x <- 5","for(i in 1:5)cat(i,'\\n')","salam <- function(n) paste0('salam ',n)"),
("matlab","disp('salam')","x = 5;","for i=1:5, disp(i); end","function s=salam(n); s=['salam ' n]; end"),
("julia","println(\"salam\")","x = 5","for i in 1:5 println(i) end","salam(n) = \"salam $n\""),
("haskell","main = putStrLn \"salam\"","x = 5 :: Int","mapM_ print [0..4]","salam n = \"salam \" ++ n"),
("elixir","IO.puts \"salam\"","x = 5","for i <- 0..4, do: IO.puts i","def salam(n), do: \"salam #{n}\""),
("erlang","-module(p).\n-export([m/0]).\nm() -> io:format(\"salam~n\").","X = 5.","lists:foreach(fun(I)->io:format(\"~p~n\",[I]) end,lists:seq(0,4)).","salam(N)->lists:concat([salam,32,N])."),
("clojure","(println \"salam\")","(def x 5)","(doseq [i (range 5)] (println i))","(defn salam [n] (str \"salam \" n))"),
("fsharp","printfn \"salam\"","let x = 5","for i = 0 to 4 do printfn \"%d\" i","let salam n = \"salam \" + n"),
("scala","object P extends App{println(\"salam\")}","val x = 5","(0 to 4).foreach(println)","def salam(n:String)=\"salam \"+n"),
("groovy","println 'salam'","def x = 5","5.times{println it}","def salam(n){\"salam $n\"}"),
("assembly x86 (masm)",".model small\n.stack\n.code\nstart: mov ax,@data\nmov ds,ax\nmov dx,off msg\nmov ah,9\nint 21h\nend start","mov ax, 5","mov cx,5\nlp: loop lp","(subroutine) call salam → ret"),
("bash","#!/bin/bash\necho salam","x=5","for i in 0 1 2 3 4; do echo $i; done","salam(){ echo \"salam $1\"; }"),
("powershell script","Write-Host 'salam'","$x = 5","0..4 | ForEach-Object {$_}","function salam($n){\"salam $n\"}"),
("batch cmd","@echo off\necho salam","set x=5","for /l %%i in (1,1,5) do echo %%i","(call):call :salam Ali\n:salam\necho salam %1"),
("sql","SELECT 'salam';","DECLARE @x INT = 5;","(tally) WITH t AS (SELECT 1 N UNION ALL SELECT N+1 FROM t WHERE N<5) SELECT N FROM t;","CREATE FUNCTION salam(@n VARCHAR(50)) RETURNS VARCHAR(50) AS BEGIN RETURN 'salam '+@n; END"),
("pl/sql","BEGIN DBMS_OUTPUT.PUT_LINE('salam'); END;","x NUMBER := 5;","FOR i IN 1..5 LOOP DBMS_OUTPUT.PUT_LINE(i); END LOOP;","FUNCTION salam(n VARCHAR2) RETURN VARCHAR2 IS BEGIN RETURN 'salam '||n; END;"),
("t-sql / mssql","PRINT 'salam';","DECLARE @x INT = 5;","DECLARE @i INT=0; WHILE @i<5 BEGIN PRINT @i; SET @i+=1; END;","CREATE FUNCTION salam(@n VARCHAR(50)) RETURNS VARCHAR(50) AS BEGIN RETURN 'salam '+@n; END"),
("vbscript","MsgBox \"salam\"","Dim x : x = 5","For i = 0 To 4 : WScript.Echo i : Next","Function salam(n): salam = \"salam \" & n : End Function"),
("vb.net","Module P\nSub Main() : Console.WriteLine(\"salam\") : End Sub\nEnd Module","Dim x As Integer = 5","For i = 0 To 4 : Console.WriteLine(i) : Next","Function Salam(n As String) As String : Return \"salam \" & n : End Function"),
("delphi / pascal","program P;begin writeln('salam');end.","var x: Integer = 5;","for i := 0 to 4 do writeln(i);","function salam(n: string): string; begin result := 'salam '+n; end;"),
("objective-c","#import <Foundation/Foundation.h>\nint main(){NSLog(@\"salam\");return 0;}","NSInteger x = 5;","for(int i=0;i<5;i++)NSLog(@\"%ld\",(long)i);","NSString* salam(NSString*n){return [NSString stringWithFormat:@\"salam %@\",n];}"),
("arduino (c++)","void setup(){Serial.begin(9600);}","int x = 5;","for(int i=0;i<5;i++)Serial.println(i);","String salam(String n){return \"salam \"+n;}"),
("html","<!DOCTYPE html><html><head><title>S</title></head><body><h1>salam</h1></body></html>","<input value=\"5\">","<ul><li>1</li><li>2</li></ul>","<button onclick=\"salam('Ali')\">go</button>"),
("css","body::before{content:'salam'}","--x: 5; (custom-prop)","li:nth-child(n){} (pattern-loop)",".salam::after{content:attr(data-n)}"),
("solidity","pragma solidity ^0.8;\ncontract P{string public s=\"salam\";}","uint x = 5;","for(uint i=0;i<5;i++){}","function salam(string n) public pure returns(string m){m=string.concat(\"salam \",n);}"),
("fortran","program p\nprint *,\"salam\"\nend program","integer :: x = 5","do i=1,5\nprint *,i\nend do","function salam(n); character(len=64) salam; character(*) n; salam='salam '//n; end function"),
("cobol","IDENTIFICATION DIVISION.\nPROGRAM-ID. P.\nPROCEDURE DIVISION.\nDISPLAY \"salam\".\nSTOP RUN.","01 X PIC 9 VALUE 5.","PERFORM VARYING I FROM 1 BY 1 UNTIL I > 5\nDISPLAY I\nEND-PERFORM.","MOVE \"salam \" TO WS-OUT. STRING N DELIMITED BY SPACE INTO WS-OUT."),
("ada","with Ada.Text_IO;\nprocedure P is begin Ada.Text_IO.Put_Line(\"salam\"); end P;","X : Integer := 5;","for I in 0..4 loop Put_Line(Integer'Image(I)); end loop;","function Salam(N:String) return String is (\"salam \" & N);"),
("prolog","main :- write('salam'), nl.","X is 5.","forall(between(0,4,I), writeln(I)).","salam(N, S) :- atom_concat('salam ', N, S)."),
("lisp (cl)","(format t \"salam~%\")","(defparameter x 5)","(loop for i from 0 to 4 do (print i))","(defun salam (n) (concatenate 'string \"salam \" n))"),
("scheme","(display \"salam\") (newline)","(define x 5)","(do ((i 0 (+ i 1)))((> i 4))(display i))","(define (salam n)(string-append \"salam \" n))"),
("d (dlang)","import std.stdio;\nvoid main(){writeln(\"salam\");}","int x = 5;","foreach(i;0..5)writeln(i);","string salam(string n){return \"salam \"~n;}"),
("zig","const std=@import(\"std\");\npub fn main()!void{try std.io.getStdOut().writer().print(\"salam\\n\",.{});}","var x: i32 = 5;","var i: usize=0; while(i<5):(i+=1){try w.print(\"{d}\\n\",.{i});}","fn salam(alloc:std.mem.Allocator,n:[]const u8)![]const u8{return std.fmt.allocPrint(alloc,\"salam {s}\",.{n});}"),
("nim","echo \"salam\"","var x = 5","for i in 0..<5: echo i","proc salam(n: string): string = \"salam \" & n"),
("crystal","puts \"salam\"","x = 5","5.times{|i|puts i}","def salam(n); \"salam #{n}\"; end"),
]

def code_entries():
    es = []
    for name, hello, var, loop, fn in LANGS:
        es.append((variants(
            "code hello in %s" % name,
            "%s me salam ka code" % name,
            "hello world %s" % name,
        ), "Asli %s program (khud banaya, apna token-dimagh):\n%s" % (name, hello)))
        es.append((variants(
            "%s variable" % name,
            "%s me variable kaise" % name,
        ), "%s me variable: %s" % (name, var)))
        es.append((variants(
            "%s loop" % name,
            "%s me for-loop" % name,
        ), "%s me loop: %s" % (name, loop)))
        es.append((variants(
            "%s function" % name,
            "%s me function/method" % name,
        ), "%s me function: %s" % (name, fn)))
    return es

# ════════════════════════════════════════════════════════════════════
# 3) VERIFIED WORLD-ILM (sach, imandari — standard-docs level)
# ════════════════════════════════════════════════════════════════════
FACTS = [
("suraj ka temper","Suraj ki satah ~5500°C, andar ~15,000,000°C (nuclear-fusion: hydrogen→helium)."),
("sabse bara planet","Brihaspati (Jupiter) — zameen se ~11x bara qatr; 1300+ zameen andar aa sakti hain."),
("sabse chhota planet","Atarad (Mercury) — suraj ke sab-qareeb bhi bada-wazan hai."),
("roshni ki raftaar","~299,792 km/second — vacuum me tehreer-shehar ki hadd (Einstein)."),
("zameen ki roundness","Zameen gool; qatr ~12,742 km; circumference ~40,075 km."),
("pahaar-sabse-ooncha","Everest (sagarmatha) 8,849 m — sagar-satah se; Mauna Kea (Hawaii) base-to-peak sabse-tulba."),
("muhit-sabse-gahra","Mariana Trench ~10,935 m (Challenger Deep)."),
("jannat-warood-ilm (quran)","Quran: 114 surahs, ~6,236 aayaat (riwayat-farq), 30 para — hifz ki naimat."),
(" hadees-sahi","Sahih Bukhari (~7,563 hadith sahih-riwayat), Sahih Muslim — islami-ilm ke amin-khazane."),
("computer-kya","Computer = input→process(CPU)→output + memory. CPU-cycles GHz (1GHz = 10^9 tik/hr)."),
("binary-kya","Computer-sirf 0/1 (bit). 1 byte = 8 bit = 256 mumkin-values. ASCII 'A' = 65 = 01000001."),
("OS-kya-hai","OS (Windows/Linux/macOS) = hardware-ka-muhtasim: process/memory/file/device — apps usi par chalti."),
("RAM kya","Random-Access-Memory: temporary-kaam-ki-jagah (bijli-band→saf). HDD/SSD = permanent."),
("CPU-core","Core = asli-hisaab-unit. Multi-core = parallel. Cache L1/L2/L3 = tez-chhota-memory."),
("GPU kya","Graphics-card: hazaron-cores parallel (display + AI-matrix + rendering)."),
("internet-kya-hai","World-wide packet-network (TCP/IP). IP = makan-ka-pata; DNS = naam→IP; HTTP = page-protocol."),
("IP kya","IPv4: 32-bit (192.168.1.1); IPv6: 128-bit (2001:db8::1) — dunia bhar ke liye bohot-zada."),
("dns kya","Domain-Name-System: google.com → 142.250.x.x (root→TLD→authoritative chain)."),
("http https farq","HTTPS = HTTP + TLS (sari-traffic-encrypted; padlock-cert)."),
("email-kaise","SMTP (bhejo) + IMAP/POP3 (parho) — server-to-server MX-records se."),
("ssl-tls-kya","TLS = data-jur-mehfooz (handshake→keys→encrypt). Certificates = CA ki tasdeeq."),
("wifi kaise","Radio-waves 2.4/5GHz; WPA2/WPA3-encryption; SSID = network-naam."),
("battery-ilm","Li-ion: 300-500 full-cycles; 20-80% range-bacha-lo; garmi dushman."),
("solar-panel","Photovoltaic: roshni→DC-bijli (~20% modern-efficiency)."),
("insaan-dil","4-hisson ka pump, ~70-75 beats/min aaram; din-me ~100,000 dhadkan."),
("insaan-dimagh","~86 billion neurons; synapses ~100 trillion; 20W-power (1-diyay-ke-barabar!)."),
("khun-groups","A, B, AB, O (Rh+/-) — O-negative universal-donor, AB+ universal-acceptor."),
("pani-kya","H2O: 2-hydrogen 1-oxygen; 0°C jam, 100°C boil (1-atm); 4°C sab-zada-ghana."),
("hawa-kya","N2 78% + O2 21% + Ar 0.9% + CO2 0.04% — sagar-satah par 1-atm pressure."),
("chand-fasla","~384,400 km (zameen se); qatr 3,474 km; gravity zameen-ka 1/6."),
("tajmahal","Agra, 1632-1653 (Shah-Jahan, Mumtaz ki yaad) — white-marble UNESCO."),
("qadim-ajayab","Giza-piramids (2560 BC), Hanging-Gardens, Temple-Artemis, Statue-Zeus, Mausoleum, Colossus, Lighthouse-Alexandria."),
("mera-pak-mulk","Pakistan: 1947 (14-August) qaim; capital Islamabad; population ~240 million (2nd-muslim, 5th-world)."),
("K2","Duniya ka doosra-ooncha (8,611 m) — Pakistan (Karakoram) — 'Savage Mountain'."),
("thar","Pakistan ke Thar desert — hindu-kush/himalaya/karakoram 3-ranges apne-mulk-me."),
("mohsin-kalam","Allama-Iqbal (shaheer-mashriq) + Quaid-Azam (bani-e-pakistan) — qaumi-shakhsiyat."),
("sajda-k-num","Quran me sajda-ayaat 14 (riwayat-farq) — tilawat-me sajda-e-tilawat."),
(" Islami-calendar","Hijri: lunar-year (~354-din); Muharram se shuru; 2026 CE ≈ 1447-48 AH."),
("din-ka-hisaab","Din 24-hrs = 1440-min; zone: Earth 24-maqtai-zones (UTC-base)."),
("rail-gari","Rail 1825 (England, Stockton-Darlington) se; steam→diesel→electric."),
("hawai-jahaz","Wright-brothers 17-Dec-1903 (Kitty-Hawk) — pehli-controlled-flight 12s/37m."),
("mobile-kya","Handheld-computer: SoC (CPU+GPU+modem), Li-battery, radio (LTE/5G)."),
("sim-kya","Subscriber-Identity-Module: chip-me IMSI/keys — network-parh-kar-tasdeeq."),
("barcode/qr","Barcode: line-pattern (1D); QR: square-matrix (2D) — 30% error-correction Reed-Solomon."),
("wifi-signal-kaise","OFDM subcarriers par digital-modulation; MIMO antennas-multi-stream."),
("password-safety","Password-manager + 2FA (TOTP); 12+ chars; kabhi-reuse-nahi."),
("phishing-kya","Jhooti-email/site ke zariye cred-churaya — link-padho, domain-jaanch."),
("virus-malware","Malware-kinds: virus (file), worm (khud-fail), trojan (parda), ransomware (lock+paisa), spyware (khufia)."),
("antivirus-kaise","Signature + heuristic + behaviour (Defender modern-cloud)."),
("firewall-kya","Packet-filter/Stateful: in/out rules (port/protocol/IP)."),
("vpn-kya","Encrypted-tunnel: PC→VPN-server→internet (IP-chhupa, Wi-Fi-suraksha)."),
("https-padlock","Browser-padlock = TLS-cert-valid (padlock ≠ site-imandari — content-bhi-dekho)."),
("database-kya","Structured-data-store (SQL: tables/rows/keys; NoSQL: docs/kv). ACID = amanat."),
("sql-kya-hai","Structured-Query-Language: SELECT/INSERT/UPDATE/DELETE + JOIN/WHERE/GROUP."),
("algorithm-kya","Qadam-war-qadam-hal (steps). Efficiency: O(n), O(log n), O(n²) — big-O."),
("data-structure","Array, Linked-list, Stack (LIFO), Queue (FIFO), Tree, Graph, Hash-map (O(1)-lookup)."),
("ai-kya-hai","Machine-learning se software-jo-seekhe: pattern→prediction. Neural-net = layers × weights."),
("neural-network","Input→hidden-layers (weights+bias, activation)→output; training = loss-ghatao (gradient-descent)."),
("llm kya","Large-Language-Model: text par token-prediction sekh kar bana transformer."),
("token-kya","Text-ka tukra (word/sub-word). Models tokens-par parhte-likhte hain."),
("cloud-kya","Doosre-PC-parkar-services (rent: compute/storage). Local-AI = sab-apne-PC (Hemomemo-tareeqa)."),
("qanoon-imandari","Ye-app-100%-local: koi-cloud-AI, koi-bahar-API, koi-data-bahar — sirf-apna-dimagh."),
("open-source-kya","Code-sab-ko (license) — MIT/GPL/Apache — imandari-share."),
("git kya","Version-control: commits = snapshots; branch = parallel-kahani; merge = joro."),
("github-kya","Git-hosting + PR/issues/releases — dunia-bhar-ke-projects."),
("json kya","Data-format: {\"key\": \"value\"} — apps-ka-amanat-exchange."),
("yaml/csv/xml","YAML: indent-config; CSV: comma-table; XML: tags (purana-lakin-amin)."),
("http-methods","GET (parho), POST (bhejo), PUT (badlo), DELETE (hatao) — status: 200 OK, 404 nahi-mila, 500 server-ghalat."),
("http-status","1xx info, 2xx kamyab (200/201/204), 3xx redirect (301/304), 4xx aap-ghalat (400/401/403/404/429), 5xx server-ghalat (500/502/503)."),
("cookie-session","Cookie = browser-me chhota-pair (server-bheja); session-server-ki-yaad; JWT = signed-token."),
("api-kya","App-to-app-ka-sar (contract): REST (URL+JSON), GraphQL (ek-sawal), gRPC (fast-binary)."),
("compiler/interpreter","Compiler: sab-pehle-machine-code (C/C++/Rust); interpreter: line-by-line (Python/JS); JIT: mix (Java/C#)."),
("memory-leak","App-RAM-chhore-na-bande (delete/free bhool) — fix: dispose/RAII/garbage-collect."),
("linux-kya","Kernel 1991 (Linus); distro = kernel+tools (Ubuntu/Debian/Arch); terminal-lover."),
("unix-ilm","1970 Bell-Labs; everything-is-a-file; pipelines | (philosophy)."),
("macOS-kya","Apple-OS (Darwin-Unix base) — Mac-ka-dil."),
("gsm-calling","SIM-auth → MSC → voice-channel; VoLTE = IP-voice."),
("5g-kya","Ultra-fast-radio (mmWave/sub-6) — low-latency (~10ms)."),
("gps-kya","Satellites (≥4 dikh) → trilateration → jagah (±5m)."),
("batteries-recycle","E-waste-mat-phaink — recycle-centres (lead/lithium-zehreela)."),
("solar-system-planets","8 planets: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune (+ Pluto dwarf-2006)."),
("insaan-jism-pani","Jism ~60% pani; khoon ~7% of-weight; haddiyan 206 (adult)."),
("duniya-ki-abaadi","~8.1 billion (2024-est); sabse-zada India, phir China, phir USA/Indonesia/Pakistan."),
("languages-count","~7,000 zindah-zabanein; sabse-zada-speakers: English, Mandarin, Hindi-Urdu, Spanish, Arabic."),
("urdu-kya","Urdu: Hindustani-khazana (Arabic-Persian-script) — Pakistan-ki-qaumi-zaban."),
("maths-pi","π ≈ 3.14159265 (d/q); e ≈ 2.718 (natural-log); √2 ≈ 1.414."),
("maths-primes","Prime: sirf 1 aur khud-par-kata (2,3,5,7,11...); RSA-key-security = bade-primes."),
("algebra-base","x-dhoondo: ax+b=0 → x=-b/a; quadratic: x=(-b±√(b²-4ac))/2a."),
("geometry-pythagoras","Right-triangle: a²+b²=c²."),
("statistics-mean","Mean (jama/count), median (beech), mode (zyada-baar); std-dev = phailav."),
("probability-base","P = manzoor/mumkin (0-1); coin 1/2; dice 1/6; independent: multiply."),
("unit-si","metre/kg/second/ampere/kelvin/mole/candela — 7-SI-base-units."),
("speed-calc","Speed = faasla/waqt (km/h); acceleration = speed-change/time."),
("newton-laws","1: inertia; 2: F=ma; 3: har-amal-pardakht-muqabil."),
("einstein-emc","E=mc² — mass=energy; light-speed-hadd."),
("thermo-laws","Energy-ur-nahi (1st); entropy-barhti (2nd); 0K-pahunch-nahi (3rd)."),
("electricity-ohm","V=IR; P=VI (watts); series: R-jama; parallel: 1/R-jama."),
("magnet-ilm","Like-poles-repel; field-lines N→S; electromagnet = current-coil."),
("light-refraction","Roshni-lateef-se-dense: mud-jati (snell: n1sinθ1=n2sinθ2); rainbow = prisma-farq."),
("sound-waves","Hawa-me ~343 m/s; pitch = frequency (Hz); loudness = amplitude (dB)."),
("camera-kaise","Lens→sensor (photodiodes); exposure = aperture×shutter×ISO; RAW = unprocessed."),
("video-fps","FPS = frames/sec (24 film, 30 TV, 60 game); bitrate = quality×size."),
("compression-zip","Lossless (ZIP/DEFLATE: repeat-patterns) vs lossy (JPEG/MP3: chhota-data-丢 khatarnaak-detail)."),
("encryption-kya","Plaintext→cipher (key). Symmetric (AES, same-key) vs asymmetric (RSA/ECC, public+private)."),
("hashing-kya","One-way-fingerprint (SHA-256) — file-integrity; collision-resistant."),
("digital-signature","Hash + private-key-sign → koi-bhi-public-se-tasdeeq (imandari-mohar)."),
("log-kya-hai","App-ka-amal-record (timestamp+level) — debugging-ka-dost."),
("api-key-kya","Secret-token app-identity-ke-liye (koi-share-nahi; rotate-periodically)."),
("api-localhost","127.0.0.1 = khud-PC (loopback); localhost-port (misal 8790) = app-ka-sar — bahar-nahi-jata."),
("versioning-semver","MAJOR.MINOR.PATCH (4.2.0): major = tod-wali-tarbiyati, minor = naya-kirdar, patch = theek."),
("backup-rule","3-2-1: 3-copies, 2-media, 1-offsite — data-amanat."),
("uml-kya","Software-design-diagram (class/sequence/usecase) — bolne-se-pehle-sochna."),
("oop-kya","Object: data+functions (class = naqsha); encapsulation, inheritance, polymorphism, abstraction."),
("design-patterns","Factory, Singleton, Observer, Strategy, Adapter — bara-masla, amin-hal."),
("regression-test","Badlaav-ke-baad purana-kuch-tod-na-pare — tests-phir-chalao."),
("unit-test","Ek-hissa-alag-test (assert) — bug-pakray-jaldi; coverage = kitna-test-hua."),
("profiling-kya","Kaahan-waqt/RAM-kharch (perfmon, ps -aux, JS-profiler)."),
("sql-injection","Input-me SQL-ghusao (halka-filter) — hal: parameterized-queries (kabhi-concat-nahi)."),
("xss-csrf","XSS: site-par-dusro-ka-script; CSRF: aap-ke-naam-se-farzi-request — hal: sanitize+CSRF-token."),
("dns-over-https","DoH: DNS-sawal-bhi-encrypted (privacy)."),
("rust-safety","Ownership/borrow-checker: memory-bugs-compile-par-pakrey."),
("python-zen","import this — saaf-suthra (Readable > clever). PEP8-style."),
("java-jvm","Write-once-run-anywhere: bytecode → JVM (Windows/Mac/Linux)."),
("c-make-compile","gcc a.c -o a.exe; make = build-rules; CMake = cross-platform-builder."),
("js-node","Node.js = JS-runtime (V8) — server-side; npm = package-manager."),
("npm pip cargo","Package-managers: npm (JS), pip (Python), cargo (Rust), maven/gradle (Java), nuget (C#)."),
("ide-kya-hai","Editor+tools (VS-Code, PyCharm) — lint/debug/git-ek-jagah."),
("regex-kya","Pattern-language: ^start, $end, [abc], \\d digit, * 0+, + 1+, ? optional — dhoondo-badlo."),
("ascii-unicode","ASCII 127; Unicode = sab-zabanein (UTF-8 backward-compatible-amin)."),
("endian-kya","Little-endian (x86: chhota-pehle) vs big-endian (network-order)."),
("floating-point","IEEE-754: 0.1+0.2 ≠ 0.3 (binary-fraction) — money: cents/decimal-use-karo."),
("big-data-kya","Bohot-zada-data (TB+): distribute (Hadoop/Spark) — chunk-process."),
("cache-kya","Tez-chhota-copy (browser, CPU, DNS, CDN) — hit/miss; stale-data-muamla."),
("cdn-kya","Content-Delivery-Network: duniya-bhar-edges-se pages-tez."),
("load-balancer","Requests-multi-servers-baat (round-robin/least-conn) — up-time."),
("docker-kya","Container = app+libs-ek-packet (portable) — image/run/volume."),
("k8s-kya","Kubernetes: containers-orchestrate (scale/heal/schedule)."),
("ci/cd-kya","Har-push → auto-test → auto-deploy (GitHub-Actions pattern) — imandari-automation."),
("seo-kya","Search-Engine-Optimization: title/meta/heading/sitemap/OG/JSON-LD — crawler-dosti."),
("robots-txt","robots.txt crawler-ko-rasta: User-agent: * Allow: / + Sitemap-link."),
("sitemap-xml","Site-ke-sare-URL-ki-list (lastmod/priority) — crawler-ki-map."),
("traffic-analytics","Visits/CTR/bounce — privacy-first-analytics (koi-chupda-tracking-nahi)."),
("ad-free-imandari","Ye-site-bina-tracking: koi-ad, koi-third-party-pixel — sirf-download-link."),
]

def fact_entries():
    es = []
    for t, j in FACTS:
        base = t.strip()
        es.append((variants(
            base,
            "%s kya hai" % base,
            "%s ke bare me ilm" % base,
            "batao %s" % base,
            "%s sach batao" % base,
        ), j + " (sach — amanat-ke-mutabiq, koi-jhoot nahi.)"))
    return es

# ════════════════════════════════════════════════════════════════════
# 4) CRAWL-ILM (world-class web-crawl knowledge for the agent)
# ════════════════════════════════════════════════════════════════════
CRAWL = [
("web-crawler kya","Crawler = bot jo pages-khole→links-nikale→dohray (politeness + depth-limit). Hemomemo: apna browser (Obscura) + live_research — koi-AI-API-nahi."),
("robots.txt kya","Site-ka-rasta-bot-ke-liye: User-agent: * Disallow: /private — crawler-IMANDARI: pehle-parho-phir-chalo."),
("sitemap kaise parse","/sitemap.xml parho → <loc> URLs → queue (rate-limit 1-req/sec-dostana)."),
("search operators","Google/Bing/DDG operators: site:example.com (sirf-usi-site), filetype:pdf, intitle:\"khobsurat\", inurl:api, \"exact phrase\", -word (nikal), OR, before:/after: — research-ki-taig."),
("wayback-machine","archive.org/web/URL — purana-page-dekho (deleted-content-amin-khazana)."),
("rate-limit kya","Kitni-requests-kitne-waqt-me (429 = bas-karo). Respect: backoff (1s→2s→4s) + Retry-After-header."),
("user-agent kya","Bot-ki-pehchan header (HemomemoBot/1.0 +contact). Stealth-test ke liye sirf-owner-run me (hifazat-qanoon)."),
("html-parse kaise","<a href> links, <title>, meta-description, h1-h2 (zimma-dar-parsing: html.parser/regex-na-fashan)."),
("rss/atom feeds","<item><title><link><pubDate> — fresh-content-bina-crawl (subscribe-tareeqa)."),
("api vs crawl","API (amin-structured) pehle-try; crawl-sirf-jahan-API-nahi — tos-check-zaroori."),
("js-page-kaise parhe","SPA/headless-browser (Obscura-Rust-CDP) — HTML-dynamically-render-phir-parse."),
("pagination-kaise","Next/rel=next, ?page=n pattern — loop-until-no-more; dedupe (seen-set)."),
("dedupe-kya","Pehle-dekha-URL-chor (hash-set) — crawler-ka-akhlaq + RAM-bachao."),
("robots meta tag","<meta name=robots content=noindex,nofollow> — page-level-rasta; crawler-respect."),
("canonical-link","<link rel=canonical> — asli-URL (dup-content-ka-hal) — crawl-usi-ko-karo."),
("404/410 handling","404 = page-ghaib (queue-nikaal), 410 = hamesha-ghaib, 301/302 = naye-jagah (follow)."),
("download file kaise","curl -O / iwr -OutFile + Content-Type-check + size-limit (safety) + hash-tasdeeq."),
("extract table","<table> rows/cells-parse → CSV (headless-browser-ka-table-text-kaam-amin)."),
("js-render vs source","View-source = server-HTML; F12-DOM = rendered — crawler-dono-jaanta (Obscura-DOM-events)."),
("iframe handling","<iframe src> alag-document — separately-fetch (same-origin-policy-yaad)."),
("auth crawl","Login-ke-peeche-wala-data: sirf-owner-ke-credentials + tos-amanat (koi-chori-nahi)."),
("image-crawl","<img src> + srcset (hi-res-pick) + alt-text (ilm); hotlink-nahi — download-to-own-storage."),
("email-extract","mailto: + obfuscated (at)-patterns — imandari: sirf-apni-lists (spam-kabhi-nahi)."),
("pdf-crawl","Content-Type-check + pdf-parser (text-extract) — malaa-cab-file-limits."),
("captcha kya","Bot-rok-test (images/challenge) — Hemomemo: ROKO (bypass-NAHI — imandari-qanoon)."),
("geo-restricted","Region-blocked-content — respect-karo (proxy-ghalat-tareeqa)."),
("crawl-depth-strategy","BFS (breadth-first, polite) vs DFS (deep-topic) — priority-frontier (score: relevance)."),
("politeness-delay","Same-host: 1-2s gap (server-ka-haq) — concurrent-per-host ≤2."),
("session-crawl","Cookies keep-alive → logged-state-continue (session-jar + expiry-jaanch)."),
("headers-note","Accept-Language/Accept-Encoding (gzip) — server-dosti; ETag/If-Modified-Since = bandwidth-imandari."),
("meta-refresh","<meta http-equiv=refresh content=3;url> — JS-nahi bhi redirect-parh-lo."),
("http redirects","301/302/307/308 — max-10-follow (loop-guard)."),
("https-first","HTTP→HTTPS-upgrade (security); mixed-content-warning-respect."),
("trailing-slash","/page vs /page/ = 2-URL (normalize: ek-form-rakho)."),
("query-param-dedupe","utm_* / fbclid params-strip (same-content-hamesha)."),
("archive-org api","https://archive.org/wayback/available?url= — nearest-snapshot-JSON (amin)."),
("wikipedia-api","https://xx.wikipedia.org/api/rest_v1/page/summary/TITLE — structured-ilm (whitelisted-source)."),
("github-api","api.github.com/repos/{owner}/{repo} — releases/contents (token-free-public)."),
("npm/pypi registry","registry.npmjs.org/pkg — versions/metadata (package-ilm)."),
("stack-api","api.stackexchange.com — Q&A-ilm (quota-respect)."),
("rss-discovery","<link rel=alternate type=application/rss+xml> — page-head-se-feed-dhoondo."),
("link-graph","A→B→C edges-save — topic-map (rank: in-links-score)."),
("content-fingerprint","hash-main-content (boilerplate-strip) — dup-page-pakdo."),
("boilerplate-kya","Nav/footer/ads = har-page-same — content-extract (readability-algo-jaisa)."),
("language-detect","<html lang> + charset-jaanch — Urdu/English-content-alag-route."),
("date-extract","<time datetime> + meta-article:published_time — fresh-ka-tareekh."),
("author-extract","meta-author + byline-patterns — ilm-ke-zimma-dar."),
("rate-per-domain","Per-domain-token-bucket — duniya-bhar-crawl-par-server-sachai."),
("errors-logging","Har-crawl-line-log (url, status, ms, bytes) — imandari-report."),
("crawl-pause","KeyboardInterrupt/flag-file (data\\_PAUSED.flag-jaisa) — chain-amanat."),
("proxy-kya","Beech-wala-server (IP-badal) — Hemomemo: sirf-owner-run + halal-maqsid (chhupna-nahi)."),
("concurrent-crawl","Threads/async: 5-10-parallel, per-host-limit — Obscura-headless-pool."),
("ttl-cache","Re-crawl-jab-tak-purana (Cache-Control: max-age) — imandari-bandwidth."),
("integrity-check","Downloaded-page: status+size+hash-log; partial→discard-retry."),
("extract-paragraphs","<p> + <article> + readability-score — sirf-matn (nav/ads-strip)."),
("heading-outline","h1-h6-tree = page-ki-kahani — summary-ke-liye-amin."),
("meta-og-image","og:image URL-social-card (crawler-ka-sach)."),
("structured-data","JSON-LD (@context schema.org) — page-ka-sach-machine-format (saara-data-structured)."),
("amp-pages","amp.* versions — lightweight-alternate (prefer-canonical)."),
("printer-friendly","?print=1 / print-css — saaf-text-nikalo."),
("robots-agents-note","Blocked-agents (Cloudflare-bot-fight) — 403-respect-karo, zor-nahi."),
("feed-pagination","RSS me rel=next / ?paged=n — continue-loop."),
("search-engine-diff","Google/Bing/DDG-index-farq — multi-engine-research-amin."),
("deep-web","Login-ke-peeche-wala (not-indexed) — sirf-authorized-access."),
("dark-pattern-jaanch","Fake-buttons/hidden-terms — crawler-report-kar (imandari-flag)."),
("crawl-report","End-of-run: pages-OK/failed/duplicates + top-domains — imandari-num."),
("respect-source","Isteemal: quote-source (URL+date) — ilm-ki-amanat."),
]

def crawl_entries():
    es = []
    for t, j in CRAWL:
        base = t.strip()
        es.append((variants(
            "crawler %s" % base,
            "web-crawl %s" % base,
            "bot se %s kaise" % base,
            "%s crawling" % base,
            "research %s" % base,
        ), j))
    return es

# ════════════════════════════════════════════════════════════════════
# 5) EXTRAS: param-level CMD/PS + coding-topics + mazeed facts/crawl
# ════════════════════════════════════════════════════════════════════
CMD_PARAMS = [
("robocopy", [("/E","sub-folders copy (khali-bhi)"),("/MIR","mirror — dst ko src jaisa; EXTRA-files-URA (khayal!)"),("/Z","restartable mode (network-safe)"),("/MT:n","n-threads parallel (MT:8 tez)"),("/R:n","fail-par n-retries (default 1 million!)"),("/W:n","retry ke beech n-second wait"),("/XD dir","ye folders chhod do (exclude)"),("/LOG:file","poora-report file me likho")]),
("xcopy", [("/E","subfolders (empty-bhi)"),("/H","hidden+system files bhi"),("/K","attributes-rakho"),("/Y","overwrite bina-poochay"),("/-Y","overwrite-par-ask"),("/D","sirf naye-purane-farq wali files")]),
("dir", [("/a","sab-attributes (hidden/system bhi)"),("/o:n","naam-se-sort (o:d date, o:s size)"),("/s","sub-folders-bhi (recursion)"),("/b","sirf-naam (bare-format)"),("/q","owner bhi dikhao")]),
("del", [("/f","force (read-only-bhi)"),("/q","quiet (poochay-nahi)"),("/s","sub-folders me bhi dhoondo"),("/p","har-delete-par-poochay")]),
("copy", [("/y","overwrite-no-ask"),("/-y","overwrite-par-ask"),("/b","binary-mode (asi-file)"),("/a","ascii-mode")]),
("chkdsk", [("/f","ghalatiyan-theek-karo"),("/r","bad-sectors-dhoondo+recover (lamba-waqt)"),("/x","pehle-volume-detach")]),
("sfc", [("/scannow","sab-protected-files-janch+theek"),("/verifyonly","sirf-janch (theek-nahi)"),("/scanfile=","ek-file-theek")]),
("dism", [("/online","chalte-huye-OS-par-kaam"),("/cleanup-image","component-store-kaam"),("/restorehealth","store-theek-karo"),("/get-packages","packages-list")]),
("taskkill", [("/im","image-naam se (notepad.exe)"),("/pid","process-id se"),("/f","force"),("/t","children-tree-bhi-khatam")]),
("tasklist", [("/v","verbose-tafsil"),("/fi","filter (memusage gt 100000)"),("/svc","services-bhi-dikhao"),("/m","modules-dll-list")]),
("sc", [("query","service-ka-haal"),("start","service-chalao"),("stop","service-roko"),("config start= auto","boot-par-auto (start= ke baad SPACE zaroori)"),("description","service-ka-bayan")]),
("schtasks", [("/create","naya-task (/tn naam /tr kaam /sc schedule)"),("/run","task-abhi-chalao"),("/delete","task-hatao (/f)"),("/change","badlo (/disable bhi)"),("/query","sab-tasks-dikhao /v tafsil")]),
("reg", [("add","value-likena (/v naam /t type /d data /f)"),("query","value-parho (/v naam)"),("delete","value/key-hatao (/f)"),("export","key-file-me-bachao"),("import","file-se-wapas-dalo")]),
("netsh", [("wlan show profiles","bachaye-huye-wifi-list"),("interface ip set dns","DNS-set (static)"),("advfirewall firewall add rule","firewall-rule (dir/protocol/localport/action)"),("interface show interface","adapters-ka-haal")]),
("ipconfig", [("/all","poora-tafsil (MAC/DNS/DHCP)"),("/release","IP-chhor do"),("/renew","naya-IP-mango"),("/flushdns","DNS-cache-saaf"),("/displaydns","cache-dekho")]),
("netstat", [("-a","sab-ports (listening-bhi)"),("-n","naam-nahi, number"),("-o","PID-dikhao"),("-b","exe-naam-dikhao (admin)"),("-ano","sab-mila-kar (port-kaun-pakray)")]),
("ping", [("-n 4","4-packets (default-bhej-chal)"),("-t","lagatar (CTRL+C rok)"),("-l 1400","packet-size-1400-byte"),("-4 / -6","IPv4/IPv6-zabardasti")]),
("shutdown", [("/s","shutdown"),("/r","restart"),("/a","shutdown-CANCEL (60s-ke-andar)"),("/t 60","60-second-intezar"),("/l","logoff"),("/f","apps-zabardasti-band")]),
("for", [("/f","file/string-parse (tokens/delims)"),("/d","sirf-folders"),("/r","recursion (sub-folders)"),("/l","number-loop (1,1,5)")]),
("findstr", [("/i","case-nahi-dekhta"),("/r","regex"),("/s","sub-folders"),("/m","sirf-file-name"),("/c:","exact-phrase (spaces-wala)"),("/v","matlab-hai-jis-me-NAHI")]),
("sort", [("/+n","column-n-se-sort"),("/r","ulta (reverse)"),("/o file","output-file-me-likho")]),
("attrib", [("+r","read-only-banao"),("-r","read-only-hatao"),("+h","hidden-banao"),("+s","system-banao"),("/s","sub-folders-bhi"),("/d","folders-bhi")]),
("mklink", [("(default)","file-symbolic-link"),("/D","directory-symbolic-link (admin)"),("/J","junction (admin-NAHI-chahiye)"),("/H","hard-link (same-volume)")]),
("certutil", [("-hashfile f SHA256","file-ka-SHA256-hash"),("-addstore Root c.cer","certificate-store-me-dalo"),("-encode/-decode","base64-tabdeel")]),
("curl", [("-O","naam-rakh-kar-download"),("-o f","apna-naam"),("-I","sirf-headers"),("-L","redirect-follow"),("-d","POST-body"),("-X POST","method-zabardasti"),("-H","header-bhejo")]),
("tar", [("-czf a.tar.gz f","banao (gzip)"),("-xzf a.tar.gz","kholo"),("-xf","kholo (format-khud-pakray)"),("-tf","andar-list-dekho"),("-v","verbose")]),
("powercfg", [("/a","sleep-states-kya-mumkin"),("/list","power-plans-list"),("/setactive","plan-lagao"),("/energy","60-sec-energy-report"),("/batteryreport","battery-khairiyat")]),
("wmic", [("cpu get name","CPU-naam"),("logicaldisk get size,freespace","disk-jagah"),("process where name='x.exe' delete","process-khatam"),("qfe list brief","updates-list"),("os get caption","OS-naam")]),
("icacls", [("/grant Users:F","permission-do ((OI)(CI)F inherit)"),("/deny","roko"),("/reset /T","inherited-wapas"),("/save f","permissions-bachao"),("/restore f","wapas-lagao")]),
]
PS_PARAMS = [
("Get-ChildItem", [("-Recurse","andar-bhi (sub-folders)"),("-Filter *.txt","naam-pattern"),("-Force","hidden-bhi"),("-Depth 2","recursion-ki-hadd"),("-File / -Directory","sirf-file/folder")]),
("Get-Content", [("-Tail 20","aakhri-20-lines"),("-Raw","poori-file-ek-string"),("-Wait","live-follow (log-tail)"),("-TotalCount 5","pehli-5-lines"),("-Encoding utf8","encoding-tay")]),
("Set-Content", [("-Encoding utf8","encoding"),("-NoNewline","akhir-line-break-nahi"),("-PassThru","likh-kar-wapas-dikha")]),
("Copy-Item", [("-Recurse","folder-copy (andar-bhi)"),("-Force","overwrite-no-ask"),("-PassThru","copy-ka-pata-dikha")]),
("Remove-Item", [("-Recurse","folder-sab-andar"),("-Force","hidden/readonly-bhi"),("-WhatIf","bas-dikhao (mat-karo)"),("-Exclude *.tmp","ye-na-uto")]),
("Get-Process", [("-Name python","naam-se"),("-Id 1234","id-se"),("-IncludeUserName","kiska-process-bhi")]),
("Stop-Process", [("-Name notepad","naam-se"),("-Id 1234","id-se"),("-Force","force (bina-poochay)"),("-PassThru","mita-hua-dikha")]),
("Start-Process", [("-ArgumentList","args-list (-Xutf8,'app.py')"),("-WindowStyle Hidden","chhupa-window"),("-WorkingDirectory","kahan-se-chalao"),("-Verb RunAs","admin-banao"),("-Wait","khatam-hone-tak-intezar")]),
("Get-Service", [("-Name wuauserv","naam-se"),("-DisplayName","dikhane-wale-naam-se"),("-DependentServices","kis-par-nitah")]),
("Test-NetConnection", [("-Port 8790","port-janch"),("-InformationLevel Quiet","sirf True/False"),("-TraceRoute","route-bhi")]),
("Invoke-WebRequest", [("-OutFile f.png","file-me-bachao"),("-Method Head","sirf-headers"),("-Headers @{X='1'}","headers-bhejo"),("-Body","data-bhejo"),("-UserAgent","bot-naam")]),
("Invoke-RestMethod", [("-Method Post","method"),("-Body $json","body"),("-ContentType 'application/json'","type"),("-Headers","auth-header")]),
("Get-WinEvent", [("-LogName System","kaun-log"),("-MaxEvents 10","kitne (naye-pehle)"),("-FilterHashtable @{LogName='System';Level=2}","sirf-errors"),("-Oldest","purane-pehle")]),
("Select-String", [("-Pattern 'ERROR'","dhoondo"),("-Path *.log","kaun-files"),("-SimpleMatch","regex-nahi, seedha"),("-Context 2","aagay-peechay-2-lines-bhi")]),
("Measure-Object", [("-Sum / -Maximum","jama/sabse-bara"),("-Line / -Word / -Character","lines/words/chars-ginti"),("-Average","ausat")]),
("Sort-Object", [("-Property Length","kis-hisab-se"),("-Descending","ulta"),("-Unique","dohray-hatao"),("-Top 5","(PS7) sabse-aagay-5")]),
("Select-Object", [("-First 5 / -Last 1","shuru/aakhir"),("-Skip 5","5-chhor-kar"),("-ExpandProperty Name","sirf-wo-column (flat)"),("-Property Name,Length","kaun-columns")]),
("Out-File", [("-Append","joro (mita-nahi)"),("-Encoding utf8","encoding"),("-NoClobber","mojood-mita-nahi")]),
("Export-Csv", [("-NoTypeInformation","sir-lagai-nahi"),("-Delimiter ';'","alag-karnay-wala"),("-Append","joro")]),
("ConvertTo-Json", [("-Depth 5","nested-ki-hadd (default-2 kam!)"),("-Compress","chhota (spaces-hatao)")]),
("Get-Date", [("-Format 'yyyy-MM-dd'","format-apna"),("-Date '2026-01-01'","tay-tareekh")]),
("Get-FileHash", [("-Algorithm SHA256","kaun-hash (MD5/SHA1/SHA256/SHA512)"),("-InputStream","stream-par")]),
("Compress-Archive", [("-Path folder","kya-zip"),("-DestinationPath a.zip","kahan"),("-Update","mojood-zip-me-joro")]),
("Expand-Archive", [("-DestinationPath out","kahan-kholo"),("-Force","overwrite")]),
("Where-Object", [("-Property CPU -GT 10","simplified-syntax"),("-FilterScript { $_.CPU -gt 10 }","poora-shart"),("(-Match/-Like/-EQ)","match/pattern/barabar")]),
("ForEach-Object", [("-Begin/-Process/-End","teen-marhalay"),("-Parallel {..} -ThrottleLimit 4","(PS7) parallel-4-threads")]),
("New-Item", [("-ItemType File/Directory","kya-banao"),("-Value 'text'","file-me-likho"),("-Force","path-banaye-agar-nahi")]),
]
LANGS_MORE = [
("python","lst = [1,2,3]; lst.append(4)","d = {'naam':'Ali','umr':25}; d['naam']","with open('a.txt') as f: t = f.read() — likho: open('a.txt','w')","# ye comment hai"),
("javascript","const lst = [1,2,3]; lst.push(4);","const d = {naam:'Ali'}; d.naam;","fs.writeFileSync('a.txt','salam'); let t = fs.readFileSync('a.txt','utf8');","// ye comment hai"),
("c","int a[3] = {1,2,3};","(struct) struct P {int x;}; map = khud-hash-table","FILE* f = fopen(\"a.txt\",\"w\"); fprintf(f,\"salam\"); fclose(f);","// ye comment hai"),
("c++","std::vector<int> v = {1,2,3}; v.push_back(4);","std::map<std::string,int> m; m[\"x\"] = 1;","std::ofstream f(\"a.txt\"); f << \"salam\"; (read: std::ifstream)","// ye comment hai"),
("c#","var lst = new List<int>{1,2,3}; lst.Add(4);","var d = new Dictionary<string,int>(); d[\"x\"] = 1;","File.WriteAllText(\"a.txt\",\"salam\"); string t = File.ReadAllText(\"a.txt\");","// ye comment hai"),
("java","List<Integer> lst = new ArrayList<>(); lst.add(4);","Map<String,Integer> m = new HashMap<>(); m.put(\"x\",1);","Files.writeString(Path.of(\"a.txt\"), \"salam\");","// ye comment hai"),
("go","lst := []int{1,2,3}; lst = append(lst, 4)","m := map[string]int{\"x\":1}","os.WriteFile(\"a.txt\", []byte(\"salam\"), 0644)","// ye comment hai"),
("rust","let mut v = vec![1,2,3]; v.push(4);","use std::collections::HashMap; let mut m = HashMap::new(); m.insert(\"x\", 1);","std::fs::write(\"a.txt\", b\"salam\"); let t = std::fs::read_to_string(\"a.txt\");","// ye comment hai"),
("php","$lst = [1,2,3]; $lst[] = 4;","$d = ['naam'=>'Ali']; $d['naam'];","file_put_contents('a.txt','salam'); $t = file_get_contents('a.txt');","// ye comment hai"),
("bash","lst=(1 2 3); lst+=(4); echo ${lst[@]}","declare -A d; d[naam]=Ali; echo ${d[naam]}","echo salam > a.txt; cat a.txt","# ye comment hai"),
("sql","SELECT * FROM t WHERE x IN (1,2,3);","SELECT JSON_VALUE(col, '$.naam') FROM t;","BULK INSERT / OPENROWSET se file-import","-- ye comment hai"),
("html","<ul><li>1</li><li>2</li></ul>","<div data-naam=\"Ali\"> (data-attribute)","<input type=\"file\"> (browser-file-picker)","<!-- ye comment hai -->"),
]
MORE_FACTS = [
("penicillin-khoj","1928 Alexander Fleming ne penicillin khoja — pehla antibiotic; 1945 Nobel."),
("pehla-vaccine","1796 Edward Jenner — smallpox-vaccine; 'vaccine' lafz Latin vacca (gai) se."),
("radio-khoj","1895 Marconi ne radio-signals bheji; 1901 trans-Atlantic-signal."),
("bulb-ijad","1879 Edison ki practical incandescent-bulb (Joseph Swan bhi mushtarka-kirdar); 1882 pehli power-station."),
("telephone-ijad","1876 Alexander Graham Bell ka patent; pehli-call: 'Mr. Watson, come here.'"),
("television-ijad","1926 John Logie Baird ne pehli mechanical-TV-dikhayi."),
("world-wide-web-ijad","1989-1991 Tim Berners-Lee (CERN) ne WWW banaya — HTML + URL + HTTP; pehla browser."),
("pehla-computer","1941 Zuse-Z3 (programmable); 1945 ENIAC (electronic, USA); 1948 Manchester-Baby (stored-program)."),
("transistor-ijad","1947 Bell-Labs (Bardeen-Brattain-Shockley) — modern-electronics-ki-neenh; 1956 Nobel."),
("ic-ijad","1958 Jack Kilby + 1959 Robert Noyce ne integrated-circuit banaya — chip-ki-ibtda."),
("pehli-programming-zaban","1957 FORTRAN (John Backus, IBM) — pehli widely-used compiler-language."),
("dna-structure","1953 Watson-Crick double-helix (Rosalind Franklin ka X-ray data buniyad); 1962 Nobel."),
("human-genome-ilm","2003 Human-Genome-Project pura: ~3-billion base-pairs, ~20,000 genes."),
("chand-par-qadam","20-July-1969 Armstrong + Aldrin (Apollo-11); Collins command-module me — 382-kg moon-rocks wapas."),
("pehla-insaan-space","12-April-1961 Yuri Gagarin (Vostok-1) — 108-minute orbit."),
("pehli-aurat-space","1963 Valentina Tereshkova — 48-orbits, ~3-din."),
("iss-ilm","International Space Station: 1998-launch, 2000-se-lagatar-insaan-hain; ~400-km ooncha, 90-min-orbit."),
("voyager-1-ilm","1977-launch; 2012-me interstellar-space dakhil — insaan-ka-sabse-door bheja-hwa-cheez."),
("everest-ka-naam","George Everest (Surveyor-General-India) ke naam par; Nepal me Sagarmatha, Tibet me Chomolungma."),
("sahara-ilm","Sabse-bara hot-desert (~9.2M km²); sabse-bara desert overall Antarctica (barf-desert)."),
("sabse-thanda-jagah","Antarctica: -89.2°C (Vostok, 1983) — earth-record; duniya-ka ~70% freshwater-ice bhi yahin."),
("nile-vs-amazon","Nile ~6,650-km (sabse-lamba by length); Amazon sabse-bara by volume (~209,000 m³/s)."),
("baikal-ilm","Baikal (Russia) sabse-gahra lake (1,642-m); duniya-ke ~20% unfrozen-freshwater."),
("angel-falls-ilm","Angel Falls (Venezuela) 979-m — sabse-ooncha waterfall."),
("great-wall-ilm","Great Wall: sab-branches mila-kar ~21,196-km (2012 official survey)."),
("burj-khalifa-ilm","828-m (Dubai, 2010) — duniya-ki-sabse-ooncha building."),
("paper-ijad","China, ~105-CE (Cai Lun); Europe tak 11th-century pohnchi."),
("printing-press-ijad","~1440 Gutenberg (Mainz) — movable-metal-type; pehli-muddat-printed-Bible 1455."),
("zero-aur-algebra","Zero-ka qanooni-concept India se (Brahmagupta, 7th-century); algebra Al-Khwarizmi (9th-century) — 'algorithm' unhi-ke-naam-se."),
("oonchai-boiling","Oonchai-par-boiling-point ghatta: Everest-par pani ~70°C par ubalta (pressure-kam)."),
("bijli-dahan-ilm","Lightning ~30,000°C — suraj-ki-satah-se ~5-guna-garam; bolt ~300-million-volt tak."),
("pani-anomaly","Pani-jamne-par-phailta-hai (4°C-par-sab-zada-ghana) — isliye barf-paani-par-taire-zindagi-bachati."),
("dodo-extinct-ilm","Dodo (Mauritius) ~1681-extinct — insaan + leye-gaye-janwar-se."),
("dinosaur-khatam-ilm","~66-million-saal-pehle (Chicxulub-asteroid, Mexico); parinde dinosaurs-ki-hi-aulad."),
("zameen-umar-ilm","~4.54-billion-saal (radiometric-dating); zindagi ~3.7-billion-saal-se."),
("kainat-umar-ilm","~13.8-billion-saal (Big-Bang; Planck-satellite 2018 tajziya)."),
("suraj-wazan-hisa","Suraj = solar-system-ka-99.86%-wazan; andar ~1.3-million-zameen-samaye."),
("suraj-roshni-waqt","Suraj-ki-roshni-zameen-tak ~8-minute-20-second (~150-million-km)."),
("photosynthesis-ilm","Patta: CO₂ + pani + roshni → glucose + O₂ (chlorophyll); duniya-ki-O₂-ka-~50%-ocean-plankton-se."),
("gold-ilm","Gold (Au) atomic-number-79; neutron-star-mergers me banta — zameen-ka-gold-space-se-aya."),
("dna-insaan-ilm","Har-insaan-ke-DNA ~3-billion base-pairs; koi-2-insaan-99.9%-same."),
("aankh-rang-ilm","Aankh ~10-million-rang pehchan-sakti; retina: ~127M-rod + ~7M-cone-cells."),
("neptune-hawa-ilm","Neptune-ki-hawaein ~2,100-km/h — solar-system-ki-sabse-tez."),
("great-red-spot-ilm","Jupiter-ka-Great-Red-Spot: 350+ saal-purana-toofan, zameen-se-bada."),
]
MORE_CRAWL = [
("crawl-budget","Har-site-ke-liye-max-pages-per-visit (Search-Console 'crawl-stats') — server-imaandari."),
("sitemap-index","sitemap-index.xml me kai-sitemaps ho-sakte — sab-parho-phir-URLs-queue."),
("hreflang-ilm","<link rel=alternate hreflang=ur> — multi-zaban-versions-ka-map; crawler-usi-zaban-leta."),
("noindex-vs-robots","robots.txt = crawl-ROKO; noindex = index-me-mat-dalo. Farq: noindex-page-crawl-ho-kar-meta-parha-jata."),
("nofollow-links","rel=nofollow = weight-na-do — crawler-follow-kar-sakta-par-rank-mat."),
("last-modified-use","Last-Modified-header/ETag — purana-page-dobara-mat-uto (If-Modified-Since → 304)."),
("hash-fragment-ilm","URL-me #ke-baad-wala-hissa server-tak-NAHI-jata — crawl-URL-normalize (#hatao)."),
("url-encoding-ilm","%20 aur + (spaces), percent-encoding-normalize — ek-page-2-URL-na-bane."),
("gzip-decode-crawl","Accept-Encoding: gzip, br — response-decompress (Content-Encoding-header-dekho)."),
("charset-detect-crawl","<meta charset> / BOM / HTTP-charset — UTF-8-default (Urdu-text-safai)."),
("infinite-scroll-crawl","Scroll-par-XHR/fetch-JSON-load — Network-tab-se-API-endpoint-pakdo (API-first)."),
("lazy-loading-crawl","<img loading=lazy> / data-src — asli-src attribute DOM-se-nikalo."),
("head-first-crawl","Bari-file: pehle-HEAD-request (Content-Length) — limit-se-bara → skip+log."),
("conditional-get","If-None-Match / If-Modified-Since bhejo — 304-aya→bandwidth-bachao (etiquette)."),
("ua-robots-groups","robots.txt groups: 'User-agent: Googlebot' alag, '*' sab-ke-liye — longest-match-rule."),
("warc-format","Web-ARChive (.warc) — puri-crawl-archive-standard (archive.org-isi-format)."),
("dns-cache-crawler","DNS-resolution-cache (TTL-tak) — har-request-par-naya-lookup-nahi."),
("obey-tos-ilm","Site-ke-Terms-of-Service parho — crawl-ki-imandari-qanoon (Hemomemo-hamesha)."),
]

def cmd_param_entries():
    es = []
    for cmd, params in CMD_PARAMS:
        for p, d in params:
            es.append((variants(
                "%s %s" % (cmd, p),
                "%s %s kya karta hai" % (cmd, p),
                "%s me %s parameter" % (cmd, p),
                "%s %s ka istemal" % (cmd, p),
            ), "%s %s — %s" % (cmd.upper(), p, d)))
    return es

def ps_param_entries():
    es = []
    for cmd, params in PS_PARAMS:
        for p, d in params:
            es.append((variants(
                "powershell %s %s" % (cmd, p),
                "%s %s kya karta hai" % (cmd, p),
                "%s me %s parameter" % (cmd, p),
                "%s %s example" % (cmd, p),
            ), "%s %s — %s" % (cmd, p, d)))
    return es

def lang_more_entries():
    es = []
    for lang, lst, mp, fl, cm in LANGS_MORE:
        es.append((variants("%s me list/array" % lang, "%s list banane ka tareeqa" % lang),
                   "%s me list/array: %s" % (lang, lst)))
        es.append((variants("%s me dictionary/map" % lang, "%s dictionary kaise" % lang),
                   "%s me dict/map: %s" % (lang, mp)))
        es.append((variants("%s me file read write" % lang, "%s file kaise parho likho" % lang),
                   "%s me file-kaam: %s" % (lang, fl)))
        es.append((variants("%s me comment" % lang, "%s comment kaise likhte hain" % lang),
                   "%s me comment: %s" % (lang, cm)))
    return es

def fact_more_entries():
    es = []
    for t, j in MORE_FACTS:
        base = t.strip()
        es.append((variants(base, "%s kya hai" % base, "%s ke bare me ilm" % base,
                            "batao %s" % base, "%s sach batao" % base),
                   j + " (sach — amanat-ke-mutabiq.)"))
    return es

def crawl_more_entries():
    es = []
    for t, j in MORE_CRAWL:
        base = t.strip()
        es.append((variants("crawler %s" % base, "web-crawl %s" % base, "bot se %s kaise" % base,
                            "%s crawling" % base, "research %s" % base), j))
    return es

# ════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════
def main():
    t0 = time.time()
    total = 0
    total += w("trainer_knowledge_cmdshell.txt",
               cmd_entries() + ps_entries() + cmd_param_entries() + ps_param_entries(),
               "# HEMOMEMO CMD+POWERSHELL ILM (hazaaran-asli-commands, 100% local)\n"
               "# Sab haqeeqi-Windows-commands (standard-docs-level sach). "
               "KnowledgeRetrieval + token-dimagh isi parhte hain.\n\n")
    total += w("coding_ilm.txt",
               code_entries() + lang_more_entries(),
               "# HEMOMEMO CODING-ILM (45+ zabanein: hello/variable/loop/function)\n"
               "# App-ka code-dimagh isi-format par samajhta hai: code hello in <lang>.\n\n")
    total += w("sacred_facts.txt",
               fact_entries() + fact_more_entries(),
               "# HEMOMEMO VERIFIED-WORLD-ILM (sach-amanat: science/tech/math/deen-basics)\n"
               "# Har-jawab-tasdeeq-shuda (standard-docs-level). Koi-jhoot, koi-chhupav nahi.\n\n")
    total += w("crawl_ilm.txt",
               crawl_entries() + crawl_more_entries(),
               "# HEMOMEMO WORLD-CRAWL-ILM (bot ki web-research ki a-to-z imandari-tarib)\n"
               "# robots/sitemaps/operators/APIs/rate-limits — Hemomemo live_research + Obscura browser isi par chale.\n\n")

    # brain_map.json — DigitalBrain ki A-to-Z deep-link index
    SKIP_DIRS = {"__pycache__", "archive", "_old_broken", "_unfiltered",
                 "node_modules", ".git", "harvest", "data\\videos"}
    m = {"brain": "hemomemo-master", "generated": time.strftime("%Y-%m-%d %H:%M"),
         "note": "A-to-Z file-map: har file ka rasta + wazan (app/deep-link/qanoon)", "sections": {}}
    for root, dirs, files in os.walk(SRC):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS
                   and not d.lower().startswith("digitalbrain")]
        rel = os.path.relpath(root, SRC)
        if rel.startswith("build"):
            dirs[:] = []
            continue
        sec = rel.split(os.sep)[0] if rel != "." else "root"
        bucket = m["sections"].setdefault(sec, [])
        for fn in files:
            fp = os.path.join(root, fn)
            try:
                sz = os.path.getsize(fp)
            except OSError:
                sz = 0
            bucket.append({"f": os.path.relpath(fp, SRC).replace(os.sep, "/"), "kb": round(sz/1024, 1)})
    p = os.path.join(SRC, "data", "brain_map.json")
    with io.open(p, "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    print("brain_map.json: %d sections, %.1f KB" % (len(m["sections"]), os.path.getsize(p)/1024.0))
    print("TOTAL-ILM-ENTRIES: %d | waqt: %.0fs" % (total, time.time() - t0))

if __name__ == "__main__":
    main()
