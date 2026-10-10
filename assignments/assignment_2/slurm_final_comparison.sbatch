#!/usr/bin/env bash
# One task runs both parent-retention conditions and matched random search.
#SBATCH --partition=rome
#SBATCH --cpus-per-task=8
#SBATCH --mem=8G
#SBATCH --time=01:00:00
#SBATCH --output=logs/final-%A_%a.out
#SBATCH --error=logs/final-%A_%a.err

set -euo pipefail

export PATH="$HOME/.local/bin:$PATH"
PROJECT_DIR=${PROJECT_DIR:?Set PROJECT_DIR to the repository root}
ASSIGNMENT_DIR="$PROJECT_DIR/assignments/assignment_2"
cd "$ASSIGNMENT_DIR"

IFS=';' read -r -a final_seeds <<< "${FINAL_SEEDS:-5;6;7;8;9}"
seed=${final_seeds[${SLURM_ARRAY_TASK_ID:?This script must run as a SLURM array}]}
if [[ -n "${FINAL_MUTATION_SIGMA:-}" ]]; then
    mutation_sigma="$FINAL_MUTATION_SIGMA"
else
    mutation_sigma=$(< results/slurm_tuning/selected_mutation_sigma.txt)
fi
workers=${SLURM_CPUS_PER_TASK:-1}

echo "host: $(hostname)"
echo "seed: $seed"
echo "parent fractions: 0.2, 0.5"
echo "shared mutation sigma: $mutation_sigma"
echo "workers: $workers"

run_if_missing() {
    local run_name="$1"
    local result_dir="results/${run_name}_seed_${seed}"
    shift
    if [[ -f "$result_dir/generations.csv" ]]; then
        echo "reusing completed run: $result_dir"
        return
    fi
    if [[ -e "$result_dir" ]]; then
        echo "incomplete result directory exists: $result_dir" >&2
        exit 1
    fi
    "$@"
}

for parent_fraction in 0.2 0.5; do
    if [[ "$parent_fraction" == "0.2" ]]; then
        run_name=final_parent_fraction_20
    else
        run_name=final_parent_fraction_50
    fi
    run_if_missing "$run_name" uv run --project "$PROJECT_DIR" python a2_experiment.py \
        --config config.yaml \
        --seed "$seed" \
        --population-size "${POPULATION_SIZE:-20}" \
        --generations "${GENERATIONS:-25}" \
        --parent-fraction "$parent_fraction" \
        --mutation-sigma "$mutation_sigma" \
        --workers "$workers" \
        --run-name "$run_name"
done

run_if_missing final_random_search uv run --project "$PROJECT_DIR" python random_search.py \
    --config config.yaml \
    --seed "$seed" \
    --population-size "${POPULATION_SIZE:-20}" \
    --generations "${GENERATIONS:-25}" \
    --workers "$workers" \
    --run-name final_random_search