import math
import random
from enum import Enum


class Strategy(str, Enum):
    ALL_TO_ONE = "all to one"
    ALL_TO_RANDOM = "all to random"
    ALL_TO_ALL = "all to all"


STRATEGY = Strategy.ALL_TO_ONE
PATH_LENGTH = 1.7
STEP = 0.27
SEED = 42


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
        low, high = bounds
        self.position = [random.uniform(low, high) for _ in range(dimension)]
        self.fitness = math.inf  # fitness of the current position
        self.best_position = self.position[:]  # personal best
        self.best_fitness = math.inf

    def in_bounds(self, bounds: tuple[float, float]) -> bool:
        low, high = bounds
        return all(low <= v <= high for v in self.position)

    def update_personal_best(self) -> None:
        if self.fitness < self.best_fitness:
            self.best_fitness = self.fitness
            self.best_position = self.position[:]

    def move(self) -> None:
        # TODO
        pass

class Swarm:
    def __init__(self, particles, strategy, path_length, step):
        self.particles = particles
        self.strategy = strategy
        self.path_length = path_length
        self.step = step

    def global_best(self) -> Particle:
        return min(self.particles, key=lambda p: p.best_fitness)


def run_experiment():
    pass


def plot_results():
    pass


def main():
    pass


if __name__ == "__main__":
    main()
