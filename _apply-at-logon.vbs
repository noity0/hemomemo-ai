' Hemomemo AI — boot/logon pe apply-chain khud resume (qanoon: 24/7)
' Koi window nahi, seedha background me chain chal padegi (Task-Scheduler
' "HemomemoApplyNow" wali apply-log me likhta rahega).
On Error Resume Next
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """D:\DigitalBrain\_APPLY-NOW.bat""", 0, False
