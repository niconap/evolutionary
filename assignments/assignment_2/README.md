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

## Parent-selection comparison

> **Note:** `run_parent_selection_comparison.sh` (and its `parent_fraction_20`
> / `parent_fraction_50` results) used a confounded survivor-selection
> implementation and is kept only for reference — do not use it for new
> comparisons. Use `run_parent_selection_comparison_fixed.sh` below instead.
> See `WORKLOG.md` ("Survivor-selection confound fix") for details.

Run the corrected matched 20%-versus-50% parent-selection experiment with
five seeds and plot the results:

```bash
./run_parent_selection_comparison_fixed.sh
```

The defaults are five seeds (0-4), population size 20, 25 generations, and
one worker per available CPU reported by `nproc`. Override them without
editing the script, for example:

```bash
SEEDS="0 1 2 3 4" POPULATION_SIZE=20 GENERATIONS=25 WORKERS=8 \
  ./run_parent_selection_comparison_fixed.sh
```

Results are written to `results/parent_fraction_20_fixed_seed_<seed>/` and
`results/parent_fraction_50_fixed_seed_<seed>/`. Generate the plots and
numerical summary separately (so you can re-plot without rerunning):

```bash
uv run --project ../.. python plot_comparison.py --output-dir results/comparison_plots_fixed
```

This writes to `results/comparison_plots_fixed/`:

- `convergence.png` — best fitness vs. fitness evaluations, mean ± 1 std
  across seeds (main comparison graph)
- `convergence_by_generation.png` — same, by generation (secondary view)
- `final_fitness.png` — boxplot of final best fitness per condition, with
  individual seed values overlaid as points
- `population_mean.png` — population mean fitness convergence (optional,
  kept separate from the best-fitness graph)
- `final_fitness_per_seed.csv` — one row per (condition, seed)
- `parent_selection_summary.csv` — `condition, n, mean_final_best, std_final_best`

`plot_comparison.py` only reads the `_fixed` run-name prefixes by default, so
the old confounded runs can never be mixed into these plots.

`WORKERS` controls the number of CPU processes used for independent fitness
evaluations. Start with the number of physical CPU cores, or slightly fewer
if the computer remains busy with other work.

## Parent-selection comparison: 20% vs 80% (stronger contrast)

Exploratory follow-up to the 20%-vs-50% comparison above, testing a larger
difference in parent-selection pressure. All other settings are identical
(population size 20, 25 generations, seeds 0-4, mutation probability 1.0 /
sigma 0.1, hidden size 6, init scale 0.5, crossover disabled, corrected
elitist survivor selection: full previous population + offspring). The
existing `parent_fraction_20_fixed_seed_*` runs are reused as-is; only the
80% condition needs to be run:

```bash
./run_parent_fraction_80_fixed.sh
```

Override settings the same way as above, e.g.
`SEEDS="0 1 2 3 4" POPULATION_SIZE=20 GENERATIONS=25 WORKERS=8 ./run_parent_fraction_80_fixed.sh`.
Results are written to `results/parent_fraction_80_fixed_seed_<seed>/`.

Generate the dedicated 20%-vs-80% plots/summary (own directory, does not
touch `comparison_plots_fixed/`):

```bash
uv run --project ../.. python plot_comparison.py \
  --condition-b-prefix parent_fraction_80_fixed --condition-b-label "80% parents" \
  --output-dir results/comparison_plots_20_vs_80
```

This writes the same set of files as above (`convergence.png`,
`convergence_by_generation.png`, `final_fitness.png`, `population_mean.png`,
`final_fitness_per_seed.csv`, `parent_selection_summary.csv`) into
`results/comparison_plots_20_vs_80/`, containing only the 20%/80% conditions.

Optionally, generate a three-way 20%/50%/80% overview (separate folder,
does not replace either pairwise comparison):

```bash
uv run --project ../.. python plot_comparison_all.py --output-dir results/comparison_plots_all_parent_fractions
```

## Full parent-pressure study: 10/20/50/80/100% + random search (10 seeds)

