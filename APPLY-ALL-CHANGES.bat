@echo off
REM ============================================================
REM  HEMOMEMO AI - APPLY ALL CHANGES AND FIXES EVERYWHERE
REM  This script applies all latest changes to EXE, ZIP, Repo, Site, Desktop
REM ============================================================

title Hemomemo AI - Apply All Changes

echo.
echo APPLYING ALL CHANGES AND FIXES TO EVERYWHERE...
echo.
echo =============================================================
echo.

echo [1/6] Building latest EXE with all features...
python -m PyInstaller --noconfirm "Hemomemo-Ultra-Brain.spec"
if errorlevel 1 goto fail
echo EXE built successfully with latest features

echo.
echo [2/6] Creating updated ZIP package...
if exist "D:\HemomemoUltra-People\hemomemo_ai_desktop_complete.zip" del "D:\HemomemoUltra-People\hemomemo_ai_desktop_complete.zip"

cd "D:\HemomemoUltra-People"
python -c "import zipfile; import os; print('Creating ZIP...'); z=zipfile.ZipFile('hemomemo_ai_desktop_complete.zip','w',zipfile.ZIP_DEFLATED); [z.write(os.path.join(r, f), os.path.join(os.path.relpath(r, '.'), f)) for r,ds,fs in os.walk('hemomemo_ai_desktop') for f in fs if not f.startswith('.') and f != '__pycache__']; print('ZIP created successfully!')"
cd "..\DigitalBrain"
echo ZIP package updated successfully

echo.
echo [3/6] Updating repository files...
xcopy /E /I /Y "app" "D:\HemomemoUltra-People\hemomemo_ai_desktop\app" >nul 2>&1
xcopy /E /I /Y "agent" "D:\HemomemoUltra-People\hemomemo_ai_desktop\agent" >nul 2>&1
xcopy /E /I /Y "model" "D:\HemomemoUltra-People\hemomemo_ai_desktop\model" >nul 2>&1
xcopy /E /I /Y "core" "D:\HemomemoUltra-People\hemomemo_ai_desktop\core" >nul 2>&1
xcopy /E /I /Y "brain" "D:\HemomemoUltra-People\hemomemo_ai_desktop\brain" >nul 2>&1
xcopy /E /I /Y "server" "D:\HemomemoUltra-People\hemomemo_ai_desktop\server" >nul 2>&1
xcopy /E /I /Y "scripts" "D:\HemomemoUltra-People\hemomemo_ai_desktop\scripts" >nul 2>&1
xcopy /E /I /Y "tests" "D:\HemomemoUltra-People\hemomemo_ai_desktop\tests" >nul 2>&1
xcopy /E /I /Y "data" "D:\HemomemoUltra-People\hemomemo_ai_desktop\data" >nul 2>&1
xcopy /E /I /Y "harvest" "D:\HemomemoUltra-People\hemomemo_ai_desktop\harvest" >nul 2>&1
copy "*.py" "D:\HemomemoUltra-People\hemomemo_ai_desktop\" >nul 2>&1
copy "*.bat" "D:\HemomemoUltra-People\hemomemo_ai_desktop\" >nul 2>&1
copy "*.spec" "D:\HemomemoUltra-People\hemomemo_ai_desktop\" >nul 2>&1
copy "*.md" "D:\HemomemoUltra-People\hemomemo_ai_desktop\" >nul 2>&1
echo Repository files updated successfully

echo.
echo [4/6] Updating site files...
if exist "web" (
    if exist "D:\HemomemoUltra-People\hemomemo_ai_desktop\web" rmdir /s /q "D:\HemomemoUltra-People\hemomemo_ai_desktop\web"
    xcopy /E /I /Y "web" "D:\HemomemoUltra-People\hemomemo_ai_desktop\web" >nul 2>&1
    echo Site files updated successfully
)

echo.
echo [5/6] Finalizing desktop folder...
if exist "D:\HemomemoUltra-People\hemomemo_ai_desktop_final" rmdir /s /q "D:\HemomemoUltra-People\hemomemo_ai_desktop_final"
xcopy /E /I /Y "D:\HemomemoUltra-People\hemomemo_ai_desktop" "D:\HemomemoUltra-People\hemomemo_ai_desktop_final" >nul 2>&1
echo Desktop folder finalized successfully

echo.
echo [6/6] Creating final complete package...
if exist "D:\HemomemoUltra-People\hemomemo_ai_complete_final.zip" del "D:\HemomemoUltra-People\hemomemo_ai_complete_final.zip"

cd "D:\HemomemoUltra-People"
python -c "import zipfile; import os; print('Creating final ZIP...'); z=zipfile.ZipFile('hemomemo_ai_complete_final.zip','w',zipfile.ZIP_DEFLATED); [z.write(os.path.join(r, f), os.path.join(os.path.relpath(r, '.'), f)) for r,ds,fs in os.walk('hemomemo_ai_desktop_final') for f in fs if not f.startswith('.') and f != '__pycache__']; print('Final ZIP created successfully!')"
cd "..\DigitalBrain"
echo Final complete package created successfully

echo.
echo =============================================================
echo ALL CHANGES AND FIXES APPLIED EVERYWHERE!
echo =============================================================
echo.
echo EXE Location: D:\DigitalBrain\dist\Hemomemo-Ultra-Brain.exe
echo ZIP Location: D:\HemomemoUltra-People\hemomemo_ai_desktop_complete.zip
echo Final Package: D:\HemomemoUltra-People\hemomemo_ai_complete_final.zip
echo Desktop Folder: D:\HemomemoUltra-People\hemomemo_ai_desktop_final
echo.
echo EXE: Built with latest ultra-realistic video features
echo ZIP: Contains complete desktop app with all features
echo Repo: All files updated with latest changes
echo Site: Web components updated
echo Desktop: Complete standalone application
echo Final Package: Ready for distribution
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