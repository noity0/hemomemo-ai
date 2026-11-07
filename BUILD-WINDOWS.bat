@echo off
REM ============================================================
REM  HEMOMO AI - WINDOWS BUILD WORKFLOW (7 se 11 Pro tak)
REM  Ye script pura build imandari se banati hai:
REM    1) Tests (memory / reasoning / mc-bot)  - pehle sach
REM    2) EXE build (PyInstaller, Hemomemo-Ultra-Brain.spec)
REM    3) Package (make_package.py - 96+ files + SHA-256 manifest)
REM  NO AI-API. NO cloud. Sirf aap ka PC.
REM ============================================================
cd /d %~dp0
setlocal

echo [1/3] TESTS chal rahe hain (honest)...
py -3 tests\test_new_modules.py
if errorlevel 1 goto :fail

echo.
echo [2/3] EXE build (PyInstaller)...
py -3 -m PyInstaller --noconfirm "Hemomemo-Ultra-Brain.spec"
if errorlevel 1 goto :fail

echo.
echo [3/3] PACKAGE bana rahe hain (zip ke liye)...
py -3 scripts\make_package.py
if errorlevel 1 goto :fail

echo.
echo ==============================================
echo   BUILD-OK: tests pass + EXE + package tayar
echo   Chalao: D:\HemomemoUltra-People\START-HEMOMO.bat
echo ==============================================
exit /b 0

:fail
echo.
echo BUILD-FAIL - upar ki honest error dekho (koi jhoot nahi).
exit /b 1
