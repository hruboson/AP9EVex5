import math
import os
import random
from enum import Enum

import matplotlib.pyplot as plt


class Strategy(str, Enum):
    ALL_TO_ONE = "all to one"
    ALL_TO_RANDOM = "all to random"
    ALL_TO_ALL = "all to all"


STRATEGY = Strategy.ALL_TO_ONE
PATH_LENGTH = 1.7
STEP = 0.27
SEED = 42

RUNS_NO = 10
POPULATION_SIZE = 50
EVALS_PER_DIM = 1000
DIMENSIONS = (10, 30)


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

    def in_bounds(self, bounds: tuple[float, float]) -> bool:
        low, high = bounds
        return all(low <= v <= high for v in self.position)

    def update_personal_best(self) -> None:
        if self.fitness < self.best_fitness:
            self.best_fitness = self.fitness
            self.best_position = self.position[:]

    def move(
        self,
        strategy: Strategy,
        global_best_position: list[float],
        path_length: float,
        step_length: float,
    ) -> None:
        if strategy == Strategy.ALL_TO_ONE:
            pass
        elif strategy == Strategy.ALL_TO_RANDOM:
            pass
        elif strategy == Strategy.ALL_TO_ALL:
            pass

        # clamp
        self.position = [max(self.low, min(self.high, p)) for p in self.position]
        pass


class Swarm:
    def __init__(
        self,
        particles: list[Particle],
        strategy: Strategy,
        path_length: float,
        step_length: float,
        bounds: tuple[float, float],
        objective,
    ):
        self.particles = particles
        self.strategy = strategy
        self.path_length = path_length
        self.step_length = step_length
        self.bounds = bounds

    def global_best(self) -> Particle:
        return min(self.particles, key=lambda p: p.best_fitness)

    def step(self) -> None:
        """
        Perform one evolution step for the entire swarm.
        """
        if self.strategy == Strategy.ALL_TO_ONE:
            gb = self.global_best()
            for particle in self.particles:
                particle.move(
                    self.strategy, gb.best_position, self.path_length, self.step_length
                )
                particle.fitness = OBJECTIVES["Sphere"][0](
                    particle.position
                )  # Example objective
                particle.update_personal_best()

        elif self.strategy == Strategy.ALL_TO_RANDOM:
            all_best_positions = [p.best_position for p in self.particles]
            for particle in self.particles:
                # todo remove itself so it cant go to itself
                target = random.choice(all_best_positions)
                particle.move(self.strategy, target, self.path_length, self.step_length)
                particle.fitness = OBJECTIVES["Sphere"][0](particle.position)
                particle.update_personal_best()

        elif self.strategy == Strategy.ALL_TO_ALL:
            # TODO
            pass


def run_soma(
    objective, bounds: tuple[float, float], dimension: int, max_evals: int
) -> list[float]:
    """
    Run SOMA optimization for a single objective function.
    """
    num_particles = 30
    path_length = PATH_LENGTH
    step_length = STEP

    # Initialize particles
    particles = [Particle(dimension, bounds) for _ in range(num_particles)]
    swarm = Swarm(
        particles, STRATEGY, path_length, step_length, bounds, objective.__name__
    )

    # Evaluate initial fitness
    for p in particles:
        p.fitness = objective(p.position)
        p.update_personal_best()

    convergence_history = []
    max_iterations = max_evals // (num_particles * 2)  # Approximate iteration count
    if max_iterations < 1:
        max_iterations = 1

    for _ in range(max_iterations):
        swarm.step()
        gb = swarm.global_best()
        convergence_history.append(gb.best_fitness)

    return convergence_history


def run_experiment(
    objective_names: list[str] | None = None,
    num_particles: int = 30,
    dimension: int = 10,
    runs: int = RUNS_NO,
):
    """
    Run the SOMA experiment for multiple objective functions, dimensions, and strategies.
    Returns a nested dictionary: {objective: {dimension: {strategy: {run: [convergence_history]}}}}
    """
    if objective_names is None:
        objective_names = list(OBJECTIVES.keys())

    results: dict[str, dict[int, dict[str, list[list[float]]]]] = {}

    for strategy in Strategy:
        global STRATEGY
        STRATEGY = strategy

        for obj_name in objective_names:
            obj_func, bounds = OBJECTIVES[obj_name]

            if obj_name not in results:
                results[obj_name] = {}

            for dim in DIMENSIONS:
                if dim not in results[obj_name]:
                    results[obj_name][dim] = {}

                if strategy.value not in results[obj_name][dim]:
                    results[obj_name][dim][strategy.value] = []

                for _ in range(runs):
                    max_evals = EVALS_PER_DIM * dim
                    convergence_history = run_soma(obj_func, bounds, dim, max_evals)
                    results[obj_name][dim][strategy.value].append(convergence_history)

    return results


def plot_results(results: dict, save_dir: str) -> None:
    """
    Plot the convergence history for all objectives, averaged over runs.
    """
    os.makedirs(save_dir, exist_ok=True)

    plt.figure(figsize=(12, 7))

    for obj_name, dims_data in results.items():
        plt.figure(figsize=(12, 7))

        for dim, strategies_data in dims_data.items():
            for strategy, runs_data in strategies_data.items():
                # Average convergence across runs
                avg_history = [
                    sum(run[i] for run in runs_data if i < len(run)) / len(runs_data)
                    for i in range(max(len(run) for run in runs_data))
                ]
                label = f"{obj_name} dim={dim} {strategy}"
                plt.plot(
                    avg_history,
                    label=label,
                    linestyle="--" if dim != min(dims_data.keys()) else "-",
                )

        plt.title(f"Convergence: {obj_name}")
        plt.xlabel("Iteration")
        plt.ylabel("Best Fitness")
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


def main():
    results = run_experiment(objective_names=list(OBJECTIVES.keys()))
    plot_results(results, "./doc")


if __name__ == "__main__":
    main()
