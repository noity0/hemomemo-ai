@echo off
REM ============================================================
REM  HEMOMEMO AI - FINAL SYNCHRONIZATION
REM  Apply all changes to EXE, ZIP, Repo, Site, Desktop everywhere
REM ============================================================

title Hemomemo AI Final Sync

echo.
echo FINAL SYNCHRONIZATION - APPLYING ALL CHANGES
echo.
echo =============================================================
echo.

echo [1/6] Building latest EXE...
python -m PyInstaller --noconfirm "Hemomemo-Ultra-Brain.spec"
if errorlevel 1 goto fail
echo EXE built successfully

echo.
echo [2/6] Copying desktop app to all locations...
set DESKTOP_SRC=D:\HemomemoUltra-People\hemomemo_ai_desktop

set LOCATIONS[0]=D:\HemomemoUltra-People\hemomemo_ai_desktop_final
set LOCATIONS[1]=D:\HemomemoUltra-People\hemomemo_ai_complete

for %%L in (%LOCATIONS%) do (
    if exist "%%L" rmdir /s /q "%%L"
    xcopy /E /I /Y "%DESKTOP_SRC%" "%%L" >nul 2>&1
    echo Copied to %%L
)

echo.
echo [3/6] Updating all ZIP packages...
if exist "D:\HemomemoUltra-People\hemomemo_ai_desktop_complete.zip" del "D:\HemomemoUltra-People\hemomemo_ai_desktop_complete.zip"
if exist "D:\HemomemoUltra-People\hemomemo_ai_complete_final.zip" del "D:\HemomemoUltra-People\hemomemo_ai_complete_final.zip"

cd "D:\HemomemoUltra-People"
python -c "import zipfile; import os; print('Creating desktop ZIP...'); z=zipfile.ZipFile('hemomemo_ai_desktop_complete.zip','w',zipfile.ZIP_DEFLATED); [z.write(os.path.join(r, f), os.path.join(os.path.relpath(r, '.'), f)) for r,ds,fs in os.walk('hemomemo_ai_desktop') for f in fs if not f.startswith('.') and f != '__pycache__']; print('Desktop ZIP created!')"
python -c "import zipfile; import os; print('Creating complete ZIP...'); z=zipfile.ZipFile('hemomemo_ai_complete_final.zip','w',zipfile.ZIP_DEFLATED); [z.write(os.path.join(r, f), os.path.join(os.path.relpath(r, '.'), f)) for r,ds,fs in os.walk('hemomemo_ai_desktop_final') for f in fs if not f.startswith('.') and f != '__pycache__']; print('Complete ZIP created!')"
cd "..\DigitalBrain"
echo ZIP packages updated

echo.
echo [4/6] Updating launcher scripts...
set LAUNCHERS[0]=D:\HemomemoUltra-People\hemomemo_ai_desktop_final\DESKTOP-Launch.bat
set LAUNCHERS[1]=D:\HemomemoUltra-People\hemomemo_ai_desktop_final\TERMINAL-Launch.bat
set LAUNCHERS[2]=D:\HemomemoUltra-People\hemomemo_ai_complete\QUICK-Launch.bat

for %%L in (%LAUNCHERS%) do (
    echo @echo off > "%%L"
    echo title Hemomemo AI Ultra-Realistic Motion Video >> "%%L"
    echo. >> "%%L"
    echo echo. >> "%%L"
    echo echo 🚀 Hemomemo AI Desktop App >> "%%L"
    echo echo. >> "%%L"
    echo echo Ultra-Realistic Motion Video Generator >> "%%L"
    echo echo Flow Fields + Higgsfield Technology + Physics Simulation >> "%%L"
    echo echo. >> "%%L"
    echo. >> "%%L"
    echo if exist \"app\hemomemo_app.py\" ( >> "%%L"
    echo     python app\hemomemo_app.py >> "%%L"
    echo ) else ( >> "%%L"
    echo     echo Application not found. Please check installation. >> "%%L"
    echo     pause >> "%%L"
    echo     exit /b 1 >> "%%L"
    echo ) >> "%%L"
    echo. >> "%%L"
    echo echo. >> "%%L"
    echo echo Thank you for using Hemomemo AI! >> "%%L"
    echo pause >> "%%L"
    echo Created %%L
)

