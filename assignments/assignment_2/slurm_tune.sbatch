#!/usr/bin/env bash
# One SLURM array task = one parameter combination and one random seed.
# The submission wrapper supplies the comma-separated parameter lists.
#SBATCH --partition=rome
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=logs/slurm-%A_%a.out
#SBATCH --error=logs/slurm-%A_%a.err

set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"
PROJECT_DIR=${PROJECT_DIR:?Set PROJECT_DIR to the repository root}
ASSIGNMENT_DIR="$PROJECT_DIR/assignments/assignment_2"
cd "$ASSIGNMENT_DIR"

IFS=';' read -r -a parent_fractions <<< "${PARENT_FRACTIONS:-0.2;0.5;0.8}"
IFS=';' read -r -a mutation_sigmas <<< "${MUTATION_SIGMAS:-0.05;0.1;0.2}"
IFS=';' read -r -a seeds <<< "${SEEDS:-0;1;2}"

num_sigmas=${#mutation_sigmas[@]}
num_seeds=${#seeds[@]}
task_id=${SLURM_ARRAY_TASK_ID:?This script must run as a SLURM array}

fraction_index=$((task_id / (num_sigmas * num_seeds)))
remainder=$((task_id % (num_sigmas * num_seeds)))
sigma_index=$((remainder / num_seeds))
seed_index=$((remainder % num_seeds))

parent_fraction=${parent_fractions[$fraction_index]}
mutation_sigma=${mutation_sigmas[$sigma_index]}
seed=${seeds[$seed_index]}
run_name="tune_fraction_${parent_fraction}_sigma_${mutation_sigma}"

echo "host: $(hostname)"
echo "task: $task_id"
echo "parent fraction: $parent_fraction"
echo "mutation sigma: $mutation_sigma"
echo "seed: $seed"
echo "workers: ${SLURM_CPUS_PER_TASK:-1}"

uv run --project "$PROJECT_DIR" python a2_experiment.py \
    --config config.yaml \
    --seed "$seed" \
    --population-size "${POPULATION_SIZE:-20}" \
    --generations "${GENERATIONS:-25}" \
    --parent-fraction "$parent_fraction" \
    --mutation-sigma "$mutation_sigma" \
    --workers "${SLURM_CPUS_PER_TASK:-1}" \
    --run-name "$run_name"