# -*- coding: utf-8 -*-
"""_sound_sessions.py — per-app (volume-mixer) mute/vol check on DEFAULT device.
--fix: muted-apps unmute (+0-vol -> 50%). End me test-beep (sunai-den test)."""
import sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from pycaw.pycaw import AudioUtilities

fix = "--fix" in sys.argv
print("== APP-SESSIONS (volume-mixer) on default device ==")
for s in AudioUtilities.GetAllSessions():
    name = "?"
    try:
        if s.Process is not None:
            name = s.Process.name()
    except Exception:
        pass
    sys_snd = False
    try:
        sys_snd = s.isSystemSoundsSession()
    except Exception:
        pass
    try:
        v = s.SimpleAudioVolume.GetMasterVolume()
        m = bool(s.SimpleAudioVolume.GetMute())
        print("  %-28s pid=%-7s vol %3.0f%% | mute %-5s%s" % (
            name[:28], s.ProcessId, v * 100, m,
            " (system-sounds)" if sys_snd else ""))
        if fix and m:
            s.SimpleAudioVolume.SetMute(False, None)
            print("    -> UNMUTE kiya")
        if fix and v < 0.05 and not sys_snd:
            s.SimpleAudioVolume.SetMasterVolume(0.5, None)
            print("    -> VOL 0%% -> 50%% kiya")
    except Exception as e:
        print("  ", name, "check FAIL:", e)

print("== TEST-BEEP (default device par, 2 baar) ==")
import winsound
winsound.Beep(660, 500)
winsound.Beep(880, 500)
print("BEEP-DONE")
