#!/usr/bin/env bash
# Corrected parent-selection comparison: survivor selection is now
# (full previous population + offspring) for BOTH conditions, so only the
# parent-pool size differs between EA A (20%) and EA B (50%).
#
# Uses NEW run names (parent_fraction_20_fixed / parent_fraction_50_fixed) so
# the old, confounded runs (parent_fraction_20 / parent_fraction_50) are never
# mixed into these results or into the plots.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Override these without editing the script, for example:
# SEEDS="0 1 2 3 4" POPULATION_SIZE=20 GENERATIONS=25 WORKERS=8 ./run_parent_selection_comparison_fixed.sh
SEEDS=${SEEDS:-"0 1 2 3 4"}
POPULATION_SIZE=${POPULATION_SIZE:-20}
GENERATIONS=${GENERATIONS:-25}
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

run_condition parent_fraction_20_fixed 0.2
run_condition parent_fraction_50_fixed 0.5

echo "Done. Generate plots separately with:"
echo "  uv run --project ../.. python plot_comparison.py --output-dir results/comparison_plots_fixed"
