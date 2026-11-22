"""
🧬 genetic.py — EVOLUTION ENGINE

Brain ke synaptic weights = DNA (vector of 2.5M genes, sampled).
Genetic algorithm: population of brains -> evaluate fitness -> selection,
crossover, mutation -> agla generation. Best brain disk me save hota hai.

Fitness tasks (aap choose kar sakte ho):
  - "spot": spot dekho -> 'grab' action expected
  - "tone": sound suno -> 'listen' action expected
  - "press": touch -> 'approach' expected
"""
import numpy as np
import time

from brain.brain import DigitalBrain


class EvolutionEngine:
    def __init__(self, pop_size: int = 8, mutation_rate: float = 0.05,
                 mutation_scale: float = 0.10, elites: int = 2):
        self.pop_size = pop_size
        self.mut_rate = mutation_rate
        self.mut_scale = mutation_scale
        self.elites = elites
        self.generation = 0
        self.history: list[float] = []

    # ------------------------------------------------------------------
    def make_genotype(self) -> np.ndarray:
        """Ek brain ka compact DNA (sampled weights)."""
        brain = DigitalBrain()
        dna = brain.synapses.weights[::97, ::37].reshape(-1).copy()  # downsample
        return dna

    def apply_genotype(self, brain: DigitalBrain, dna: np.ndarray):
        """DNA vector ko brain ke poore weight-matrix par map karo."""
        h, w = brain.synapses.weights.shape
        brain.synapses.weights = np.resize(dna, (h, w)).astype(np.float32)
        np.clip(brain.synapses.weights, -2.0, 2.0, out=brain.synapses.weights)

    # ------------------------------------------------------------------
    def fitness(self, brain: DigitalBrain, tasks: list[str], steps_per_task: int = 20) -> float:
        """Brain ko 3 chhote tasks do, reward = correct action ratio."""
        score = 0.0
        cases = {
            "vision": ("spot", "approach"),
            "sound": ("tone", "listen"),
            "touch": ("press", "withdraw"),
        }
        for task in tasks:
            stim, expect = cases.get(task, (None, None))
            if stim is None:
                continue
            if stim == "spot":
                brain.senses.vision.draw_spot(12, 12)
            elif stim == "tone":
                brain.senses.sound.hear_tone(3)
            elif stim == "press":
                brain.senses.touch.press(6, 6)
            action, conf = brain.step(steps_per_task)
            if action == expect:
                score += 1.0 + conf
            else:
                score += conf * 0.3
            # clear
            brain.senses.vision.clear(); brain.senses.sound.clear(); brain.senses.touch.clear()
        return score

    # ------------------------------------------------------------------
    def crossover(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        mask = np.random.random(a.shape) < 0.5
        return np.where(mask, a, b)

    def mutate(self, dna: np.ndarray) -> np.ndarray:
        d = dna.copy()
        m = np.random.random(d.shape) < self.mut_rate
        d[m] += np.random.normal(0, self.mut_scale, m.sum())
        return np.clip(d, -2.0, 2.0)

    # ------------------------------------------------------------------
    def evolve_gens(self, n_gens: int, tasks=("vision", "sound", "touch"),
                    verbose=True, save_best_path=None):
        """Main loop: population banao, evaluate, evolve."""
        population = [self.make_genotype() for _ in range(self.pop_size)]

        best_dna, best_fit = None, -1e9
        for g in range(n_gens):
            self.generation += 1
            fits = []
            t0 = time.time()
            for dna in population:
                brain = DigitalBrain()
                self.apply_genotype(brain, dna)
                fits.append(self.fitness(brain, list(tasks)))
            order = np.argsort(fits)[::-1]
            gen_best = fits[order[0]]
            avg = float(np.mean(fits))
            self.history.append(avg)
            if verbose:
                print(f"🧬 Gen {self.generation:3d} | best {gen_best:.3f} "
                      f"| avg {avg:.3f} | {time.time()-t0:.1f}s")
            if gen_best > best_fit:
                best_fit, best_dna = gen_best, population[order[0]].copy()
                if save_best_path and best_dna is not None:
                    np.savez(save_best_path, dna=best_dna, generation=self.generation,
                             fitness=best_fit)

            # selection
            elite_idx = order[: self.elites]
            alive = [population[i] for i in order[self.elites:]]
            new_pop = [population[i] for i in elite_idx]
            pool = fits[:]
            while len(new_pop) < self.pop_size:
                a = population[min(np.random.randint(0, len(population)), self.pop_size - 1)]
                b = population[min(np.random.randint(0, len(population)), self.pop_size - 1)]
                child = self.mutate(self.crossover(a, b))
                new_pop.append(child)
            population = new_pop[: self.pop_size]

        # restore best into a fresh brain
        best_brain = DigitalBrain()
        if best_dna is not None:
            self.apply_genotype(best_brain, best_dna)
        return best_brain, best_fit


if __name__ == "__main__":
    eng = EvolutionEngine(pop_size=4)
    eng.evolve_gens(2)
