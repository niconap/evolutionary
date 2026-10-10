"""Plot evolutionary search against the matched random-search baseline."""

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
        if path.exists():
            with path.open(newline="") as file:
                runs.append([{key: float(value) for key, value in row.items()} for row in csv.DictReader(file)])
    if not runs:
        raise FileNotFoundError(f"No completed runs found for {prefix!r} in {results_dir}")
    return runs


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--output-dir", type=Path, default=Path("results/ea_vs_random_plots"))
    args = parser.parse_args()
    conditions = [
        ("EA, 20% parents", read_runs(args.results_dir, "parent_fraction_20"), "tab:blue"),
        ("Random search", read_runs(args.results_dir, "random_search"), "tab:orange"),
    ]
    args.output_dir.mkdir(parents=True, exist_ok=True)

    figure, axis = plt.subplots(figsize=(9, 5.5))
    summary_rows = []
    for label, runs, color in conditions:
        evaluations = np.array([row["evaluations"] for row in runs[0]])
        best = np.array([[row["best_fitness"] for row in run] for run in runs])
        mean = best.mean(axis=0)
        spread = best.std(axis=0)
        axis.plot(evaluations, mean, label=label, color=color)
        axis.fill_between(evaluations, mean - spread, mean + spread, color=color, alpha=0.15)
        for index, run in enumerate(runs):
            summary_rows.append([label, index, run[-1]["best_fitness"]])

    axis.set_xlabel("Fitness evaluations")
    axis.set_ylabel("Best-so-far distance to target (lower is better)")
    axis.set_title("Evolutionary search versus random search")
    axis.grid(alpha=0.25)
    axis.legend()
    figure.tight_layout()
    figure.savefig(args.output_dir / "convergence.png", dpi=180)
    plt.close(figure)

    with (args.output_dir / "final_fitness_summary.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["condition", "seed_run", "final_best_fitness"])
        writer.writerows(summary_rows)
    print(f"Plots written to {args.output_dir}")


if __name__ == "__main__":
    main()