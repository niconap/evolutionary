"""Phase-1 EA for EC Assignment 2 (ARIEL): evolve NN-controller weights.

Body and world are read from configuration (see `components.py` for the
factories); the EA loop itself has no knowledge of `spider_12` or
`CraterTerrainWorld` and works with a flat NumPy genotype vector.

Fitness convention: LOWER IS BETTER (distance to target), matching
`A2_template_2026.py`. "Best" always means "lowest fitness" below.

Usage
-----
    python a2_experiment.py --config config.yaml --seed 0
"""

from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from components import create_random_genotype, evaluate_genotype, inspect_dimensions

SCRIPT_DIR = Path(__file__).resolve().parent


# ============================================================================ #
#  CONFIG
# ============================================================================ #


def load_config(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return yaml.safe_load(f)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase-1 EA experiment runner.")
    parser.add_argument("--config", type=Path, default=SCRIPT_DIR / "config.yaml")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--population-size", type=int, default=None)
    parser.add_argument("--generations", type=int, default=None)
    parser.add_argument("--mutation-probability", type=float, default=None)
    parser.add_argument("--mutation-sigma", type=float, default=None)
    parser.add_argument(
        "--run-name",
        type=str,
        default="base",
        help="Name of the results subdirectory: results/<run-name>_seed_<seed>/",
    )
    return parser.parse_args()


def apply_overrides(cfg: dict[str, Any], args: argparse.Namespace) -> dict[str, Any]:
    """Command-line arguments override values loaded from the config file."""
    if args.seed is not None:
        cfg["seed"] = args.seed
    if args.population_size is not None:
        cfg["population_size"] = args.population_size
    if args.generations is not None:
        cfg["generations"] = args.generations
    if args.mutation_probability is not None:
        cfg["mutation"]["probability"] = args.mutation_probability
    if args.mutation_sigma is not None:
        cfg["mutation"]["sigma"] = args.mutation_sigma
    return cfg


# ============================================================================ #
#  REPRODUCIBILITY
# ============================================================================ #


def seed_everything(seed: int) -> np.random.Generator:
    random.seed(seed)
    return np.random.default_rng(seed)


# ============================================================================ #
#  EA OPERATORS (independent from body/world construction)
# ============================================================================ #


def mutate_gaussian(
    genotype: np.ndarray,
    rng: np.random.Generator,
    probability: float,
    sigma: float,
) -> np.ndarray:
    """Per-gene Gaussian perturbation, applied with the given probability."""
    child = genotype.copy()
    mask = rng.random(child.shape) < probability
    noise = rng.normal(scale=sigma, size=child.shape)
    child[mask] += noise[mask]
    return child


def evaluate_population(
    population: list[np.ndarray],
    cfg: dict[str, Any],
) -> list[float]:
    return [evaluate_genotype(genotype, cfg) for genotype in population]


def make_offspring(
    parents: list[np.ndarray],
    num_offspring: int,
    rng: np.random.Generator,
    mutation_cfg: dict[str, Any],
) -> list[np.ndarray]:
    """Clone parents (cycling as needed) and apply Gaussian mutation."""
    offspring = []
    for i in range(num_offspring):
        parent = parents[i % len(parents)]
        child = mutate_gaussian(
            parent,
            rng,
            probability=mutation_cfg["probability"],
            sigma=mutation_cfg["sigma"],
        )
        offspring.append(child)
    return offspring


# ============================================================================ #
#  RESULTS DIRECTORY
# ============================================================================ #


def make_results_dir(cfg: dict[str, Any], run_name: str) -> Path:
    results_dir = SCRIPT_DIR / "results" / f"{run_name}_seed_{cfg['seed']}"
    if results_dir.exists():
        msg = (
            f"Results directory already exists: {results_dir}\n"
            "Refusing to overwrite an existing experiment. Use a different "
            "--seed/--run-name or remove the old directory."
        )
        raise FileExistsError(msg)
    results_dir.mkdir(parents=True)
    return results_dir


# ============================================================================ #
#  MAIN EA LOOP
# ============================================================================ #


def main() -> None:
    args = parse_args()
    cfg = load_config(args.config)
    cfg = apply_overrides(cfg, args)

    rng = seed_everything(cfg["seed"])

    results_dir = make_results_dir(cfg, args.run_name)

    # Discover network dimensions from the actual compiled model (never hardcoded).
    input_size, hidden_size, output_size = inspect_dimensions(cfg)
    cfg["network"]["input_size"] = input_size
    cfg["network"]["output_size"] = output_size
    print(f"controller inputs  (len(data.qpos)) : {input_size}")
    print(f"controller outputs (model.nu)       : {output_size}")

    pop_size = cfg["population_size"]
    num_generations = cfg["generations"]
    fraction = cfg["parent_selection"]["fraction"]
    num_parents = max(1, round(pop_size * fraction))

    # --- Initial population --------------------------------------------- #
    population = [
        create_random_genotype(
            rng,
            input_size,
            hidden_size,
            output_size,
            scale=cfg["network"]["init_scale"],
        )
        for _ in range(pop_size)
    ]
    fitnesses = evaluate_population(population, cfg)
    evaluations = len(population)

    generation_rows = []
    best_overall_genotype = None
    best_overall_fitness = float("inf")

    def record_generation(gen: int) -> None:
        nonlocal best_overall_genotype, best_overall_fitness
        best_idx = int(np.argmin(fitnesses))
        if fitnesses[best_idx] < best_overall_fitness:
            best_overall_fitness = fitnesses[best_idx]
            best_overall_genotype = population[best_idx].copy()
        generation_rows.append(
            {
                "generation": gen,
                "evaluations": evaluations,
                "best_fitness": float(np.min(fitnesses)),
                "mean_fitness": float(np.mean(fitnesses)),
                "std_fitness": float(np.std(fitnesses)),
            }
        )
        print(
            f"gen {gen:3d} | evals {evaluations:4d} | "
            f"best {min(fitnesses):.4f} | mean {np.mean(fitnesses):.4f} | "
            f"std {np.std(fitnesses):.4f}"
        )

    # Generation 0 = the initial population, before any evolution.
    record_generation(0)

    for gen in range(1, num_generations + 1):
        # Rank parents+population by fitness ascending (lower is better).
        order = np.argsort(fitnesses)
        parent_indices = order[:num_parents]
        parents = [population[i] for i in parent_indices]

        # Crossover disabled (Phase 1): offspring are mutated clones of parents.
        offspring = make_offspring(
            parents,
            num_offspring=pop_size,
            rng=rng,
            mutation_cfg=cfg["mutation"],
        )
        offspring_fitnesses = evaluate_population(offspring, cfg)
        evaluations += len(offspring)

        # Elitist survivor selection from parents + offspring.
        combined = parents + offspring
        combined_fitnesses = [fitnesses[i] for i in parent_indices] + offspring_fitnesses
        survivor_order = np.argsort(combined_fitnesses)[:pop_size]
        population = [combined[i] for i in survivor_order]
        fitnesses = [combined_fitnesses[i] for i in survivor_order]

        record_generation(gen)

    # --- Save outputs ----------------------------------------------------- #
    with (results_dir / "config.yaml").open("w") as f:
        yaml.safe_dump(cfg, f, sort_keys=False)

    import csv

    with (results_dir / "generations.csv").open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["generation", "evaluations", "best_fitness", "mean_fitness", "std_fitness"],
        )
        writer.writeheader()
        writer.writerows(generation_rows)

    np.save(results_dir / "best_weights.npy", best_overall_genotype)

    print(f"best overall fitness: {best_overall_fitness:.4f}")
    print(f"results written to: {results_dir}")


if __name__ == "__main__":
    main()
