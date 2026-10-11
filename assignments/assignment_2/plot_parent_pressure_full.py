"""Parent-fraction-only plots for the full study: 10% / 20% / 50% / 80% / 100%.

Does NOT include random search (see plot_all_with_random.py for that).
Writes only to results/comparison_plots_parent_pressure_full/ - does not
touch comparison_plots_fixed/, comparison_plots_20_vs_80/, or
comparison_plots_all_parent_fractions/.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from plot_comparison import read_runs

CONDITIONS = [
    ("10%", "parent_fraction_10_fixed"),
    ("20%", "parent_fraction_20_fixed"),
    ("50%", "parent_fraction_50_fixed"),
    ("80%", "parent_fraction_80_fixed"),
    ("100%", "parent_fraction_100_fixed"),
]
PARENT_FRACTIONS = [10, 20, 50, 80, 100]
COLORS = ["tab:red", "tab:orange", "tab:blue", "tab:green", "tab:purple"]


def plot_best_by_evaluations(ax: plt.Axes, runs: list[list[dict[str, float]]], label: str, color: str) -> None:
    evaluations = np.array([row["evaluations"] for row in runs[0]])
    best = np.array([[row["best_fitness"] for row in run] for run in runs])
    best_mean = best.mean(axis=0)
    best_std = best.std(axis=0)
    ax.plot(evaluations, best_mean, label=label, color=color)
    ax.fill_between(evaluations, best_mean - best_std, best_mean + best_std, color=color, alpha=0.15)


def plot_best_by_generation(ax: plt.Axes, runs: list[list[dict[str, float]]], label: str, color: str) -> None:
    generations = np.array([row["generation"] for row in runs[0]])
    best = np.array([[row["best_fitness"] for row in run] for run in runs])
    best_mean = best.mean(axis=0)
    best_std = best.std(axis=0)
    ax.plot(generations, best_mean, label=label, color=color)
    ax.fill_between(generations, best_mean - best_std, best_mean + best_std, color=color, alpha=0.15)


def plot_population_mean(ax: plt.Axes, runs: list[list[dict[str, float]]], label: str, color: str) -> None:
    evaluations = np.array([row["evaluations"] for row in runs[0]])
    mean = np.array([[row["mean_fitness"] for row in run] for run in runs])
    ax.plot(evaluations, mean.mean(axis=0), label=label, color=color)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results/comparison_plots_parent_pressure_full"),
    )
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    all_runs = [(label, read_runs(args.results_dir, prefix)) for label, prefix in CONDITIONS]

    # A. Main convergence: best fitness vs. fitness evaluations
    figure, axis = plt.subplots(figsize=(9.5, 5.5))
    for (label, runs), color in zip(all_runs, COLORS):
        plot_best_by_evaluations(axis, runs, label, color)
    axis.set_xlabel("Fitness evaluations")
    axis.set_ylabel("Best distance to target")
    axis.set_title("Effect of Parent-Selection Pressure")
    axis.grid(alpha=0.25)
    axis.legend(title="Parent fraction")
    figure.tight_layout()
    figure.savefig(args.output_dir / "convergence_parent_fractions.png", dpi=180)
    plt.close(figure)

    # B. Convergence by generation
    figure, axis = plt.subplots(figsize=(9.5, 5.5))
    for (label, runs), color in zip(all_runs, COLORS):
        plot_best_by_generation(axis, runs, label, color)
    axis.set_xlabel("Generation")
    axis.set_ylabel("Best distance to target")
    axis.set_title("Effect of Parent-Selection Pressure (by generation)")
    axis.grid(alpha=0.25)
    axis.legend(title="Parent fraction")
    figure.tight_layout()
    figure.savefig(args.output_dir / "convergence_parent_fractions_by_generation.png", dpi=180)
    plt.close(figure)

    # C. Final fitness distributions (boxplot + individual seed points)
    figure, axis = plt.subplots(figsize=(9, 5.5))
    labels = [label for label, _ in all_runs]
    final_values = [[run[-1]["best_fitness"] for run in runs] for _, runs in all_runs]
    axis.boxplot(final_values, tick_labels=labels, showfliers=False)
    rng = np.random.default_rng(0)
    for position, values in enumerate(final_values, start=1):
        jitter = rng.uniform(-0.05, 0.05, size=len(values))
        axis.scatter(np.full(len(values), position) + jitter, values, color="black", zorder=3, s=20)
    axis.set_xlabel("Parent fraction")
    axis.set_ylabel("Final best distance to target")
    axis.set_title("Final Best Fitness Across Seeds")
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(args.output_dir / "final_fitness_parent_fractions.png", dpi=180)
    plt.close(figure)

    # D. Parent fraction vs. mean final fitness, with +/-1 std error bars
    means = [float(np.mean(values)) for values in final_values]
    stds = [float(np.std(values)) for values in final_values]
    figure, axis = plt.subplots(figsize=(8, 5.5))
    axis.errorbar(PARENT_FRACTIONS, means, yerr=stds, marker="o", capsize=5, color="tab:blue")
    axis.set_xlabel("Parent fraction (%)")
    axis.set_ylabel("Mean final best fitness (+/- 1 std)")
    axis.set_title("Final Fitness vs. Parent-Selection Pressure")
    axis.set_xticks(PARENT_FRACTIONS)
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(args.output_dir / "final_fitness_vs_parent_fraction.png", dpi=180)
    plt.close(figure)

    # E. Population mean fitness convergence (kept separate from best-fitness)
    figure, axis = plt.subplots(figsize=(9.5, 5.5))
    for (label, runs), color in zip(all_runs, COLORS):
        plot_population_mean(axis, runs, label, color)
    axis.set_xlabel("Fitness evaluations")
    axis.set_ylabel("Mean population distance to target")
    axis.set_title("Population Mean Fitness Convergence")
    axis.grid(alpha=0.25)
    axis.legend(title="Parent fraction")
    figure.tight_layout()
    figure.savefig(args.output_dir / "population_mean_parent_fractions.png", dpi=180)
    plt.close(figure)

    # Numerical summaries
    with (args.output_dir / "parent_selection_summary.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["condition", "n", "mean_final_best", "std_final_best"])
        for (label, _), values in zip(all_runs, final_values):
            writer.writerow([label, len(values), np.mean(values), np.std(values)])

    with (args.output_dir / "parent_selection_per_seed.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["condition", "seed_run", "final_best_fitness"])
        for (label, _), values in zip(all_runs, final_values):
            for seed_index, value in enumerate(values):
                writer.writerow([label, seed_index, value])

    print(f"Plots and summaries written to {args.output_dir}")


if __name__ == "__main__":
    main()
