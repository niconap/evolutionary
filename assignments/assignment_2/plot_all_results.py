"""Create report-quality figures from Assignment 2 result directories."""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure

mpl.rcParams.update(
    {
        "font.family": "serif",
        "font.size": 10,
        "axes.titlesize": 12,
        "axes.labelsize": 11,
        "legend.fontsize": 9,
        "figure.dpi": 120,
        "savefig.dpi": 300,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.22,
        "grid.linewidth": 0.7,
    }
)


def read_run(path: Path) -> list[dict[str, float]]:
    with (path / "generations.csv").open(newline="") as file:
        return [{key: float(value) for key, value in row.items()} for row in csv.DictReader(file)]


def find_runs(results_dir: Path, prefix: str) -> list[list[dict[str, float]]]:
    runs = []
    for path in sorted(results_dir.glob(f"{prefix}_seed_*")):
        if (path / "generations.csv").exists():
            runs.append(read_run(path))
    return runs


def save_figure(figure: Figure, output_dir: Path, name: str) -> None:
    figure.tight_layout()
    figure.savefig(output_dir / f"{name}.pdf", bbox_inches="tight")
    figure.savefig(output_dir / f"{name}.png", bbox_inches="tight")
    plt.close(figure)


def plot_convergence(
    conditions: list[tuple[str, list[list[dict[str, float]]], str]],
    output_dir: Path,
    name: str,
    title: str,
) -> None:
    figure, axis = plt.subplots(figsize=(7.2, 4.4))
    for label, runs, color in conditions:
        evaluations = np.array([row["evaluations"] for row in runs[0]])
        best = np.array([[row["best_fitness"] for row in run] for run in runs])
        mean = best.mean(axis=0)
        spread = best.std(axis=0, ddof=1) if len(runs) > 1 else np.zeros_like(mean)
        axis.plot(evaluations, mean, color=color, linewidth=2, label=f"{label} (n={len(runs)})")
        axis.fill_between(evaluations, mean - spread, mean + spread, color=color, alpha=0.16)
    axis.set_xlabel("Fitness evaluations")
    axis.set_ylabel("Best-so-far distance to target")
    axis.set_title(title)
    axis.legend(frameon=False)
    save_figure(figure, output_dir, name)


def plot_final_distributions(
    conditions: list[tuple[str, list[list[dict[str, float]]], str]], output_dir: Path
) -> None:
    figure, axis = plt.subplots(figsize=(7.2, 4.4))
    values = [[run[-1]["best_fitness"] for run in runs] for _, runs, _ in conditions]
    box = axis.boxplot(values, patch_artist=True, tick_labels=[label for label, _, _ in conditions])
    for patch, (_, _, color) in zip(box["boxes"], conditions):
        patch.set_facecolor(color)
        patch.set_alpha(0.65)
    for index, group in enumerate(values, start=1):
        jitter = np.linspace(-0.08, 0.08, len(group)) if len(group) > 1 else [0]
        axis.scatter(np.full(len(group), index) + jitter, group, color="black", s=18, zorder=3)
    axis.set_ylabel("Final best distance to target")
    axis.set_title("Final performance across independent seeds")
    save_figure(figure, output_dir, "final_fitness_distributions")


def plot_tuning_heatmap(results_dir: Path, output_dir: Path) -> None:
    pattern = re.compile(r"tune_fraction_(.+)_sigma_(.+)_seed_\d+$")
    grouped: dict[tuple[float, float], list[float]] = defaultdict(list)
    for path in results_dir.iterdir():
        match = pattern.fullmatch(path.name)
        if match and (path / "generations.csv").exists():
            grouped[(float(match.group(1)), float(match.group(2)))].append(read_run(path)[-1]["best_fitness"])
    if not grouped:
        return

    fractions = sorted({key[0] for key in grouped})
    sigmas = sorted({key[1] for key in grouped})
    means = np.array([[np.mean(grouped[(fraction, sigma)]) for sigma in sigmas] for fraction in fractions])
    figure, axis = plt.subplots(figsize=(6.8, 4.8))
    image = axis.imshow(means, cmap="viridis_r", aspect="auto")
    axis.set_xticks(range(len(sigmas)), [f"{value:g}" for value in sigmas])
    axis.set_yticks(range(len(fractions)), [f"{value:g}" for value in fractions])
    axis.set_xlabel("Mutation sigma")
    axis.set_ylabel("Parent fraction")
    axis.set_title("Parameter tuning: mean final fitness")
    figure.colorbar(image, ax=axis, label="Distance (lower is better)")
    for row_index in range(len(fractions)):
        for column_index in range(len(sigmas)):
            axis.text(column_index, row_index, f"{means[row_index, column_index]:.3f}", ha="center", va="center", color="white")
    save_figure(figure, output_dir, "parameter_tuning_heatmap")

    with (output_dir / "parameter_tuning_summary.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["parent_fraction", "mutation_sigma", "mean_final_best", "std_final_best", "n"])
        for (fraction, sigma), values in sorted(grouped.items(), key=lambda item: np.mean(item[1])):
            writer.writerow([fraction, sigma, np.mean(values), np.std(values, ddof=1) if len(values) > 1 else 0.0, len(values)])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--output-dir", type=Path, default=Path("results/report_plots"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    colors = {
        "Random search": "#D55E00",
        "EA, 20% parents": "#0072B2",
        "EA, 50% parents": "#009E73",
        "Matched random search": "#D55E00",
    }
    final_ea_20 = find_runs(args.results_dir, "final_parent_fraction_20")
    final_ea_50 = find_runs(args.results_dir, "final_parent_fraction_50")
    final_random = find_runs(args.results_dir, "final_random_search")
    if final_ea_20 and final_ea_50 and final_random:
        available = [
            ("EA, 20% parents", final_ea_20, colors["EA, 20% parents"]),
            ("EA, 50% parents", final_ea_50, colors["EA, 50% parents"]),
            ("Matched random search", final_random, colors["Matched random search"]),
        ]
    else:
        available = []
    for label, prefix in (
        ("EA, 20% parents", "parent_fraction_20"),
        ("EA, 50% parents", "parent_fraction_50"),
        ("Random search", "random_search"),
    ):
        runs = find_runs(args.results_dir, prefix)
        if runs and not available:
            available.append((label, runs, colors[label]))

    if not available:
        raise FileNotFoundError(f"No completed runs found in {args.results_dir}")
    plot_convergence(available, args.output_dir, "convergence_all_conditions", "Search performance across evaluations")
    plot_final_distributions(available, args.output_dir)

    ea_conditions = [condition for condition in available if condition[0].startswith("EA")]
    if len(ea_conditions) >= 2:
        plot_convergence(ea_conditions, args.output_dir, "selection_pressure_convergence", "Effect of parent-selection pressure")
    plot_tuning_heatmap(args.results_dir, args.output_dir)
    print(f"Report figures written to {args.output_dir}")


if __name__ == "__main__":
    main()