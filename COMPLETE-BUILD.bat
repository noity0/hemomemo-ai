@echo off
REM ============================================================
REM  HEMOMEMO AI - COMPLETE BUILD WORKFLOW
REM  This script builds everything with latest features
REM ============================================================

title Hemomemo AI Complete Build

echo.
echo 🚀 Starting Complete Hemomemo AI Build...
echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║  ULTRA-REALISTIC MOTION VIDEO GENERATOR EDITION        ║
echo ║  Flow Fields + Higgsfield + Physics Simulation         ║
echo ╚════════════════════════════════════════════════════════╝
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+ and try again.
    pause
    exit /b 1
)

echo [1/6] Cleaning previous builds...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build
if exist "D:\HemomemoUltra-People\hemomemo_ai_desktop" rmdir /s /q "D:\HemomemoUltra-People\hemomemo_ai_desktop"
echo ✅ Cleaned previous builds

echo [2/6] Running tests...
python tests\test_new_modules.py
if errorlevel 1 goto fail
echo ✅ Tests passed

echo [3/6] Building desktop app components...
mkdir "D:\HemomemoUltra-People\hemomemo_ai_desktop"
xcopy /E /I /Y "app" "D:\HemomemoUltra-People\hemomemo_ai_desktop\app"
xcopy /E /I /Y "agent" "D:\HemomemoUltra-People\hemomemo_ai_desktop\agent"
xcopy /E /I /Y "model" "D:\HemomemoUltra-People\hemomemo_ai_desktop\model"
xcopy /E /I /Y "core" "D:\HemomemoUltra-People\hemomemo_ai_desktop\core"
xcopy /E /I /Y "brain" "D:\HemomemoUltra-People\hemomemo_ai_desktop\brain"
xcopy /E /I /Y "server" "D:\HemomemoUltra-People\hemomemo_ai_desktop\server"
xcopy /E /I /Y "scripts" "D:\HemomemoUltra-People\hemomemo_ai_desktop\scripts"
xcopy /E /I /Y "tests" "D:\HemomemoUltra-People\hemomemo_ai_desktop\tests"
xcopy /E /I /Y "data" "D:\HemomemoUltra-People\hemomemo_ai_desktop\data"
xcopy /E /I /Y "harvest" "D:\HemomemoUltra-People\hemomemo_ai_desktop\harvest"
echo ✅ Desktop app components copied

echo [4/6] Copying configuration files...
copy "*.py" "D:\HemomemoUltra-People\hemomemo_ai_desktop\" >nul 2>&1
copy "*.bat" "D:\HemomemoUltra-People\hemomemo_ai_desktop\" >nul 2>&1
copy "*.spec" "D:\HemomemoUltra-People\hemomemo_ai_desktop\" >nul 2>&1
copy "*.md" "D:\HemomemoUltra-People\hemomemo_ai_desktop\" >nul 2>&1
echo ✅ Configuration files copied

echo [5/6] Building EXE...
python -m PyInstaller --noconfirm "Hemomemo-Ultra-Brain.spec"
if errorlevel 1 goto fail
echo ✅ EXE built successfully

echo [6/6] Creating distribution package...
cd "D:\HemomemoUltra-People"
python -c "import zipfile; import os; print('Creating ZIP...'); z=zipfile.ZipFile('hemomemo_ai_desktop_complete.zip','w',zipfile.ZIP_DEFLATED); [z.write(os.path.join(r, f), os.path.join(os.path.relpath(r, '.'), f)) for r,ds,fs in os.walk('hemomemo_ai_desktop') for f in fs if not f.startswith('.') and f != '__pycache__']; print('ZIP created successfully!')"
cd ..
echo ✅ Distribution package created

echo.
echo ╔════════════════════════════════════════════════════════╗
echo ║  BUILD COMPLETE!                                      ║
echo ║                                                      ║
echo ║  Complete Hemomemo AI Desktop App ready!              ║
echo ║                                                      ║
echo ║  Locations:                                          ║
echo ║  📁 Desktop App: D:\HemomemoUltra-People\hemomemo_ai_desktop\ ║
echo ║  📦 Distribution: D:\HemomemoUltra-People\hemomemo_ai_desktop_complete.zip ║
echo ║  🚀 EXE: D:\DigitalBrain\dist\Hemomemo-Ultra-Brain.exe ║
echo ║                                                      ║
echo ║  Launch with:                                         ║
echo ║  • HEMOMEMO-DESKTOP.bat (in desktop app folder)       ║
echo ║  • START-HEMOMO.bat (in distribution folder)         ║
echo ║                                                      ║
echo ║  Features:                                           ║
echo ║  ✓ Ultra-Realistic Motion Video Generator            ║
echo ║  ✓ Flow Fields Technology                             ║
echo ║  ✓ Higgsfield Volumetric Rendering                   ║
echo ║  ✓ Real-time Progress Display                         ║
echo ║  ✓ Multiple Resolutions                              ║
echo ║  ✓ 100% Local Operation                              ║
echo ╚════════════════════════════════════════════════════════╝
echo.

echo Build completed successfully!
echo.
pause
exit /b 0

:fail
echo.
echo ❌ BUILD FAILED - Please check the error messages above
echo.
pause
exit /b 1