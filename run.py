r"""
🧠 run.py — DIGITAL BRAIN MAIN MENU

D:\DigitalBrain ka entry-point. Choose karo:
  1) Hemomemo AI Chat — FULL SYSTEM (brain+brain2+heart+autonomous+research)
  2) Live Brain Simulation  (2,000,000 neurons + 1,600,000 glia + senses + decisions)
  3) Evolve Brain           (genetic algorithm se DNA improve)
  4) Quick Test             (chhota sanity run)
  5) Load & Watch           (saved brain state dekho)
"""
import os
import sys

# Windows console (cp1252) me emoji/print safe karein
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
sys.path.insert(0, HERE)

try:
    from brain.brain import DigitalBrain          # noqa: E402
    from brain.neurons import AREAS               # noqa: E402
    from evolution.genetic import EvolutionEngine # noqa: E402
    from core.state import save_brain, load_brain # noqa: E402
    _BRAIN_OK = True
except Exception as _e:  # numpy nahi installed → chat/menu phir bhi chale
    _BRAIN_OK = False
    _BRAIN_ERR = str(_e)
from core.owner import summary as owner_summary  # noqa: E402


def _brain_missing():
    print(" ⚠️  Brain module load nahi hua: " + _BRAIN_ERR)
    print("    (numpy install karein: pip install numpy) — chat band option phir bhi available hai.")


def bar(n=48):
    return "=" * n


def show_stats(brain):
    st = brain.stats()
    print(f"   ⚙️  neurons {st['neurons']:,} | synapses {st['synapses']:,} | "
          f"spikes {st['total_spikes']:,} | grid {st['grid_phase']} | "
          f"action: {st['last_action']}")
    print("   ⚡ " + brain.visualize())
    print("   " + brain.sense_summary())


def live_menu():
    print(bar())
    print(" LIVE SIMULATION — brain senses + decisions")
    print("   Senses dena: text likho, spot/tone do, touch dabo")
    brain = DigitalBrain()

    # initial stimuli
    brain.senses.vision.draw_spot(12, 12)
    brain.senses.sound.hear_tone(3)
    text = input("   ⌨️  Brain ke liye text likho (Enter=skip): ").strip()
    if text:
        brain.senses.keyboard.feed_text(text)

    steps = 200
    for i in range(steps):
        brain.step()
        if i % 20 == 0:
            print(f"\n [t={brain.t}] {bar(20)}")
            show_stats(brain)
    lo, hi = AREAS["motor"]
    a, c = brain.motor.decode(brain.neurons.rate_smooth[lo:hi])
    print(f"\n 🪄 FINAL DECISION: {a}  (confidence {c:.2f})")
    p = save_brain(brain, "brain_live")
    print(f" 💾 Brain state saved: {p}")


def evolve_menu():
    print(bar())
    gens = input(" 🧬 Kitne generations? [3]: ").strip()
    gens = int(gens) if gens.isdigit() else 3
    eng = EvolutionEngine(pop_size=6, mutation_rate=0.06)
    best_brain, best_fit = eng.evolve_gens(
        n_gens=gens, save_best_path=os.path.join("core", "best_dna.npz"))
    print(f"\n 🏆 Best fitness: {best_fit:.3f}")
    a, c = best_brain.step(20)
    print(" 🪄 Best brain decision:", a, f"(conf {c:.2f})")


def quick_test():
    brain = DigitalBrain()
    brain.senses.vision.draw_spot(6, 6)
    brain.senses.sound.hear_tone(7)
    for _ in range(50):
        brain.step()
    st = brain.stats()
    print(bar())
    print(" QUICK TEST RESULTS")
    for k, v in st.items():
        print(f"   {k:12s} : {v}")
    print("   ⚡ " + brain.visualize())


def load_menu():
    brain = DigitalBrain()
    if load_brain(brain, "brain_live"):
        print(" ✅ Saved brain loaded. 20 steps chala raha hoon...")
        for _ in range(20):
            brain.step()
        show_stats(brain)
    else:
        print(" ❌ Pehle koi brain save nahi; live simulation chalao.")


def main():
    # 🔒 ULTRA-SECURITY: file integrity + Quran guard checks on boot
    try:
        from model.autonomous import verify_system_integrity
        ok, tampered = verify_system_integrity()
        if not ok:
            print("🛡️ ULTRA SECURITY ALERT: System files modified:", tampered)
            print("Unauthorized changes detected — Hemomemo AI band ho raha hai.")
            return
    except Exception:
        pass
    while True:
        print(bar())
        from brain.config import N_TOTAL, N_GLIA, FAN_OUT
        print(" 🧠  DIGITAL BRAIN — {:,} neurons + {:,} glial cells (fan {})".format(
            N_TOTAL, N_GLIA, FAN_OUT))
        print(" 🪪  Owner: " + owner_summary())
        print(bar())
        print(" 🔗 UNIFIED HEMOMO AI MASTER MENU")
        print(" 1) 🤖 Hemomemo AI Chat — FULL SYSTEM (brain+brain2+heart+autonomous+research)")
        print(" 2) 🧠 Live Brain Simulation   (brain senses + decides LIVE)")
        print(" 3) 🧬 Evolve Brain           (genetic algorithm se DNA improve)")
        print(" 4) 🧪 Quick Test             (fast 50-step sanity)")
        print(" 5) 📦 Load & Watch           (saved brain state dekho)")
        print(" 6) 📈 Train Brain More       (usko aur seekhaao)")
        print(" 7) 🌐 Browser Server         (local web chat — internet ki zaroorat nahi)")
        print(" 8) 💓 System Status         (hub: sab files ka deep connection)")
        print(" 0) 🚪 Exit")
        ch = input(" 👉 Choose [1-8, 0]: ").strip()
        try:
            if ch == "1":
                from model.generate import chat_loop
                chat_loop()
            elif ch in ("2", "3", "4", "5"):
                if not _BRAIN_OK:
                    _brain_missing()
                    continue
                if ch == "2":
                    live_menu()
                elif ch == "3":
                    evolve_menu()
                elif ch == "4":
                    quick_test()
                else:
                    load_menu()
            elif ch == "6":
                steps = input(" Kitne steps train karein? [500]: ").strip()
                steps = int(steps) if steps.isdigit() else 500
                from model.train import train
                train(steps=steps)
            elif ch == "7":
                from server.server import run_server
                run_server()
            elif ch == "8":
                from core.hub import status, heartbeat_check
                import pprint as _pp
                _pp.pprint(status())
                print(" heartbeat:", heartbeat_check()["ok"])
            elif ch == "0":
                print(" 👋 Brain band kar raha hoon. Phayla waqt fir milenge!")
                break
            else:
                print(" Galat choice — 1 se 8 ya 0 likho.")
        except KeyboardInterrupt:
            print("\n ⏹️  Stopped.")
        except Exception as e:
            print(f"\n ⚠️  Error: {e}\n")


if __name__ == "__main__":
    main()
