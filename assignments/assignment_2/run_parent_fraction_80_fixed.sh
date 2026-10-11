#!/usr/bin/env bash
# Exploratory 20%-vs-80% parent-selection comparison (stronger contrast than
# the corrected 20%-vs-50% comparison in run_parent_selection_comparison_fixed.sh).
#
# Only runs the 80% condition: the existing parent_fraction_20_fixed_seed_*
# runs are reused as-is (verified to match this exact configuration) and are
# never touched or rerun by this script.
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Override these without editing the script, for example:
# SEEDS="0 1 2 3 4" POPULATION_SIZE=20 GENERATIONS=25 WORKERS=8 ./run_parent_fraction_80_fixed.sh
SEEDS=${SEEDS:-"0 1 2 3 4"}
POPULATION_SIZE=${POPULATION_SIZE:-20}
GENERATIONS=${GENERATIONS:-25}
WORKERS=${WORKERS:-$(nproc)}

for seed in $SEEDS; do
    uv run --project ../.. python a2_experiment.py \
        --config config.yaml \
        --seed "$seed" \
        --population-size "$POPULATION_SIZE" \
        --generations "$GENERATIONS" \
        --parent-fraction 0.8 \
        --workers "$WORKERS" \
        --run-name parent_fraction_80_fixed
done

echo "Done. Generate plots separately with:"
echo "  uv run --project ../.. python plot_comparison.py \\"
echo "    --condition-b-prefix parent_fraction_80_fixed --condition-b-label '80% parents' \\"
echo "    --output-dir results/comparison_plots_20_vs_80"
