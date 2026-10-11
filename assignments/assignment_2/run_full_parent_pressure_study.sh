#!/usr/bin/env bash
# Full parent-selection pressure study: extends the corrected 20/50/80%
# comparison to 10%, 20%, 50%, 80%, 100% parent fractions plus a matched
# random-search baseline, all extended to 10 seeds (0-9).
#
# Reuses existing valid runs (seeds 0-4 for 20/50/80%) and only executes what
# is missing: 10% (10 seeds), 100% (10 seeds), random search (10 seeds), and
# seeds 5-9 for 20/50/80%. Safe to re-run: a2_experiment.py/random_search.py
# refuse to overwrite an existing completed run directory, and this script
# skips any run whose generations.csv already exists.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

POPULATION_SIZE=${POPULATION_SIZE:-20}
GENERATIONS=${GENERATIONS:-25}
WORKERS=${WORKERS:-8}

run_ea() {
    local run_name="$1"
    local parent_fraction="$2"
    local seed="$3"
    local result_dir="results/${run_name}_seed_${seed}"
    if [[ -f "$result_dir/generations.csv" ]]; then
        echo "skip (already complete): $result_dir"
        return
    fi
    if [[ -e "$result_dir" ]]; then
        echo "incomplete result directory exists, remove it before rerunning: $result_dir" >&2
        exit 1
    fi
    echo "=== running $result_dir (parent_fraction=$parent_fraction) ==="
    uv run --project ../.. python a2_experiment.py \
        --config config.yaml \
        --seed "$seed" \
        --population-size "$POPULATION_SIZE" \
        --generations "$GENERATIONS" \
        --parent-fraction "$parent_fraction" \
        --workers "$WORKERS" \
        --run-name "$run_name"
}

run_random() {
    local seed="$1"
    local result_dir="results/random_search_fixed_seed_${seed}"
    if [[ -f "$result_dir/generations.csv" ]]; then
        echo "skip (already complete): $result_dir"
        return
    fi
    if [[ -e "$result_dir" ]]; then
        echo "incomplete result directory exists, remove it before rerunning: $result_dir" >&2
        exit 1
    fi
    echo "=== running $result_dir (random search) ==="
    uv run --project ../.. python random_search.py \
        --config config.yaml \
        --seed "$seed" \
        --population-size "$POPULATION_SIZE" \
        --generations "$GENERATIONS" \
        --workers "$WORKERS" \
        --run-name random_search_fixed
}

# 10% and 100% parents: all 10 seeds are new.
for seed in 0 1 2 3 4 5 6 7 8 9; do
    run_ea parent_fraction_10_fixed 0.1 "$seed"
done
for seed in 0 1 2 3 4 5 6 7 8 9; do
    run_ea parent_fraction_100_fixed 1.0 "$seed"
done

# Random-search baseline: all 10 seeds are new.
for seed in 0 1 2 3 4 5 6 7 8 9; do
    run_random "$seed"
done

# 20/50/80% parents: seeds 0-4 already exist and are reused; only run 5-9.
for seed in 5 6 7 8 9; do
    run_ea parent_fraction_20_fixed 0.2 "$seed"
done
for seed in 5 6 7 8 9; do
    run_ea parent_fraction_50_fixed 0.5 "$seed"
done
for seed in 5 6 7 8 9; do
    run_ea parent_fraction_80_fixed 0.8 "$seed"
done

echo "All runs complete."
