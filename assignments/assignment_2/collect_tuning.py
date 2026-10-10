"""Collect completed SLURM tuning runs and create ranking/heatmap outputs."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def values(text: str) -> list[float]:
    return [float(value) for value in text.split(",") if value.strip()]


def final_fitness(path: Path) -> float:
    with (path / "generations.csv").open(newline="") as file:
        rows = list(csv.DictReader(file))
    return float(rows[-1]["best_fitness"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--output-dir", type=Path, default=Path("results/slurm_tuning"))
    parser.add_argument("--parent-fractions", default="0.2,0.5,0.8")
    parser.add_argument("--mutation-sigmas", default="0.05,0.1,0.2")
    parser.add_argument("--seeds", default="0,1,2")
    args = parser.parse_args()

    fractions = values(args.parent_fractions)
    sigmas = values(args.mutation_sigmas)
    seeds = [int(value) for value in args.seeds.split(",") if value.strip()]
    rows = []
    for fraction in fractions:
        for sigma in sigmas:
            run_name = f"tune_fraction_{fraction:g}_sigma_{sigma:g}"
            for seed in seeds:
                path = args.results_dir / f"{run_name}_seed_{seed}"
                if not (path / "generations.csv").exists():
                    raise FileNotFoundError(f"Missing completed run: {path}")
                rows.append(
                    {
                        "parent_fraction": fraction,
                        "mutation_sigma": sigma,
                        "seed": seed,
                        "final_best_fitness": final_fitness(path),
                    }
                )

    grouped = {}
    for row in rows:
        grouped.setdefault((row["parent_fraction"], row["mutation_sigma"]), []).append(row["final_best_fitness"])
    ranked = sorted(
        [
            {
                "parent_fraction": fraction,
                "mutation_sigma": sigma,
                "mean_final_best": float(np.mean(fitnesses)),
                "std_final_best": float(np.std(fitnesses, ddof=1)) if len(fitnesses) > 1 else 0.0,
            }
            for (fraction, sigma), fitnesses in grouped.items()
        ],
        key=lambda row: row["mean_final_best"],
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    with (args.output_dir / "tuning_runs.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    with (args.output_dir / "tuning_summary.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(ranked[0]))
        writer.writeheader()
        writer.writerows(ranked)

    sigma_values = {}
    for row in rows:
        sigma_values.setdefault(row["mutation_sigma"], []).append(row["final_best_fitness"])
    shared_sigma = min(sigma_values, key=lambda sigma: np.mean(sigma_values[sigma]))
    (args.output_dir / "selected_mutation_sigma.txt").write_text(f"{shared_sigma:g}\n")

    sorted_fractions = sorted(fractions)
    sorted_sigmas = sorted(sigmas)
    means = np.array(
        [[np.mean(grouped[(fraction, sigma)]) for sigma in sorted_sigmas] for fraction in sorted_fractions]
    )
    figure, axis = plt.subplots(figsize=(7, 5))
    image = axis.imshow(means, cmap="viridis_r", aspect="auto")
    axis.set_xticks(range(len(sorted_sigmas)), [str(value) for value in sorted_sigmas])
    axis.set_yticks(range(len(sorted_fractions)), [str(value) for value in sorted_fractions])
    axis.set_xlabel("Mutation sigma")
    axis.set_ylabel("Parent fraction")
    axis.set_title("SLURM tuning: mean final best fitness")
    figure.colorbar(image, ax=axis, label="Fitness (lower is better)")
    for row_index in range(len(sorted_fractions)):
        for column_index in range(len(sorted_sigmas)):
            axis.text(column_index, row_index, f"{means[row_index, column_index]:.3f}", ha="center", va="center", color="white")
    figure.tight_layout()
    figure.savefig(args.output_dir / "tuning_heatmap.png", dpi=180)
    print(f"Best configuration: {ranked[0]}")
    print(f"Selected shared mutation sigma: {shared_sigma:g}")
    print(f"Results written to {args.output_dir}")


if __name__ == "__main__":
    main()