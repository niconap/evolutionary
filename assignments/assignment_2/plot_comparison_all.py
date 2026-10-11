"""Optional three-way overview plot: 20% vs 50% vs 80% parent-selection.

Reuses the plotting helpers from plot_comparison.py. Writes ONLY to
results/comparison_plots_all_parent_fractions/ - never touches
comparison_plots_fixed/ (20% vs 50%) or comparison_plots_20_vs_80/
(20% vs 80%), which remain the primary pairwise comparisons.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from plot_comparison import (
    plot_best_by_evaluations,
    plot_best_by_generation,
    plot_population_mean,
    read_runs,
    write_per_seed_csv,
    write_summary_csv,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/comparison_plots_all_parent_fractions"),
    )
    args = parser.parse_args()

    conditions = [
        ("20% parents", read_runs(args.results_dir, "parent_fraction_20_fixed")),
        ("50% parents", read_runs(args.results_dir, "parent_fraction_50_fixed")),
        ("80% parents", read_runs(args.results_dir, "parent_fraction_80_fixed")),
    ]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    colors = ["tab:orange", "tab:blue", "tab:green"]

    figure, axis = plt.subplots(figsize=(9, 5.5))
    for (label, runs), color in zip(conditions, colors):
        plot_best_by_evaluations(axis, runs, label, color)
    axis.set_xlabel("Fitness evaluations")
    axis.set_ylabel("Best distance to target")
    axis.set_title("Effect of Parent-Selection Pressure (20% / 50% / 80%)")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(args.output_dir / "convergence.png", dpi=180)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(9, 5.5))
    for (label, runs), color in zip(conditions, colors):
        plot_best_by_generation(axis, runs, label, color)
    axis.set_xlabel("Generation")
    axis.set_ylabel("Best distance to target")
    axis.set_title("Effect of Parent-Selection Pressure (by generation)")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(args.output_dir / "convergence_by_generation.png", dpi=180)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(7.5, 5.5))
    labels = [label for label, _ in conditions]
    final_values = [[run[-1]["best_fitness"] for run in runs] for _, runs in conditions]
    axis.boxplot(final_values, tick_labels=labels, showfliers=False)
    rng = np.random.default_rng(0)
    for position, values in enumerate(final_values, start=1):
        jitter = rng.uniform(-0.05, 0.05, size=len(values))
        axis.scatter(np.full(len(values), position) + jitter, values, color="black", zorder=3, s=25)
    axis.set_ylabel("Final best distance to target")
    axis.set_title("Final best fitness across seeds")
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(args.output_dir / "final_fitness.png", dpi=180)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(9, 5.5))
    for (label, runs), color in zip(conditions, colors):
        plot_population_mean(axis, runs, label, color)
    axis.set_xlabel("Fitness evaluations")
    axis.set_ylabel("Mean population distance to target")
    axis.set_title("Population Mean Fitness Convergence")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(args.output_dir / "population_mean.png", dpi=180)
    plt.close(figure)

    write_per_seed_csv(args.output_dir, conditions)
    write_summary_csv(args.output_dir, conditions)
    print(f"Plots and summaries written to {args.output_dir}")


if __name__ == "__main__":
    main()