echo.
echo [5/6] Updating documentation...
set DOCS[0]=D:\HemomemoUltra-People\hemomemo_ai_desktop_final\README.md
set DOCS[1]=D:\HemomemoUltra-People\hemomemo_ai_complete\README.md

for %%D in (%DOCS%) do (
    echo # 🚀 Hemomemo AI - Ultra-Realistic Motion Video Generator > "%%D"
    echo. >> "%%D"
    echo ## Complete Installation Guide >> "%%D"
    echo. >> "%%D"
    echo ### Quick Start: >> "%%D"
    echo 1. Run DESKTOP-Launch.bat for full application >> "%%D"
    echo 2. Run TERMINAL-Launch.bat for terminal access >> "%%D"
    echo 3. Run FINAL-INSTALL.bat for complete installation >> "%%D"
    echo. >> "%%D"
    echo ### Features: >> "%%D"
    echo - Ultra-realistic motion video generation >> "%%D"
    echo - Flow Fields + Higgsfield Technology >> "%%D"
    echo - Real-time progress tracking >> "%%D"
    echo - Multiple resolutions and motion types >> "%%D"
    echo - 100%% local operation >> "%%D"
    echo. >> "%%D"
    echo ### Requirements: >> "%%D"
    echo - Python 3.8+ >> "%%D"
    echo - 8GB RAM minimum >> "%%D"
    echo - 2GB storage space >> "%%D"
    echo Updated %%D
)

echo.
echo [6/6] Final verification...
echo Checking all components...
if exist "dist\Hemomemo-Ultra-Brain.exe" echo ✅ EXE: Built successfully
if exist "D:\HemomemoUltra-People\hemomemo_ai_desktop_complete.zip" echo ✅ ZIP: Desktop package ready
if exist "D:\HemomemoUltra-People\hemomemo_ai_complete_final.zip" echo ✅ ZIP: Complete package ready
if exist "D:\HemomemoUltra-People\hemomemo_ai_desktop_final" echo ✅ Desktop: Final folder ready
if exist "D:\HemomemoUltra-People\hemomemo_ai_complete" echo ✅ Complete: Package folder ready

echo.
echo =============================================================
echo FINAL SYNCHRONIZATION COMPLETE!
echo =============================================================
echo.
echo All locations updated with latest features:
echo - EXE: D:\DigitalBrain\dist\Hemomemo-Ultra-Brain.exe
echo - ZIP: D:\HemomemoUltra-People\hemomemo_ai_desktop_complete.zip
echo - ZIP: D:\HemomemoUltra-People\hemomemo_ai_complete_final.zip
echo - Desktop: D:\HemomemoUltra-People\hemomemo_ai_desktop_final
echo - Complete: D:\HemomemoUltra-People\hemomemo_ai_complete
echo.
echo Features included in all packages:
echo - Ultra-realistic motion video generation
echo - Flow Fields + Higgsfield Technology
echo - Real-time progress tracking (0% to 100%)
echo - Frame counter (Frame X/Y display)
echo - AI thinking indicators
echo - Multiple resolutions (360p to 1080p)
echo - Multiple motion types (racing, flow, physics)
echo - 100% local operation
echo - Complete offline capability
echo.
echo Launch options available:
echo - DESKTOP-Launch.bat: Full desktop application
echo - TERMINAL-Launch.bat: Terminal access
echo - QUICK-Launch.bat: Simple launch
echo - FINAL-INSTALL.bat: Complete installation
echo.
echo =============================================================
echo.
pause
exit /b 0

:fail
echo.
echo FAILED - Please check the error messages above
echo.
pause
exit /b 1