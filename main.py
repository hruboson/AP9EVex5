import math
import os
import random
import statistics
import warnings
from enum import Enum
from typing import Callable

import matplotlib.pyplot as plt


class Strategy(str, Enum):
    ALL_TO_ONE = "all to one"
    ALL_TO_RANDOM = "all to random"
    ALL_TO_ALL = "all to all"


PATH_LENGTH = 1.7  # > 1 so we also search beyond the target
STEP = 0.27  # fraction of the path between two evaluations (should not divide 1)
PRT = 0.3  # probability that a dimension follows the trajectory
SEED = 42

RUNS_NO = 10
POPULATION_SIZE = 50
EVALS_PER_DIM = 1000
DIMENSIONS = (10, 30)
LOG_EVERY = POPULATION_SIZE  # store best-so-far every N evaluations


class BudgetExhausted(Exception):
    """Raised when the maximum number of function evaluations is reached."""


# objective functions (minimization), each with its search range (lower, upper)
def sphere(x: list[float]) -> float:
    return sum(v * v for v in x)


def rastrigin(x: list[float]) -> float:
    return 10 * len(x) + sum(v * v - 10 * math.cos(2 * math.pi * v) for v in x)


def rosenbrock(x: list[float]) -> float:
    return sum(
        100 * (x[i + 1] - x[i] ** 2) ** 2 + (1 - x[i]) ** 2 for i in range(len(x) - 1)
    )


def ackley(x: list[float]) -> float:
    d = len(x)
    s1 = sum(v * v for v in x) / d
    s2 = sum(math.cos(2 * math.pi * v) for v in x) / d
    return -20 * math.exp(-0.2 * math.sqrt(s1)) - math.exp(s2) + 20 + math.e


OBJECTIVES = {
    "Sphere": (sphere, (-5.12, 5.12)),
    "Rastrigin": (rastrigin, (-5.12, 5.12)),
    "Rosenbrock": (rosenbrock, (-5.0, 10.0)),
    "Ackley": (ackley, (-32.768, 32.768)),
}


class Particle:
    def __init__(self, dimension: int, bounds: tuple[float, float]) -> None:
        self.low, self.high = bounds
        self.position = [random.uniform(self.low, self.high) for _ in range(dimension)]
        self.fitness = math.inf  # fitness of the current position
        self.best_position = self.position[:]  # personal best
        self.best_fitness = math.inf
        self.velocity = [0.0] * dimension

    @staticmethod
    def _prt_vector(dimension: int, prt: float) -> list[int]:
        """1 = dimension follows the trajectory, 0 = it stays. At least one 1."""
        while True:
            vec = [1 if random.random() < prt else 0 for _ in range(dimension)]
            if any(vec):
                return vec

    def in_bounds(self, candidate: list[float]) -> bool:
        return all(self.low <= v <= self.high for v in candidate)

    def update_personal_best(self) -> None:
        if self.fitness < self.best_fitness:
            self.best_fitness = self.fitness
            self.best_position = self.position[:]

    def explore(
        self,
        target: list[float],
        path_length: float,
        step_length: float,
        prt: float,
        evaluate: Callable[[list[float]], float],
    ) -> tuple[list[float] | None, float]:
        """
        Walk from the current position towards `target` (and beyond, up to
        `path_length`) in steps of `step_length` (both relative to the distance
        to the target). Every in-bounds point is evaluated.
        Returns the best point found that improves on the current fitness
        (None if there is none) together with its fitness.
        The particle itself is not moved.
        """
        prt_vector = self._prt_vector(len(self.position), prt)
        n_steps = int(path_length / step_length + 1e-9)

        best_pos: list[float] | None = None
        best_fit = self.fitness

        for k in range(1, n_steps + 1):
            t = k * step_length
            candidate = [
                s + (g - s) * t * m
                for s, g, m in zip(self.position, target, prt_vector)
            ]
            if not self.in_bounds(candidate):  # never evaluate outside bounds
                continue
            fit = evaluate(candidate)
            if fit < best_fit:
                best_fit, best_pos = fit, candidate

        return best_pos, best_fit

    def move(self, new_position: list[float], new_fitness: float) -> None:
        self.position = new_position
        self.fitness = new_fitness
        self.update_personal_best()


class Swarm:
    def __init__(
        self,
        particles: list[Particle],
        strategy: Strategy,
        path_length: float,
        step_length: float,
        prt: float,
        bounds: tuple[float, float],
        objective: Callable[[list[float]], float],
        max_evals: int,
    ):
        self.particles = particles
        self.strategy = strategy
        self.path_length = path_length
        self.step_length = step_length
        self.prt = prt
        self.bounds = bounds
        self.objective = objective
        self.max_evals = max_evals

        self.evals = 0
        self.best_so_far = math.inf
        self.history: list[float] = []  # best-so-far every LOG_EVERY evaluations

    def global_best(self) -> Particle:
        return min(self.particles, key=lambda p: p.best_fitness)

    def initialize(self) -> None:
        for p in self.particles:
            p.fitness = self.evaluate(p.position)
            p.update_personal_best()

    def evaluate(self, position: list[float]) -> float:
        """Counted objective evaluation; enforces the evaluation budget."""
        if self.evals >= self.max_evals:
            raise BudgetExhausted
        self.evals += 1
        fit = self.objective(position)
        if fit < self.best_so_far:
            self.best_so_far = fit
        if self.evals % LOG_EVERY == 0:
            self.history.append(self.best_so_far)
        return fit

    def _migrate(self, p: Particle, target: list[float]) -> None:
        new_pos, new_fit = p.explore(
            target, self.path_length, self.step_length, self.prt, self.evaluate
        )
        if new_pos is not None:
            p.move(new_pos, new_fit)

    def step(self) -> None:
        if self.strategy == Strategy.ALL_TO_ONE:
            leader = self.global_best()
            target = leader.best_position
            for particle in self.particles:
                if particle is leader:
                    continue
                self._migrate(particle, target)

        elif self.strategy == Strategy.ALL_TO_RANDOM:
            snapshot = [p.best_position for p in self.particles]
            n = len(self.particles)
            for i, particle in enumerate(self.particles):
                j = random.randrange(n - 1)  # random index that is not i
                if j >= i:
                    j += 1
                self._migrate(particle, snapshot[j])

        elif self.strategy == Strategy.ALL_TO_ALL:
            # every particle explores the paths to all the others,
            # then jumps to the best point it found among all of them
            snapshot = [p.best_position for p in self.particles]
            for i, particle in enumerate(self.particles):
                best_pos: list[float] | None = None
                best_fit = particle.fitness
                for j, target in enumerate(snapshot):
                    if j == i:
                        continue
                    pos, fit = particle.explore(
                        target,
                        self.path_length,
                        self.step_length,
                        self.prt,
                        self.evaluate,
                    )
                    if pos is not None and fit < best_fit:
                        best_pos, best_fit = pos, fit
                if best_pos is not None:
                    particle.move(best_pos, best_fit)


