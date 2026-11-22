@echo off
REM ============================================================
REM  HEMOMEMO AI — APPLY TRAINING EVERYWHERE (manual trigger)
REM  Training ke checkpoints sab jagah a→z apply:
REM  desktop app folder + hemomemo_ai_desktop + zips + repo + 2 sites
REM ============================================================
cd /d D:\DigitalBrain
py -3.12 -Xutf8 _apply_training_everywhere.py
pause
