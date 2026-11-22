@echo off
title Hemomemo API Key — OpenCode Integration
echo.
echo  === HEMOMEMO API KEY SISTEM (HMHS) ===
echo  Ye tile aap ki APNI key khud set karne ke liye hai.
echo  Key Hemomemo app me Sign-up/Sign-in se milti hai (hemo... format).
echo.
set /p HEMOKEY=  Apni hemo... key paste karke Enter dabayen: 

if "%HEMOKEY%"=="" (
  echo  [X] Key khali — kuch nahi badla.
  pause
  exit /b 1
)

echo   %HEMOKEY% | findstr /b /c:"hemo" >nul
if errorlevel 1 (
  echo  [X] Hemomemo key "hemo..." se shuru hoti hai — ye format ghalat hai.
  pause
  exit /b 1
)

rem  1) Env (baaki tools ke liye)
setx HEMOMEMO_API_KEY "%HEMOKEY%" >nul
echo  [1/2] Env HEMOMEMO_API_KEY set.

rem  2) OpenCode config me key (direct - dono config jagah, env-par na depends)
set HEMOKEY_TMP=%HEMOKEY%
py -3 -c "import json, os; p1=r'D:\Opencode\config\opencode\opencode.json'; p2=r'C:\Users\user\.config\opencode\opencode.json'; k=os.environ.get('HEMOKEY_TMP','').strip(); assert k.startswith('hemo'), 'key khali/ghalat — config NAHI badli'; d=json.load(open(p1,encoding='utf-8')); d['provider']['hemomemo']['options']['apiKey']=k; json.dump(d,open(p1,'w',encoding='utf-8'),indent=2); json.dump(d,open(p2,'w',encoding='utf-8'),indent=2); print('[2/2] OpenCode config update ho gayi (hemomemo + freellmapi salamat)')"
set HEMOKEY_TMP=

echo.
echo  DONE. Ab OpenCode ko PURI TARAH band kar ke dobara khologo,
echo  phir /models me "Hemomemo AI (local)" -> hemomemo-core chunnon.
echo  Jawab aane me 30-60 second lag sakte hain (local dimagh soch raha hota hai).
pause
