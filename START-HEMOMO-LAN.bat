@echo off
title Hemomemo AI - LAN Mode (OPT-IN)
echo.
echo  =====================================================
echo   HEMOMO - LAN MODE (OPT-IN) - kya ye hai
 echo  =====================================================
echo  Ye bat aap (owner) ke liye hai - sirf is PC par.
echo  Default Hemomemo API server HAMESHA 127.0.0.1 par
 echo  chalta hai (safety + law). LAN mode isi par OPT-OUT
 echo  hai: isse Hemomemo local API 0.0.0.0:8790 par chalega.
echo.
echo  "Door ka user" (kisi bhi dusre device se) is PC ki
 echo  Hemomemo API ko use kar sake - lekin sirf owner PC on
 echo  par, aur sirf opt-in par.
echo.
echo  Start kar raha hai: Hemomemo API server 0.0.0.0:8790 par...
 echo.
 py -3 -u -X utf8 "%~dp0server\hemomemo_server.py" start 8790 0.0.0.0
echo.
echo  DONE. API ab 0.0.0.0:8790 par hai - default 127.0.0.1 nahi.
pause
