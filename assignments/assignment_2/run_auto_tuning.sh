#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

uv run --project ../.. python auto_tune.py \
    --seeds "${SEEDS:-0,1,2}" \
    --parent-fractions "${PARENT_FRACTIONS:-0.2,0.5,0.8}" \
    --mutation-sigmas "${MUTATION_SIGMAS:-0.05,0.1,0.2}" \
    --population-size "${POPULATION_SIZE:-10}" \
    --generations "${GENERATIONS:-5}" \
    --workers "${WORKERS:-$(nproc)}"