def run_soma(
    objective,
    bounds: tuple[float, float],
    dimension: int,
    max_evals: int,
    strategy: Strategy,
) -> list[float]:
    """
    Run SOMA for a single objective function with a fixed evaluation budget.
    Returns best-so-far fitness sampled every LOG_EVERY evaluations.
    """
    particles = [Particle(dimension, bounds) for _ in range(POPULATION_SIZE)]
    swarm = Swarm(
        particles,
        strategy,
        PATH_LENGTH,
        STEP,
        PRT,
        bounds,
        objective,
        max_evals,
    )

    try:
        swarm.initialize()
        while True:
            swarm.step()
    except BudgetExhausted:
        pass

    return swarm.history


def run_experiment(
    objective_names: list[str] | None = None,
    runs: int = RUNS_NO,
):
    """
    Returns {objective: {dimension: {strategy: [convergence_history per run]}}}
    """
    if objective_names is None:
        objective_names = list(OBJECTIVES.keys())

    if abs(1 / STEP - round(1 / STEP)) < 1e-9:
        warnings.warn("STEP divides 1 exactly - particles will hit evaluated points")

    results: dict[str, dict[int, dict[str, list[list[float]]]]] = {}

    for obj_name in objective_names:
        obj_func, bounds = OBJECTIVES[obj_name]
        results[obj_name] = {}

        for dim in DIMENSIONS:
            results[obj_name][dim] = {}
            max_evals = EVALS_PER_DIM * dim

            for strategy in Strategy:
                results[obj_name][dim][strategy.value] = [
                    run_soma(obj_func, bounds, dim, max_evals, strategy)
                    for _ in range(runs)
                ]
                print(f"done: {obj_name} dim={dim} {strategy.value}")

    return results


def plot_results(results: dict, save_dir: str) -> None:
    """
    Plot the convergence history (averaged over runs) for each objective.
    """
    os.makedirs(save_dir, exist_ok=True)

    for obj_name, dims_data in results.items():
        plt.figure(figsize=(12, 7))

        for dim, strategies_data in dims_data.items():
            for strategy, runs_data in strategies_data.items():
                length = min(len(run) for run in runs_data)
                avg_history = [
                    sum(run[i] for run in runs_data) / len(runs_data)
                    for i in range(length)
                ]
                evals = [(i + 1) * LOG_EVERY for i in range(length)]
                plt.plot(
                    evals,
                    avg_history,
                    label=f"dim={dim} {strategy}",
                    linestyle="--" if dim != min(dims_data.keys()) else "-",
                )

        plt.title(f"Convergence: {obj_name}")
        plt.xlabel("Function evaluations")
        plt.ylabel("Best fitness (avg over runs)")
        plt.yscale("log")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()

        filename = os.path.join(
            save_dir,
            f"{obj_name}_dims{'_'.join(str(d) for d in sorted(dims_data.keys()))}.png",
        )
        plt.savefig(filename, dpi=150)
        plt.close()

    print(f"Plots saved to {save_dir}")


def make_tables(results: dict, save_path: str | None = None) -> str:
    lines: list[str] = []

    for obj_name, dims_data in results.items():
        for dim, strategies_data in dims_data.items():
            lines.append(f"##### {obj_name}, d={dim}")
            lines.append("")
            lines.append("| Method | Best | Worst | Mean | Median | Std |")
            lines.append("|---|---:|---:|---:|---:|---:|")

            for strategy, runs_data in strategies_data.items():
                finals = [run[-1] for run in runs_data]
                row = [
                    min(finals),
                    max(finals),
                    statistics.mean(finals),
                    statistics.median(finals),
                    statistics.pstdev(finals),
                ]
                cells = " | ".join(f"{v:.4g}" for v in row)
                lines.append(f"| {strategy.capitalize()} | {cells} |")

            lines.append("")

    table_md = "\n".join(lines)
    print(table_md)

    if save_path is not None:
        os.makedirs(os.path.dirname(save_path) or ".", exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            f.write(table_md)
        print(f"Tables saved to {save_path}")

    return table_md


def main():
    random.seed(SEED)
    results = run_experiment(objective_names=list(OBJECTIVES.keys()))
    plot_results(results, "./doc")
    make_tables(results, "./doc/results.md")


if __name__ == "__main__":
    main()
