"""Grid-search parent fraction and mutation sigma for Assignment 2."""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent


def parse_values(text: str) -> list[float]:
    return [float(value) for value in text.split(",") if value.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tune parent fraction and mutation sigma.")
    parser.add_argument("--seeds", default="0,1,2", help="Comma-separated pilot seeds.")
    parser.add_argument("--parent-fractions", default="0.2,0.5,0.8")
    parser.add_argument("--mutation-sigmas", default="0.05,0.1,0.2")
    parser.add_argument("--population-size", type=int, default=10)
    parser.add_argument("--generations", type=int, default=5)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--output-dir", type=Path, default=Path("results/tuning"))
    return parser.parse_args()


def run_if_missing(
    run_name: str,
    seed: int,
    parent_fraction: float,
    mutation_sigma: float,
    args: argparse.Namespace,
) -> None:
    result_dir = SCRIPT_DIR / "results" / f"{run_name}_seed_{seed}"
    if (result_dir / "generations.csv").exists():
        print(f"reusing completed run: {result_dir}")
        return
    if result_dir.exists():
        raise RuntimeError(f"Incomplete result directory exists: {result_dir}")

    command = [
        sys.executable,
        "a2_experiment.py",
        "--config",
        "config.yaml",
        "--seed",
        str(seed),
        "--population-size",
        str(args.population_size),
        "--generations",
        str(args.generations),
        "--parent-fraction",
        str(parent_fraction),
        "--mutation-sigma",
        str(mutation_sigma),
        "--workers",
        str(args.workers),
        "--run-name",
        run_name,
    ]
    subprocess.run(command, cwd=SCRIPT_DIR, check=True)


def final_fitness(result_dir: Path) -> float:
    with (result_dir / "generations.csv").open(newline="") as file:
        rows = list(csv.DictReader(file))
    return float(rows[-1]["best_fitness"])


def main() -> None:
    args = parse_args()
    seeds = [int(value) for value in args.seeds.split(",") if value.strip()]
    parent_fractions = parse_values(args.parent_fractions)
    mutation_sigmas = parse_values(args.mutation_sigmas)
    summary_rows = []

    for parent_fraction in parent_fractions:
        for mutation_sigma in mutation_sigmas:
            run_name = f"tune_fraction_{parent_fraction:g}_sigma_{mutation_sigma:g}"
            for seed in seeds:
                run_if_missing(run_name, seed, parent_fraction, mutation_sigma, args)
                result_dir = SCRIPT_DIR / "results" / f"{run_name}_seed_{seed}"
                summary_rows.append(
                    {
                        "parent_fraction": parent_fraction,
                        "mutation_sigma": mutation_sigma,
                        "seed": seed,
                        "final_best_fitness": final_fitness(result_dir),
                    }
                )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = args.output_dir / "tuning_runs.csv"
    with summary_path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(summary_rows[0]))
        writer.writeheader()
        writer.writerows(summary_rows)

    grouped = {}
    for row in summary_rows:
        key = (row["parent_fraction"], row["mutation_sigma"])
        grouped.setdefault(key, []).append(row["final_best_fitness"])
    ranked = sorted(
        (
            {
                "parent_fraction": key[0],
                "mutation_sigma": key[1],
                "mean_final_best": float(np.mean(values)),
                "std_final_best": float(np.std(values, ddof=1)) if len(values) > 1 else 0.0,
            }
            for key, values in grouped.items()
        ),
        key=lambda row: row["mean_final_best"],
    )
    with (args.output_dir / "tuning_summary.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(ranked[0]))
        writer.writeheader()
        writer.writerows(ranked)

    fractions = sorted(parent_fractions)
    sigmas = sorted(mutation_sigmas)
    heatmap = np.array(
        [[grouped[(fraction, sigma)] for sigma in sigmas] for fraction in fractions],
        dtype=object,
    )
    means = np.array([[np.mean(values) for values in row] for row in heatmap])
    figure, axis = plt.subplots(figsize=(7, 5))
    image = axis.imshow(means, cmap="viridis_r", aspect="auto")
    axis.set_xticks(range(len(sigmas)), [str(value) for value in sigmas])
    axis.set_yticks(range(len(fractions)), [str(value) for value in fractions])
    axis.set_xlabel("Mutation sigma")
    axis.set_ylabel("Parent fraction")
    axis.set_title("Mean final best fitness; lower is better")
    figure.colorbar(image, ax=axis, label="Mean final best fitness")
    for row_index in range(len(fractions)):
        for column_index in range(len(sigmas)):
            axis.text(column_index, row_index, f"{means[row_index, column_index]:.3f}", ha="center", va="center", color="white")
    figure.tight_layout()
    figure.savefig(args.output_dir / "tuning_heatmap.png", dpi=180)
    plt.close(figure)

    best = ranked[0]
    print(
        "Best pilot configuration: "
        f"parent_fraction={best['parent_fraction']}, "
        f"mutation_sigma={best['mutation_sigma']}, "
        f"mean_final_best={best['mean_final_best']:.4f}"
    )
    print(f"Tuning results written to {args.output_dir}")


if __name__ == "__main__":
    main()