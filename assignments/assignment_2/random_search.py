"""Random-search baseline for Assignment 2.

The baseline uses the same genotype representation, simulator, population-sized
batches, and total evaluation budget as the evolutionary runner. It retains
only the best genotype found so far; each new candidate is sampled afresh.
"""

from __future__ import annotations

import argparse
import csv
import random
from concurrent.futures import ProcessPoolExecutor
from contextlib import nullcontext
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from components import create_random_genotype, evaluate_genotype, inspect_dimensions

SCRIPT_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Random-search baseline runner.")
    parser.add_argument("--config", type=Path, default=SCRIPT_DIR / "config.yaml")
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--population-size", type=int, default=None)
    parser.add_argument("--generations", type=int, default=None)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--run-name", type=str, default="random_search")
    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    with path.open() as file:
        return yaml.safe_load(file)


def make_results_dir(seed: int, run_name: str) -> Path:
    results_dir = SCRIPT_DIR / "results" / f"{run_name}_seed_{seed}"
    if results_dir.exists():
        raise FileExistsError(f"Results directory already exists: {results_dir}")
    results_dir.mkdir(parents=True)
    return results_dir


def evaluate_population(
    population: list[np.ndarray],
    cfg: dict[str, Any],
    executor: ProcessPoolExecutor | None,
) -> list[float]:
    if executor is not None:
        return list(executor.map(evaluate_genotype, population, [cfg] * len(population)))
    return [evaluate_genotype(genotype, cfg) for genotype in population]


def main() -> None:
    args = parse_args()
    if args.workers < 1:
        raise ValueError("--workers must be at least 1")

    cfg = load_config(args.config)
    if args.population_size is not None:
        cfg["population_size"] = args.population_size
    if args.generations is not None:
        cfg["generations"] = args.generations
    cfg["seed"] = args.seed

    random.seed(args.seed)
    rng = np.random.default_rng(args.seed)
    results_dir = make_results_dir(args.seed, args.run_name)

    input_size, hidden_size, output_size = inspect_dimensions(cfg)
    cfg["network"]["input_size"] = input_size
    cfg["network"]["output_size"] = output_size
    population_size = cfg["population_size"]
    generations = cfg["generations"]

    executor_context = ProcessPoolExecutor(max_workers=args.workers) if args.workers > 1 else nullcontext()
    with executor_context as executor:
        rows = []
        best_genotype = None
        best_fitness = float("inf")
        evaluations = 0

        for generation in range(generations + 1):
            population = [
                create_random_genotype(
                    rng,
                    input_size,
                    hidden_size,
                    output_size,
                    scale=cfg["network"]["init_scale"],
                )
                for _ in range(population_size)
            ]
            fitnesses = evaluate_population(population, cfg, executor)
            evaluations += len(population)
            batch_best = int(np.argmin(fitnesses))
            if fitnesses[batch_best] < best_fitness:
                best_fitness = fitnesses[batch_best]
                best_genotype = population[batch_best].copy()
            rows.append(
                {
                    "generation": generation,
                    "evaluations": evaluations,
                    "best_fitness": best_fitness,
                    "mean_fitness": float(np.mean(fitnesses)),
                    "std_fitness": float(np.std(fitnesses)),
                }
            )
            print(
                f"gen {generation:3d} | evals {evaluations:4d} | "
                f"best {best_fitness:.4f} | mean {np.mean(fitnesses):.4f} | "
                f"std {np.std(fitnesses):.4f}"
            )

    with (results_dir / "config.yaml").open("w") as file:
        yaml.safe_dump(cfg, file, sort_keys=False)
    with (results_dir / "generations.csv").open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["generation", "evaluations", "best_fitness", "mean_fitness", "std_fitness"],
        )
        writer.writeheader()
        writer.writerows(rows)
    np.save(results_dir / "best_weights.npy", best_genotype)
    print(f"best overall fitness: {best_fitness:.4f}")
    print(f"results written to: {results_dir}")


if __name__ == "__main__":
    main()