The complete study extends the above to five parent fractions (10/20/50/80/
100%) and a matched random-search baseline, all at 10 seeds (0-9), reusing
the valid seeds 0-4 from the 20/50/80% runs above. All other settings are
unchanged (population size 20, 25 generations, mutation probability 1.0 /
sigma 0.1, hidden size 6, init scale 0.5, crossover disabled, corrected
elitist survivor selection).

```bash
./run_full_parent_pressure_study.sh
```

This skips any run whose `generations.csv` already exists, so it is safe to
re-run after an interruption. Then generate the two sets of plots:

```bash
uv run --project ../.. python plot_parent_pressure_full.py
uv run --project ../.. python plot_all_with_random.py
```

`plot_parent_pressure_full.py` writes to
`results/comparison_plots_parent_pressure_full/` (10/20/50/80/100% only, no
random search): `convergence_parent_fractions.png`,
`convergence_parent_fractions_by_generation.png`,
`final_fitness_parent_fractions.png`,
`final_fitness_vs_parent_fraction.png` (mean +/- std per parent fraction),
`population_mean_parent_fractions.png`, `parent_selection_summary.csv`,
`parent_selection_per_seed.csv`.

`plot_all_with_random.py` writes to
`results/comparison_plots_all_with_random/` (all six conditions):
`convergence_all_with_random.png`, `final_fitness_all_with_random.png`,
`all_conditions_summary.csv`, `all_conditions_per_seed.csv`.

See `WORKLOG.md` ("Full parent-pressure study") for the numerical results
and trend assessment.

## EA versus random-search baseline

For a stronger comparison, run the evolutionary algorithm against random
search using the same seeds and evaluation budget:

```bash
./run_ea_vs_random.sh
```

This compares the 20%-parent EA with a baseline that samples every controller
independently and keeps the best controller seen so far. Results are plotted
against total fitness evaluations in `results/ea_vs_random_plots/`.

## Automatic parameter tuning

Run a pilot grid search over parent fraction and mutation sigma:

```bash
./run_auto_tuning.sh
```

The default sweep uses three seeds, population size 10, and five generations.
It writes per-run data, a ranked `tuning_summary.csv`, all-run data in
`tuning_runs.csv`, and `tuning_heatmap.png` to `results/tuning/`. Override the
pilot settings with environment variables, for example:

```bash
SEEDS="0,1,2,3,4" POPULATION_SIZE=20 GENERATIONS=25 WORKERS=8 \
  ./run_auto_tuning.sh
```

Use the best pilot configuration only as a candidate. Confirm it on fresh
seeds before using it as the final reported EA configuration.

## SLURM tuning on Rome

Submit one array task per parameter combination and seed on the `rome`
partition:

```bash
./submit_slurm_tuning.sh
```

The default is a 3 x 3 x 3 sweep, with 8 CPUs per array task and at most 9
array tasks running concurrently. Each task uses its allocated CPUs for
parallel fitness evaluation. A dependent collector job writes the ranked
results and heatmap to `results/slurm_tuning/`.

The submission wrapper accepts the same controls without editing the script:

```bash
PARENT_FRACTIONS="0.1,0.2,0.5" \
MUTATION_SIGMAS="0.03,0.05,0.1" \
SEEDS="10,11,12,13,14" \
POPULATION_SIZE=20 GENERATIONS=25 MAX_CONCURRENT=12 \
./submit_slurm_tuning.sh
```

Set `SBATCH_ACCOUNT` if the cluster requires an account allocation. Adjust
`--cpus-per-task`, memory, and wall time in `slurm_tune.sbatch` to match your
Rome allocation policy.

The submission command schedules the complete chain: tuning array, tuning
collector, fresh final 20%-versus-50% parent-retention and matched-random
array, and finally
`plot_results.sbatch`. The plotting job writes publication-ready PDF and
300-dpi PNG figures to
`results/report_plots/`, including convergence curves with across-seed spread,
final-fitness distributions, parent-retention comparison, and a tuning
heatmap. The final comparison uses a shared mutation sigma, controlled by
`FINAL_MUTATION_SIGMA`. By default, the collector selects the mutation sigma
with the best mean performance across all parent fractions. To rerun plotting
manually after results already exist:

```bash
sbatch --export=ALL,PROJECT_DIR="$PWD/../.." plot_results.sbatch
```


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
