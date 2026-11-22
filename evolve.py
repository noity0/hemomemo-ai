"""
🧬 evolve.py — Brain Ko Evolve Karo

Genetic algorithm se brain ki wiring (DNA) improve karo.
Generation loop ke results live print hote hain.
"""
from evolution.genetic import EvolutionEngine

if __name__ == "__main__":
    eng = EvolutionEngine(pop_size=6, mutation_rate=0.06)
    best_brain, best_fit = eng.evolve_gens(
        n_gens=5,
        tasks=("vision", "sound", "touch"),
        save_best_path="core/best_dna.npz",
    )
    print("\n🏆 Best fitness:", best_fit)
    a, c = best_brain.step(20)
    print("Best brain decision now:", a, f"(conf {c:.2f})")
