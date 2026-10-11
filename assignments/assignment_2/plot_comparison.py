"""Plot the corrected matched parent-selection comparison runs.

By default this reads ONLY the corrected run names
(`parent_fraction_20_fixed` / `parent_fraction_50_fixed`), which were
produced after the survivor-selection confound was fixed. The old
`parent_fraction_20` / `parent_fraction_50` runs are never read unless
explicitly requested via `--condition-a-prefix` / `--condition-b-prefix`.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def read_runs(results_dir: Path, prefix: str) -> list[list[dict[str, float]]]:
    runs = []
    for run_dir in sorted(results_dir.glob(f"{prefix}_seed_*")):
        path = run_dir / "generations.csv"
        if not path.exists():
            continue
        with path.open(newline="") as file:
            runs.append([{key: float(value) for key, value in row.items()} for row in csv.DictReader(file)])
    if not runs:
        raise FileNotFoundError(f"No completed runs found for {prefix!r} in {results_dir}")
    return runs


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


def write_per_seed_csv(output_dir: Path, conditions: list[tuple[str, list[list[dict[str, float]]]]]) -> None:
    with (output_dir / "final_fitness_per_seed.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["condition", "seed_run", "final_best_fitness"])
        for label, runs in conditions:
            for index, run in enumerate(runs):
                writer.writerow([label, index, run[-1]["best_fitness"]])


def write_summary_csv(output_dir: Path, conditions: list[tuple[str, list[list[dict[str, float]]]]]) -> None:
    with (output_dir / "parent_selection_summary.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["condition", "n", "mean_final_best", "std_final_best"])
        for label, runs in conditions:
            final_values = [run[-1]["best_fitness"] for run in runs]
            writer.writerow([label, len(final_values), np.mean(final_values), np.std(final_values)])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--output-dir", type=Path, default=Path("results/comparison_plots"))
    parser.add_argument("--condition-a-prefix", default="parent_fraction_20_fixed")
    parser.add_argument("--condition-a-label", default="20% parents")
    parser.add_argument("--condition-b-prefix", default="parent_fraction_50_fixed")
    parser.add_argument("--condition-b-label", default="50% parents")
    args = parser.parse_args()

    conditions = [
        (args.condition_a_label, read_runs(args.results_dir, args.condition_a_prefix)),
        (args.condition_b_label, read_runs(args.results_dir, args.condition_b_prefix)),
    ]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    colors = ["tab:orange", "tab:blue"]

    # --- Graph 1: convergence, best fitness vs. fitness evaluations --------- #
    figure, axis = plt.subplots(figsize=(9, 5.5))
    for (label, runs), color in zip(conditions, colors):
        plot_best_by_evaluations(axis, runs, label, color)
    axis.set_xlabel("Fitness evaluations")
    axis.set_ylabel("Best distance to target")
    axis.set_title("Effect of Parent-Selection Pressure")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(args.output_dir / "convergence.png", dpi=180)
    plt.close(figure)

    # --- Additional: convergence by generation (secondary x-axis view) ------ #
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

    # --- Graph 2: final best fitness distribution, with seed points --------- #
    figure, axis = plt.subplots(figsize=(7, 5.5))
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

    # --- Optional: population mean convergence, kept separate --------------- #
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