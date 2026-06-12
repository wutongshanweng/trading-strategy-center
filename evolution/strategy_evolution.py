from typing import List, Dict, Any
import numpy as np
from backtest.vectorized_engine import VectorizedBacktest


class StrategyEvolution:
    def __init__(self, population_size: int = 50, mutation_rate: float = 0.1):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.history: List[float] = []

    def create_initial_population(self, param_ranges: Dict) -> List[Dict]:
        population = []
        for _ in range(self.population_size):
            individual = {}
            for key, (low, high) in param_ranges.items():
                if isinstance(low, int) and isinstance(high, int):
                    individual[key] = int(np.random.randint(low, high + 1))
                else:
                    individual[key] = float(np.random.uniform(low, high))
            population.append(individual)
        return population

    def _evaluate_fitness(self, df, strategy_cls, params: Dict) -> float:
        try:
            strategy = strategy_cls(**params)
            bt = VectorizedBacktest()
            result = bt.run(df, strategy)
            return result.sharpe_ratio if result.sharpe_ratio != 0 else -1.0
        except Exception:
            return -999.0

    def select(self, population: List[Dict], fitness_scores: List[float]) -> List[Dict]:
        paired = list(zip(population, fitness_scores))
        paired.sort(key=lambda x: x[1], reverse=True)
        n_keep = max(2, int(len(population) * 0.3))
        return [p[0] for p in paired[:n_keep]]

    def crossover(self, parent1: Dict, parent2: Dict) -> Dict:
        child = {}
        for key in parent1:
            if np.random.random() < 0.5:
                child[key] = parent1[key]
            else:
                child[key] = parent2[key]
        return child

    def mutate(self, individual: Dict, param_ranges: Dict) -> Dict:
        mutated = dict(individual)
        for key in mutated:
            if np.random.random() < self.mutation_rate:
                low, high = param_ranges[key]
                if isinstance(low, int) and isinstance(high, int):
                    mutated[key] = int(np.random.randint(low, high + 1))
                else:
                    mutated[key] = float(np.random.uniform(low, high))
        return mutated

    def evolve(self, df, strategy_cls, param_ranges: Dict, generations: int = 10) -> Dict[str, Any]:
        population = self.create_initial_population(param_ranges)
        best_params = None
        best_fitness = -999.0
        history = []

        for gen in range(generations):
            fitness = [self._evaluate_fitness(df, strategy_cls, ind) for ind in population]
            gen_best = max(fitness)
            gen_avg = np.mean(fitness)
            history.append({"generation": gen, "best": gen_best, "avg": gen_avg})

            if gen_best > best_fitness:
                best_fitness = gen_best
                best_params = population[fitness.index(gen_best)]

            selected = self.select(population, fitness)
            new_population = list(selected)

            while len(new_population) < self.population_size:
                p1, p2 = np.random.choice(len(selected), 2, replace=False)
                child = self.crossover(selected[p1], selected[p2])
                child = self.mutate(child, param_ranges)
                new_population.append(child)

            population = new_population[:self.population_size]

        return {"best_params": best_params, "best_fitness": best_fitness, "history": history}
