"""Plot matched parent-selection comparison runs."""

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


def plot_condition(ax: plt.Axes, runs: list[list[dict[str, float]]], label: str, color: str) -> None:
    generations = np.array([row["generation"] for row in runs[0]])
    best = np.array([[row["best_fitness"] for row in run] for run in runs])
    mean = np.array([[row["mean_fitness"] for row in run] for run in runs])
    best_mean = best.mean(axis=0)
    best_std = best.std(axis=0)
    ax.plot(generations, best_mean, label=f"{label} best", color=color)
    ax.fill_between(generations, best_mean - best_std, best_mean + best_std, color=color, alpha=0.15)
    ax.plot(generations, mean.mean(axis=0), label=f"{label} population mean", color=color, linestyle="--")


def write_summary(output_dir: Path, conditions: list[tuple[str, list[list[dict[str, float]]]]]) -> None:
    with (output_dir / "final_fitness_summary.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["condition", "seed_run", "final_best_fitness"])
        for label, runs in conditions:
            for index, run in enumerate(runs):
                writer.writerow([label, index, run[-1]["best_fitness"]])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--output-dir", type=Path, default=Path("results/comparison_plots"))
    args = parser.parse_args()

    conditions = [
        ("50% parents", read_runs(args.results_dir, "parent_fraction_50")),
        ("20% parents", read_runs(args.results_dir, "parent_fraction_20")),
    ]
    args.output_dir.mkdir(parents=True, exist_ok=True)

    figure, axis = plt.subplots(figsize=(9, 5.5))
    plot_condition(axis, conditions[0][1], conditions[0][0], "tab:blue")
    plot_condition(axis, conditions[1][1], conditions[1][0], "tab:orange")
    axis.set_xlabel("Generation")
    axis.set_ylabel("Distance to target (lower is better)")
    axis.set_title("Effect of parent-selection pressure")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(args.output_dir / "convergence.png", dpi=180)
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(7, 5.5))
    labels = [label for label, _ in conditions]
    final_values = [[run[-1]["best_fitness"] for run in runs] for _, runs in conditions]
    axis.boxplot(final_values, tick_labels=labels)
    axis.set_ylabel("Final best distance (lower is better)")
    axis.set_title("Final best fitness across seeds")
    axis.grid(axis="y", alpha=0.25)
    figure.tight_layout()
    figure.savefig(args.output_dir / "final_fitness.png", dpi=180)
    plt.close(figure)

    write_summary(args.output_dir, conditions)
    print(f"Plots written to {args.output_dir}")


if __name__ == "__main__":
    main()