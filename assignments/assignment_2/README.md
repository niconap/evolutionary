# Assignment 2 — Phase 1: Minimal EA Template

## Purpose

A minimal, configurable, reproducible evolutionary experiment: evolve the
weights of a feed-forward neural-network controller so that a robot moves
from its spawn point towards a target position in ARIEL/MuJoCo. This is a
Phase-1 smoke-test pipeline, not the final research experiment — it is meant
to be extended (new bodies/worlds, EA A vs EA B, etc.) without rewriting the
EA loop.

Architecture, target position, controller inputs, and fitness are copied
unchanged from [`A2_template_2026.py`](A2_template_2026.py).

## Supported body / world (Phase 1)

- Body: `spider_12`
- World: `CraterTerrainWorld`

These are registered in `SUPPORTED_BODIES` / `SUPPORTED_WORLDS` in
[`components.py`](components.py).

## Configuration

Everything experiment-specific is read from [`config.yaml`](config.yaml)
(see that file for the current values): body, world, population size,
generations, mutation settings, parent/survivor selection, crossover, seed,
and network settings.

Spawn position, target position, and simulation duration are fixed task
constants (not EA configuration parameters we vary) — they are copied from
`A2_template_2026.py` into a `TASK / EXPERIMENT CONSTANTS` section at the top
of `components.py` (`SPAWN_POS`, `TARGET_POSITION`, `SIM_DURATION`).

The EA loop in `a2_experiment.py` never references `spider_12` or
`CraterTerrainWorld` directly — it only calls `create_body(cfg["body"])`
and `create_world(cfg["world"])` from `components.py`.

## Setup

This project depends on the root repository's environment (`ariel`,
MuJoCo, etc.), managed with [uv](https://docs.astral.sh/uv/). From a fresh
clone, run once from the **repository root**:

```bash
git clone https://github.com/AndrzejSzczepura/EvolutionaryComputing2026.git
cd EvolutionaryComputing2026
uv venv
uv sync
```

See the top-level [README.md](../../README.md#installation-and-running) for
details.

## Running a smoke test

Run from this directory (`assignments/assignment_2`), using `uv run` so the
repo's virtual environment is used:

```bash
cd assignments/assignment_2
uv run --project ../.. python a2_experiment.py --config config.yaml --seed 0 --population-size 10 --generations 5
```

If the virtual environment is already activated (`source .venv/bin/activate`
from the repo root), you can drop `uv run --project ../..` and just call
`python a2_experiment.py ...` directly.


## CLI arguments

- `--config` (path to config file, default `config.yaml`)
- `--seed`
- `--population-size`
- `--generations`
- `--mutation-probability`
- `--mutation-sigma`
- `--run-name` (results subdirectory prefix, default `base`)

Any CLI argument overrides the corresponding value in the config file.

## Results

Each run writes to `results/<run-name>_seed_<seed>/`:

- `config.yaml` — the fully resolved configuration used for the run
- `generations.csv` — `generation, evaluations, best_fitness, mean_fitness, std_fitness` (generation 0 = initial population, before any evolution)
- `best_weights.npy` — best genotype (flat NumPy vector) found during the run

An existing results directory is never overwritten; the run raises an error
instead. Use a different `--seed`/`--run-name`, or remove the old directory.

## Adding a new body or world later

1. In `components.py`, write `create_<name>()` returning a `CoreModule`
   (body) or world instance, doing any special setup internally.
2. Register it in `SUPPORTED_BODIES` / `SUPPORTED_WORLDS`.
3. Set `body` / `world` in `config.yaml` (or via future CLI overrides).

The EA loop (`a2_experiment.py`) requires no changes.

## ARIEL-specific assumptions

- Fitness is **lower is better** (Euclidean x/y distance to target), matching
  `A2_template_2026.py`.
- Genotype = a flat NumPy vector encoding `[w1, w2]` of a 2-layer
  `tanh` network; `flatten_weights`/`restore_weights` in `components.py`
  convert between the two representations.
- Network input/output sizes (`len(data.qpos)`, `model.nu`) are discovered
  from the compiled MuJoCo model at runtime, never hardcoded.
- `CraterTerrainWorld` and spawn/target positions are untouched from the
  template; the crater's heightmap may affect spawn-collision correction
  differently than `SimpleFlatWorld` — see `WORKLOG.md` for notes.
