#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd -- "$SCRIPT_DIR/../.." && pwd)"
cd "$SCRIPT_DIR"
mkdir -p logs

PARENT_FRACTIONS=${PARENT_FRACTIONS:-"0.2,0.5,0.8"}
MUTATION_SIGMAS=${MUTATION_SIGMAS:-"0.05,0.1,0.2"}
SEEDS=${SEEDS:-"0,1,2"}
POPULATION_SIZE=${POPULATION_SIZE:-20}
GENERATIONS=${GENERATIONS:-25}
MAX_CONCURRENT=${MAX_CONCURRENT:-9}
FINAL_SEEDS=${FINAL_SEEDS:-"5,6,7,8,9"}
FINAL_MAX_CONCURRENT=${FINAL_MAX_CONCURRENT:-9}
FINAL_MUTATION_SIGMA=${FINAL_MUTATION_SIGMA:-}

count_values() {
    local value="$1"
    awk -F, '{print NF}' <<< "$value"
}

num_tasks=$(( $(count_values "$PARENT_FRACTIONS") * $(count_values "$MUTATION_SIGMAS") * $(count_values "$SEEDS") ))
slurm_parent_fractions=${PARENT_FRACTIONS//,/;}
slurm_mutation_sigmas=${MUTATION_SIGMAS//,/;}
slurm_seeds=${SEEDS//,/;}
export_args="PROJECT_DIR=$PROJECT_DIR,PARENT_FRACTIONS=$slurm_parent_fractions,MUTATION_SIGMAS=$slurm_mutation_sigmas,SEEDS=$slurm_seeds,POPULATION_SIZE=$POPULATION_SIZE,GENERATIONS=$GENERATIONS"

account_args=()
if [[ -n "${SBATCH_ACCOUNT:-}" ]]; then
    account_args+=(--account "$SBATCH_ACCOUNT")
fi

array_job_id=$(sbatch --parsable \
    "${account_args[@]}" \
    --array="0-$((num_tasks - 1))%$MAX_CONCURRENT" \
    --export="ALL,$export_args" \
    slurm_tune.sbatch)

echo "Submitted SLURM tuning array: $array_job_id"
echo "Tasks: $num_tasks, concurrency limit: $MAX_CONCURRENT"

collector_job_id=$(sbatch --parsable \
    "${account_args[@]}" \
    --partition=rome \
    --cpus-per-task=1 \
    --mem=2G \
    --time=00:15:00 \
    --dependency="afterok:$array_job_id" \
    --output=logs/slurm-collect-%j.out \
    --error=logs/slurm-collect-%j.err \
    --export="ALL,$export_args" \
    --wrap="cd '$SCRIPT_DIR' && uv run --project '$PROJECT_DIR' python collect_tuning.py --parent-fractions '$PARENT_FRACTIONS' --mutation-sigmas '$MUTATION_SIGMAS' --seeds '$SEEDS' --output-dir results/slurm_tuning"
)
echo "Submitted collector job: $collector_job_id"

slurm_final_seeds=${FINAL_SEEDS//,/;}
final_export_args="PROJECT_DIR=$PROJECT_DIR,FINAL_SEEDS=$slurm_final_seeds,FINAL_MUTATION_SIGMA=$FINAL_MUTATION_SIGMA,POPULATION_SIZE=$POPULATION_SIZE,GENERATIONS=$GENERATIONS"
final_task_count=$(count_values "$FINAL_SEEDS")

final_job_id=$(sbatch --parsable \
    "${account_args[@]}" \
    --array="0-$((final_task_count - 1))%$FINAL_MAX_CONCURRENT" \
    --dependency="afterok:$collector_job_id" \
    --export="ALL,$final_export_args" \
    slurm_final_comparison.sbatch
)
echo "Submitted final comparison array: $final_job_id"

plot_job_id=$(sbatch --parsable \
    "${account_args[@]}" \
    --dependency="afterok:$final_job_id" \
    --export="ALL,PROJECT_DIR=$PROJECT_DIR" \
    plot_results.sbatch
)
echo "Submitted report plotting job: $plot_job_id"