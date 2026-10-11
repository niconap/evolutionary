"""All conditions including random search: 10/20/50/80/100% parents + random search.

random_search_fixed/generations.csv already stores best-so-far fitness in the
best_fitness column (see random_search.py), so it is plotted the same way as
the EA conditions - no special-casing needed.

Writes only to results/comparison_plots_all_with_random/.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from plot_comparison import read_runs
from plot_parent_pressure_full import plot_best_by_evaluations

CONDITIONS = [
    ("10%", "parent_fraction_10_fixed"),
    ("20%", "parent_fraction_20_fixed"),
    ("50%", "parent_fraction_50_fixed"),
    ("80%", "parent_fraction_80_fixed"),
    ("100%", "parent_fraction_100_fixed"),
    ("Random search", "random_search_fixed"),
]
COLORS = ["tab:red", "tab:orange", "tab:blue", "tab:green", "tab:purple", "tab:gray"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/comparison_plots_all_with_random"),
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    all_runs = [(label, read_runs(args.results_dir, prefix)) for label, prefix in CONDITIONS]

    # A. Convergence: best-so-far fitness vs. fitness evaluations
    figure, axis = plt.subplots(figsize=(9.5, 5.5))
    for (label, runs), color in zip(all_runs, COLORS):
        plot_best_by_evaluations(axis, runs, label, color)
    axis.set_xlabel("Fitness evaluations")
    axis.set_ylabel("Best-so-far distance to target")
    axis.set_title("Parent-Selection Conditions vs. Random Search")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(args.output_dir / "convergence_all_with_random.png", dpi=180)
    plt.close(figure)

    # B. Final fitness distributions (boxplot + individual seed points)
    figure, axis = plt.subplots(figsize=(10, 5.5))
    labels = [label for label, _ in all_runs]
    final_values = [[run[-1]["best_fitness"] for run in runs] for _, runs in all_runs]
    axis.boxplot(final_values, tick_labels=labels, showfliers=False)
    rng = np.random.default_rng(0)
    for position, values in enumerate(final_values, start=1):
        jitter = rng.uniform(-0.05, 0.05, size=len(values))
        axis.scatter(np.full(len(values), position) + jitter, values, color="black", zorder=3, s=20)
    axis.set_ylabel("Final best distance to target")
    axis.set_title("Final Best Fitness: All Conditions vs. Random Search")
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(args.output_dir / "final_fitness_all_with_random.png", dpi=180)
    plt.close(figure)

    # Numerical summaries
    with (args.output_dir / "all_conditions_summary.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["condition", "n", "mean_final_best", "std_final_best"])
        for (label, _), values in zip(all_runs, final_values):
            writer.writerow([label, len(values), np.mean(values), np.std(values)])

    with (args.output_dir / "all_conditions_per_seed.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["condition", "seed_run", "final_best_fitness"])
        for (label, _), values in zip(all_runs, final_values):
            for seed_index, value in enumerate(values):
                writer.writerow([label, seed_index, value])

    print(f"Plots and summaries written to {args.output_dir}")


if __name__ == "__main__":
    main()
