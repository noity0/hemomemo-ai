@echo off
REM ============================================================
REM  HEMOMEMO — APPLY-TRAINING-EVERYWHERE (Task-Scheduler launch)
REM  OpenCode/terminal band ya server-restart ho — chain sarakhti rahegi.
REM ============================================================
cd /d D:\DigitalBrain
REM PAUSE-QANOON: STOP-HEMOMEMO.bat ne roka ho to chain kuch nahi karti
if exist "D:\DigitalBrain\data\_PAUSED.flag" exit /b
"C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" -Xutf8 _apply_training_everywhere.py >> data\_apply_chain3.log 2>&1
