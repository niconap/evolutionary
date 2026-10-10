#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Override these without editing the script, for example:
# SEEDS="0 1 2 3 4 5 6 7 8 9" POPULATION_SIZE=20 GENERATIONS=25 ./run_parent_selection_comparison.sh
SEEDS=${SEEDS:-"0 1 2 3 4"}
POPULATION_SIZE=${POPULATION_SIZE:-10}
GENERATIONS=${GENERATIONS:-5}
WORKERS=${WORKERS:-$(nproc)}

run_condition() {
    local name="$1"
    local parent_fraction="$2"

    for seed in $SEEDS; do
        uv run --project ../.. python a2_experiment.py \
            --config config.yaml \
            --seed "$seed" \
            --population-size "$POPULATION_SIZE" \
            --generations "$GENERATIONS" \
            --parent-fraction "$parent_fraction" \
            --workers "$WORKERS" \
            --run-name "$name"
    done
}

run_condition parent_fraction_50 0.5
run_condition parent_fraction_20 0.2

uv run --project ../.. python plot_comparison.py