# -*- coding: utf-8 -*-
"""_sound_check.py — PC-awaz ki asli-halat: default device + har-device vol/mute.
(pycaw sirf tashkhees/ilaaj ke liye — Hemomemo-app ki dependency NAHI)
--fix par: default device unmute + kam-vol utha-kar 50%."""
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from ctypes import cast, POINTER

import comtypes
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

CLSCTX = comtypes.CLSCTX_ALL
E_RENDER = 0       # eDataFlow.eRender (speaker/headphone side)
STATE_ACTIVE = 1   # DEVICE_STATE_ACTIVE


def endpoint_volume(immd):
    """IMMDevice -> IAudioEndpointVolume (asli-COM device se, wrapper se nahi)."""
    iface = immd.Activate(IAudioEndpointVolume._iid_, CLSCTX, None)
    return cast(iface, POINTER(IAudioEndpointVolume))


def get_enumerator():
    try:
        return AudioUtilities.GetDeviceEnumerator()
    except Exception:
        from pycaw.api.mmdeviceapi import CLSID_MMDeviceEnumerator, IMMDeviceEnumerator
        return comtypes.CoCreateInstance(CLSID_MMDeviceEnumerator, IMMDeviceEnumerator, CLSCTX)


def main():
    fix = "--fix" in sys.argv
    default_id = ""

    # 1) DEFAULT render device (awaz yahan ja-rahi hai)
    try:
        default_dev = AudioUtilities.GetSpeakers()
        default_id = default_dev._dev.GetId()
        dvol = endpoint_volume(default_dev._dev)
        print("DEFAULT-RENDER:", default_dev.FriendlyName)
        print("  vol %.0f%% | mute %s" % (
            dvol.GetMasterVolumeLevelScalar() * 100, bool(dvol.GetMute())))
    except Exception as e:
        print("default-check FAIL:", e)

    # 2) SARE active render devices ki halat
    try:
        coll = get_enumerator().EnumAudioEndpoints(E_RENDER, STATE_ACTIVE)
        n = coll.GetCount()
        print("== ACTIVE render devices:", n, "==")
        for i in range(n):
            dev = coll.Item(i)
            try:
                name = AudioUtilities.CreateDevice(dev).FriendlyName
            except Exception:
                name = dev.GetId()
            tag = "  <== DEFAULT" if dev.GetId() == default_id else ""
            try:
                vol = endpoint_volume(dev)
                print("  %-52s vol %3.0f%% | mute %-5s%s" % (
                    name[:52], vol.GetMasterVolumeLevelScalar() * 100,
                    bool(vol.GetMute()), tag))
            except Exception as e:
                print("  %-52s vol-check FAIL %s%s" % (name[:52], e, tag))
    except Exception as e:
        print("enumerate FAIL:", e)

    # 3) FIX (sirf --fix par): default unmute + kam-vol utha-kar 50%
    if fix:
        try:
            default_dev = AudioUtilities.GetSpeakers()
            vol = endpoint_volume(default_dev._dev)
            changed = []
            if bool(vol.GetMute()):
                vol.SetMute(0, None)
                changed.append("UNMUTE")
            v = vol.GetMasterVolumeLevelScalar()
            if v < 0.15:
                vol.SetMasterVolumeLevelScalar(0.5, None)
                changed.append("VOL %.0f%% -> 50%%" % (v * 100))
            print("FIX on", default_dev.FriendlyName, "->",
                  ", ".join(changed) if changed else "kuch-nahi (pehle-se-theek)")
        except Exception as e:
            print("FIX FAIL:", e)


main()
