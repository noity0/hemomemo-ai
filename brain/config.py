"""
🧮 config.py — BRAIN SCALE (poora system ek number se badalta hai)

Env vars (PowerShell, aur BHI bara):
  $env:HMHS_N_TOTAL  = '4000000'
  $env:HMHS_N_GLIA   = '3200000'
  $env:HMHS_FAN_OUT  = '50'

Formula har size par kaam karta hai (sensory 20%, association 40%,
motor 10%, core 30%). 20B (20,000,000,000) ke liye ~2TB+ RAM chahiye —
is PC me fit NAHI, lekin yeh code server-RAM par aise hi khul jayega.
"""
import os


def _int_env(name: str, default: int, lo: int = 1000) -> int:
    """Env/int padho — neeche `lo` par clamp. (Neuron-counts ke liye lo=1000;
    FAN_OUT jaisi chhoti values ke liye lo=1 pass karo warna 25 → 1000 ho jata!)"""
    try:
        return max(lo, int(os.environ.get(name, "") or default))
    except ValueError:
        return default


# --- core sizes (default = 2M tier; user-emaanat: 2,000,000 bio-neurons) ---
N_TOTAL = _int_env("HMHS_N_TOTAL", 2_000_000)
N_GLIA = _int_env("HMHS_N_GLIA", max(1000, int(N_TOTAL * 0.8)))
FAN_OUT = _int_env("HMHS_FAN_OUT", 25, lo=1)   # 2M × 25 = 50M synapses (~0.6GB RAM)

# --- derived areas (percentage-based — har size par barabar) ---
SENSIVE_N = max(1000, int(N_TOTAL * 0.20))       # sensory = 20%
PER_SENSE = max(250, SENSIVE_N // 4)             # 4 senses
MOTOR_N = max(1000, int(N_TOTAL * 0.10))         # motor = 10%


def areas():
    """Brain areas ka percentage-based map (kisi bhi N par sahi)."""
    s = SENSIVE_N
    assoc = int(N_TOTAL * 0.40)
    motor = MOTOR_N
    return {
        "sensory":     (0, s),                      # 20%
        "association": (s, s + assoc),              # 40% (thinking)
        "motor":       (s + assoc, s + assoc + motor),  # 10% (decisions)
        "core":        (s + assoc + motor, N_TOTAL),    # 30% (deep core)
    }


AREAS = areas()


def describe() -> str:
    return "neurons {:,} | glia {:,} | synapses {:,} | sensory {:,} | motor {:,}".format(
        N_TOTAL, N_GLIA, N_TOTAL * FAN_OUT, SENSIVE_N, MOTOR_N)
