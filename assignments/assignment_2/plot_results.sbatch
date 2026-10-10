#!/usr/bin/env bash
#SBATCH --partition=rome
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=00:15:00
#SBATCH --output=logs/plot-%j.out
#SBATCH --error=logs/plot-%j.err

set -euo pipefail

PROJECT_DIR=${PROJECT_DIR:?Set PROJECT_DIR to the repository root}
ASSIGNMENT_DIR="$PROJECT_DIR/assignments/assignment_2"
cd "$ASSIGNMENT_DIR"

uv run --project "$PROJECT_DIR" python plot_all_results.py \
    --results-dir results \
    --output-dir results/report_plots