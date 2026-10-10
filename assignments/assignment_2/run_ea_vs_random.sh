#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

SEEDS=${SEEDS:-"0 1 2 3 4"}
POPULATION_SIZE=${POPULATION_SIZE:-10}
GENERATIONS=${GENERATIONS:-5}
WORKERS=${WORKERS:-$(nproc)}

run_if_missing() {
    local run_name="$1"
    local seed="$2"
    shift 2
    local result_dir="results/${run_name}_seed_${seed}"

    if [[ -f "$result_dir/generations.csv" ]]; then
        echo "reusing completed run: $result_dir"
        return
    fi
    if [[ -e "$result_dir" ]]; then
        echo "incomplete result directory exists: $result_dir" >&2
        echo "Remove it manually before retrying." >&2
        exit 1
    fi
    "$@"
}

for seed in $SEEDS; do
    run_if_missing parent_fraction_20 "$seed" uv run --project ../.. python a2_experiment.py \
        --config config.yaml \
        --seed "$seed" \
        --population-size "$POPULATION_SIZE" \
        --generations "$GENERATIONS" \
        --parent-fraction 0.2 \
        --workers "$WORKERS" \
        --run-name parent_fraction_20

    run_if_missing random_search "$seed" uv run --project ../.. python random_search.py \
        --config config.yaml \
        --seed "$seed" \
        --population-size "$POPULATION_SIZE" \
        --generations "$GENERATIONS" \
        --workers "$WORKERS" \
        --run-name random_search
done

uv run --project ../.. python plot_ea_vs_random.py