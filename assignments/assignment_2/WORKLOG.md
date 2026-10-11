# WORKLOG

## 2026-10-11 / Full parent-pressure study: 10/20/50/80/100% + random search, 10 seeds

### Conditions and settings (unchanged from the corrected 20-vs-50/20-vs-80 work)
body=spider_12, world=CraterTerrainWorld, population_size=20, generations=25,
mutation=gaussian(probability=1.0, sigma=0.1), crossover=disabled,
network(hidden_size=6, init_scale=0.5), elitist survivor selection (full
previous population + full offspring, independent of parent fraction).
Evaluations per run: 20 + 25*20 = 520.

Six conditions, n=10 seeds (0-9) each:
- parent_fraction_10_fixed (new, 10 runs)
- parent_fraction_20_fixed (5 reused + 5 new = 10 runs)
- parent_fraction_50_fixed (5 reused + 5 new = 10 runs)
- parent_fraction_80_fixed (5 reused + 5 new = 10 runs)
- parent_fraction_100_fixed (new, 10 runs)
- random_search_fixed (new, 10 runs) - matched baseline using the same
  genotype representation/init/simulation/fitness and same evaluation
  budget (520/seed); tracks best-so-far fitness per batch
  (`random_search.py`, already existed in the repo and matched the required
  design - not modified).

### Verification before reuse
Before running anything new, the saved `config.yaml` of all 15 existing
`parent_fraction_{20,50,80}_fixed_seed_{0-4}` runs was inspected and
confirmed to match the settings above exactly (population_size=20,
generations=25, mutation probability=1.0/sigma=0.1, parent fraction
0.2/0.5/0.8 respectively, elitist survivor selection, crossover disabled,
hidden_size=6, init_scale=0.5, body/world as above). These 15 runs were
reused unchanged; no mismatch was found.

### New runs executed (45 total = 45*520 = 23,400 new evaluations)
- `run_full_parent_pressure_study.sh` (new): runs, in order, all 10 seeds
  for 10% and 100% parents, all 10 seeds of random search, then seeds 5-9
  for 20%/50%/80% parents (skipping any run whose `generations.csv` already
  exists, erroring on incomplete/partial directories instead of silently
  overwriting).
- Launched in the background (`nohup ... > full_study.log 2>&1 &`) and
  monitored to completion; all 45 runs finished successfully with no
  errors, no partial directories, no manual recovery needed this time.
- Final counts verified: `ls -d <condition>_seed_* | wc -l` = 10 for all
  six conditions.

### New plotting scripts
- `plot_parent_pressure_full.py` (new): parent-fraction-only plots (10/20/
  50/80/100%, no random search) into
  `results/comparison_plots_parent_pressure_full/`:
  `convergence_parent_fractions.png` (best fitness vs. evaluations, mean +/-
  1 std over 10 seeds), `convergence_parent_fractions_by_generation.png`,
  `final_fitness_parent_fractions.png` (boxplot + individual seed points),
  `final_fitness_vs_parent_fraction.png` (mean +/- std vs. parent fraction,
  10/20/50/80/100 on x-axis), `population_mean_parent_fractions.png`
  (kept separate from best-fitness), `parent_selection_summary.csv`
  (condition, n, mean_final_best, std_final_best), and
  `parent_selection_per_seed.csv`.
- `plot_all_with_random.py` (new): all six conditions including random
  search into `results/comparison_plots_all_with_random/`:
  `convergence_all_with_random.png` (best-so-far fitness vs. evaluations),
  `final_fitness_all_with_random.png` (boxplot + seed points),
  `all_conditions_summary.csv`, `all_conditions_per_seed.csv`.
- Neither script touches `comparison_plots_fixed/` (20 vs 50),
  `comparison_plots_20_vs_80/`, or `comparison_plots_all_parent_fractions/`
  (the earlier 3-way, n=5 overview) - all of those remain as they were.

### Results (n=10 per condition)

| condition | n | mean_final_best | std_final_best |
|---|---|---|---|
| 10% parents | 10 | 0.6079 | 0.2460 |
| 20% parents | 10 | 0.4804 | 0.2332 |
| 50% parents | 10 | 0.6295 | 0.2510 |
| 80% parents | 10 | 0.5333 | 0.3265 |
| 100% parents | 10 | 0.6884 | 0.2174 |
| Random search | 10 | 0.4217 | 0.1858 |

Ranking best (lowest mean) to worst: random search (0.4217) < 20% (0.4804)
< 80% (0.5333) < 10% (0.6079) < 50% (0.6295) < 100% (0.6884).

### Trend assessment (per the required checks, no significance test performed/claimed)
- Fitness does NOT worsen monotonically as parent fraction increases:
  20% < 80% < 10% < 50% < 100%; 80% beats both 10% and 50%.
- 10% does NOT improve over 20% (0.6079 vs. 0.4804 - 10% is worse).
- 100% IS worse than 80% (0.6884 vs. 0.5333), consistent with "too little
  selection pressure on the parent side hurts".
- NOT all EA conditions outperform random search: random search has the
  single best (lowest) mean of all six conditions, narrowly ahead of 20%
  parents.
- The differences between conditions (roughly 0.05-0.27 in mean) are small
  relative to the within-condition standard deviations (0.19-0.33) and
  every condition's per-seed values overlap heavily with every other
  condition's (see `parent_selection_per_seed.csv` /
  `all_conditions_per_seed.csv`). No statistical test was run; these
  results should be read as a noisy, inconclusive trend at n=10; they do
  not establish that any parent fraction is reliably better than another
  or than random search under this configuration/budget.

### Current status
All 45 new runs complete, all plots and summaries generated and verified
against expected file names and row counts (n=10 everywhere). Old pairwise
plot directories (`comparison_plots_fixed`, `comparison_plots_20_vs_80`,
`comparison_plots_all_parent_fractions`) are untouched.

### Remaining work / uncertainties
- No statistical significance testing has been performed; if a firmer
  conclusion is needed, a formal test (e.g. Mann-Whitney U per pair) and/or
  more seeds would be required.
- Random search outperforming all EA conditions on mean final fitness is
  worth flagging as a possible sign that 25 generations / population 20 is
  not enough budget for the EA to clearly beat an unguided search here, or
  that the mutation sigma (0.1, unchanged throughout) is not well suited to
  this body/world/network combination - this was explicitly out of scope
  to retune for this task but is a natural next question.

## 2026-10-10 / Additional 20%-vs-80% parent-selection experiment (exploratory)

### Reason
The corrected 20%-vs-50% comparison gave means/stds that overlap
substantially (20%: mean=0.4518, std=0.2908, n=5; 50%: mean=0.4948,
std=0.2676, n=5). To test whether a larger contrast in parent-selection
pressure produces a clearer effect, we add a 20%-vs-80% comparison
(best 4 vs. best 16 of 20 eligible to reproduce) as a separate, additional
experiment. This does NOT modify, overwrite, or replace the 20%-vs-50%
results in `results/comparison_plots_fixed/`.

### EA logic unchanged
Survivor selection remains the corrected version from the previous fix:
full previous population (20) + full offspring population (20) = 40
candidates, keep the best 20, independent of parent fraction. Only
`parent_fraction` differs between conditions (0.2 vs 0.8).

### Existing 20% runs verified and reused
Inspected the resolved `config.yaml` saved in each of
`results/parent_fraction_20_fixed_seed_{0,1,2,3,4}/`: all five confirm
`population_size=20, generations=25, mutation.probability=1.0,
mutation.sigma=0.1, parent_selection.fraction=0.2, survivor_selection.type=
elitist, crossover.enabled=false, network.hidden_size=6,
network.init_scale=0.5, body=spider_12, world=CraterTerrainWorld`, seeds
0-4. These match the required configuration exactly, so they are reused
as-is — not rerun.

### New run names / files
- `run_parent_fraction_80_fixed.sh` (new): runs only the 80% condition
  (`--parent-fraction 0.8`) for seeds 0-4 into
  `results/parent_fraction_80_fixed_seed_<seed>/`. Supports `SEEDS`,
  `POPULATION_SIZE`, `GENERATIONS`, `WORKERS` env var overrides (same
  pattern as `run_parent_selection_comparison_fixed.sh`), defaulting to
  population_size=20, generations=25.
- No new plotting script was needed for the pairwise 20-vs-80 comparison:
  `plot_comparison.py` already accepts `--condition-a/b-prefix` and
  `--output-dir`, so it is reused with `--condition-b-prefix
  parent_fraction_80_fixed --condition-b-label "80% parents" --output-dir
  results/comparison_plots_20_vs_80` (condition A stays the default
  `parent_fraction_20_fixed`).
- `plot_comparison_all.py` (new, optional): three-way 20%/50%/80% overview,
  writing only to `results/comparison_plots_all_parent_fractions/`. Imports
  the plotting/CSV helpers from `plot_comparison.py` rather than
  duplicating them.

### Settings (identical to the 20%-vs-50% experiment, nothing retuned)
- mutation probability: 1.0, mutation sigma: 0.1 (shared, same as before)
- network hidden_size: 6, init_scale: 0.5
- body: spider_12, world: CraterTerrainWorld, crossover: disabled
- survivor_selection: elitist (full population + offspring, unchanged)
- population_size=20, generations=25, seeds=0-4
- parent fractions compared: 0.20 (reused) vs 0.80 (new)
- evaluations per new run: 20 + 25*20 = 520; total NEW evaluations:
  5 seeds x 520 = 2,600 (the 20% side reuses existing runs, 0 new evaluations)

### Current status
- Code/scripts prepared; the five 80% runs were intentionally **not
  executed by the agent** — the user will run them locally with
  `run_parent_fraction_80_fixed.sh`.
- Output directories kept separate from the 20%-vs-50% experiment:
  `results/comparison_plots_20_vs_80/` (primary pairwise result) and
  optionally `results/comparison_plots_all_parent_fractions/` (three-way
  overview). `results/comparison_plots_fixed/` (20% vs 50%) is untouched.

### Remaining work / uncertainties
- Once the user runs the 80% condition and generates the plots, update this
  log with the actual final-fitness numbers and whether 20% vs 80% shows a
  clearer effect than 20% vs 50%.

## 2026-10-10 / Survivor-selection confound fix (parent-selection experiment)

### What the old implementation did
In `a2_experiment.py`, each generation:

```python
combined = parents + offspring
combined_fitnesses = [fitnesses[i] for i in parent_indices] + offspring_fitnesses
survivor_order = np.argsort(combined_fitnesses)[:pop_size]
```

Only the *selected parents* (the top `parent_fraction` of the population)
competed with the offspring for survival — not the full previous population.

### Why this confounded parent selection with survivor selection
With `population_size=20`:
- 20% condition: 4 old individuals + 20 offspring = 24 candidates compete.
- 50% condition: 10 old individuals + 20 offspring = 30 candidates compete.

Changing `parent_fraction` therefore also changed the survivor-selection
pressure (how many old individuals could survive and how large the
candidate pool was), so any fitness difference between the 20% and 50%
conditions could not be attributed to parent selection alone. Any previous
comparison based on `parent_fraction_20` / `parent_fraction_50` run data is
**invalid for that reason** and must not be used to draw conclusions about
parent-selection pressure.

### What was changed
`a2_experiment.py`, inside the generation loop: survivor selection now
always uses the **full previous population + full offspring population**,
independent of `parent_fraction`:

```python
combined = population + offspring
combined_fitnesses = fitnesses + offspring_fitnesses
assert len(combined) == 2 * pop_size
survivor_order = np.argsort(combined_fitnesses)[:pop_size]
population = [combined[i] for i in survivor_order]
fitnesses = [combined_fitnesses[i] for i in survivor_order]
```

`parent_fraction` now only affects `parent_indices`/`parents` (who is
eligible to reproduce), never the survivor pool. The misleading comment
"Elitist survivor selection from parents + offspring" was replaced with
"Elitist survivor selection from the full current population + offspring".
A debug assertion (`assert len(combined) == 2 * pop_size`) was added and
left in place as a cheap, permanent sanity check — it is not conditional
debug logging and has negligible cost.

Offspring creation (`make_offspring`) was not changed: offspring are still
mutated clones of the selected parents (cycling through them), crossover
remains disabled.

### Verified before rerunning
Ran a small debug test (`population_size=10`, `generations=1`, `seed=0`) for
both fractions:
- 20%: 2 parents selected, 10 offspring created, 20 candidates compete
  (`assert` held), best 10 survive.
- 50%: 5 parents selected, 10 offspring created, 20 candidates compete
  (`assert` held), best 10 survive.
Survivor candidate count (`2 * pop_size`) is now independent of
`parent_fraction` in both cases, confirming the fix.

### Obsolete previous results
No `parent_fraction_20_seed_*` / `parent_fraction_50_seed_*` result
directories existed locally at the time of this fix (only a `base_seed_0`
smoke-test directory was present), so there was nothing to archive. If any
such directories exist elsewhere (e.g. from earlier local/cluster runs),
they were generated with the confounded survivor selection above and should
be treated as invalid for the parent-selection comparison.

### New run names
To guarantee old and new results are never mixed, the corrected comparison
uses new run names and a new script:
- `run_parent_selection_comparison_fixed.sh` (new) runs
  `parent_fraction_20_fixed` and `parent_fraction_50_fixed`.
- `run_parent_selection_comparison.sh` (old, confounded) is kept only for
  reference and should not be used for new comparisons.
- `plot_comparison.py` now takes `--condition-a-prefix` /
  `--condition-b-prefix` (defaulting to the `_fixed` names) instead of
  hardcoding `parent_fraction_50` / `parent_fraction_20`, so the old,
  confounded runs cannot be accidentally included in new plots. It also now
  plots best fitness against fitness evaluations (primary x-axis, per the
  assignment's instructions) in addition to generations, overlays individual
  seed points on the final-fitness boxplot, and writes both a per-seed CSV
  (`final_fitness_per_seed.csv`) and an aggregated summary CSV
  (`parent_selection_summary.csv`: `condition, n, mean_final_best,
  std_final_best`).

### Settings for the rerun (unchanged from config.yaml / not independently tuned)
- mutation probability: 1.0
- mutation sigma: 0.1 (same for both conditions, not tuned per condition)
- network hidden_size: 6
- network init_scale: 0.5
- body: spider_12, world: CraterTerrainWorld, crossover: disabled,
  survivor_selection: elitist (now correctly full population + offspring)
- parent fractions compared: 0.20 vs 0.50 (not 0.80 — out of scope for this task)
- population_size=20, generations=25, seeds=0..4 (requested scale, matching
  `slurm_final_comparison.sbatch`'s scale but run locally, not on SLURM)
- evaluations per run: `population_size + generations * population_size`
  = `20 + 25*20` = 520; total across both conditions x 5 seeds = 5,200
  fitness evaluations.

### Current status
- Code fix implemented and verified with a debug run (see above).
- The actual 10 full runs (2 conditions x 5 seeds, population_size=20,
  generations=25) were intentionally **not executed by the agent** — the
  user will run them locally. Commands are in `README.md` under "Parent-selection
  comparison".

### Remaining work / uncertainties
- Once the user runs `run_parent_selection_comparison_fixed.sh` and
  `plot_comparison.py`, update this log with the actual final-fitness
  numbers, mean/std per condition, and a link to
  `results/comparison_plots_fixed/`.
- Decide (after seeing results) whether to extend to 20% vs 80%, or pick a
  different research variable, per the assignment's Phase-1 scope limits.

## 2026-10-10 / Corrected parent-selection results (20% vs 50%)

### What happened
The initial `run_parent_selection_comparison_fixed.sh` invocation was
cancelled partway through. `parent_fraction_20_fixed` completed all 5 seeds;
`parent_fraction_50_fixed` had seeds 0, 1 complete, an empty leftover
`parent_fraction_50_fixed_seed_2/` directory (created but no output written
before cancellation), and seeds 3, 4 missing entirely.

### Recovery
- Removed only the empty `parent_fraction_50_fixed_seed_2/` directory
  (`rmdir`, which fails if non-empty, so no data could be lost) to unblock
  reuse of that run name.
- Reran the 3 missing/incomplete seeds individually with the exact same
  settings as the original invocation: `--config config.yaml
  --population-size 20 --generations 25 --parent-fraction 0.5 --workers 8
  --run-name parent_fraction_50_fixed`, with `--seed 2`, `--seed 3`, and
  `--seed 4`.
- All 10 runs (2 conditions x 5 seeds) now complete with 26 recorded
  generations (0-25) and 520 evaluations each.
- Regenerated plots/summaries: `uv run --project ../.. python
  plot_comparison.py --output-dir results/comparison_plots_fixed`.

### Results
`results/comparison_plots_fixed/parent_selection_summary.csv`:

| condition    | n | mean_final_best | std_final_best |
|--------------|---|------------------|-----------------|
| 20% parents  | 5 | 0.4518           | 0.2908          |
| 50% parents  | 5 | 0.4948           | 0.2676          |

Per-seed final best fitness (`final_fitness_per_seed.csv`):
- 20%: seed0=0.5032, seed1=0.1890, seed2=0.2658, seed3=0.3059, seed4=0.9952
- 50%: seed0=0.1850, seed1=0.5819, seed2=0.4078, seed3=0.9650, seed4=0.3346

Mean final fitness is slightly lower (better) for 20% parents than 50%
parents, but the standard deviations are large relative to the ~0.04
difference in means and the two distributions overlap substantially (both
conditions have one high-fitness/poor-performing seed, ~0.97-1.0). This is
not strong evidence of a consistent advantage either way at n=5 seeds; no
statistical test has been run or is claimed here.

Plots: `results/comparison_plots_fixed/convergence.png`,
`convergence_by_generation.png`, `final_fitness.png` (boxplot with seed
points), `population_mean.png`.

### Current status
Corrected 20%-vs-50% comparison is complete and plotted. Debug artifacts
(`results/debug_fix_20_seed_0`, `results/debug_fix_50_seed_0`,
`results/debug_plots_sanity_check`) remain in `results/` for reference and
do not affect these plots (not matched by the `_fixed` prefixes).

## 2026-10-01 / Config format: JSON -> YAML

### Changes
- Replaced `config.json` with `config.yaml` (same structure/values, YAML
  syntax). `config.json` deleted.
- `a2_experiment.py`: `load_config` now uses `yaml.safe_load`; resolved
  config is saved as `results/<run>/config.yaml` via `yaml.safe_dump`
  (previously JSON). `--config` default changed to `config.yaml`.
- `README.md` updated to reference `config.yaml` throughout.

### Discoveries
- `pyyaml` is importable in the repo's `uv` environment even though it is
  not an explicit top-level dependency in the root `pyproject.toml` (only
  `types-pyyaml` is listed); it is pulled in transitively. Not modified,
  since it already works, but flagging in case it ever stops resolving.

### Commands tested
```bash
cd assignments/assignment_2
uv run --project /home/spatel/EvolutionaryComputing2026 python a2_experiment.py \
    --config config.yaml --seed 0 --population-size 2 --generations 1
```

### Current status
- Smoke test passes with the YAML config; `results/<run>/config.yaml` is
  written correctly.

## 2026-10-01 / Phase 1 cleanup

### Changes
- Removed `spawn_position`, `target_position`, `sim_duration` from
  `config.json` — these are fixed task constants from
  `A2_template_2026.py`, not EA parameters we intend to vary.
- Added a `TASK / EXPERIMENT CONSTANTS` section at the top of
  `components.py` with `SPAWN_POS`, `TARGET_POSITION`, `SIM_DURATION`
  (same values as before); `evaluate_genotype`/`inspect_dimensions` now use
  these constants directly instead of reading them from `cfg`.
- No CLI overrides added for these (intentionally not configurable).
- Updated `README.md` to describe them as fixed constants rather than
  config fields.

## 2026-10-01 / Phase 1

### Changes
- Created `components.py`: body/world factories (`create_body`, `create_world`,
  `SUPPORTED_BODIES`, `SUPPORTED_WORLDS`), NN controller (copied from
  `A2_template_2026.py`), `flatten_weights`/`restore_weights`/
  `create_random_genotype`, `evaluate_genotype` (one full simulation ->
  fitness), `inspect_dimensions` (discovers input/hidden/output sizes).
- Created `config.json`: body, world, population_size, generations, mutation,
  parent_selection, survivor_selection, crossover, seed, spawn_position,
  target_position, sim_duration, network settings.
- Created `a2_experiment.py`: CLI (`--config`, `--seed`,
  `--population-size`, `--generations`, `--mutation-probability`,
  `--mutation-sigma`, `--run-name`), config loading + override, RNG seeding
  (`random` + NumPy), minimal EA loop (init -> evaluate -> rank -> select best
  50% as parents -> mutate clones as offspring (no crossover) -> evaluate
  offspring -> elitist survivor selection from parents+offspring -> record
  stats), results saving (`config.json`, `generations.csv`,
  `best_weights.npy`), no-overwrite protection on `results/<run-name>_seed_<seed>/`.
- Updated `README.md`.

### Discoveries
- `spider_12()` (in
  `ariel.body_phenotypes.robogen_lite.prebuilt_robots.john_set`) takes no
  arguments and returns a `CoreModule`; spawned the same way as `gecko()` in
  the template (`world.spawn(robot.spec, position=..., correct_collision_with_floor=True)`).
- `CraterTerrainWorld` (in `ariel.simulation.environments._crater`, exported
  from `ariel.simulation.environments`) is a dataclass with all-default
  fields — `CraterTerrainWorld()` works with no arguments.
- Controller inputs: `data.qpos` (bare qpos, as in the template).
- Controller outputs: `model.nu` values, scaled to `[-pi/2, pi/2]` via tanh.
- With `spider_12` + `CraterTerrainWorld`: `input_size = len(data.qpos) = 19`,
  `output_size = model.nu = 12`.
- Network architecture: 2-layer, `tanh` activations, `HIDDEN_SIZE = 6`
  (from the template). Total evolved parameters =
  `19*6 + 6*12 = 114 + 72 = 186` for this body/world combination.
- Fitness: Euclidean distance between final (x, y) core position and
  `target_position[:2]`. LOWER IS BETTER. Target = `[2.0, 0.0, 0.1]`,
  spawn = `[0.0, 0.0, 0.1]` (both copied unchanged from the template).
- `simple_runner(model, data, duration=...)` runs one full headless
  evaluation; each evaluation with `sim_duration=15.0` takes a few seconds.
- The project uses `uv`; ariel is importable via
  `uv run --project <repo-root> python ...` (plain `python3 -c "import ariel"`
  did not have the dependency available in this environment).

### Decisions
- Fitness convention fixed as "lower is better" throughout the EA (selection
  picks lowest fitness as "best").
- Offspring are generated by cloning parents (cycling through the selected
  parent set) up to `population_size`, then mutating every clone — crossover
  is disabled per Phase-1 config.
- Elitist survivor pool = selected parents (not full previous population) +
  offspring, keep the `population_size` lowest-fitness individuals. This
  matches "elitist selection from parents + offspring" in the assignment.
- Results directory name: `results/<run-name>_seed_<seed>/`, `run-name`
  defaults to `"base"` (CLI-overridable), to disambiguate future
  multi-body/world runs without redesigning the EA.
- Kept spawn/target positions, controller input/output design, network
  architecture, and fitness exactly as in `A2_template_2026.py` — not
  redesigned in Phase 1.

### Commands tested
```bash
cd assignments/assignment_2
uv run --project /home/spatel/EvolutionaryComputing2026 python a2_experiment.py \
    --config config.json --seed 0 --population-size 10 --generations 5
```
Re-running the exact same command a second time correctly raised
`FileExistsError` instead of overwriting `results/base_seed_0/`.

### Current status
- Smoke test completed successfully end-to-end:
  - config loaded, `spider_12` + `CraterTerrainWorld` selected via config;
  - robot spawned, world compiled (`input_size=19`, `output_size=12`);
  - random genotypes evaluated, fitness varied across genotypes
    (gen 0: best 1.6707, mean 2.0332, std 0.2425);
  - mutation + EA loop ran for 5 generations, best fitness improved
    monotonically across generations (1.6707 -> 1.3726);
  - `results/base_seed_0/config.json`, `generations.csv`, `best_weights.npy`
    all written correctly;
  - no-overwrite protection verified.
- Not yet tested: multiple seeds, longer runs, video/frame rendering of the
  evolved controller, behaviour on an unsupported body/world (error path is
  implemented in `components.py` but not exercised in a test run).

### Remaining work / uncertainties
- `CraterTerrainWorld`'s crater/rugged heightmap may make the fixed spawn
  position `[0.0, 0.0, 0.1]` collide with terrain depending on the terrain's
  random noise seed; `correct_collision_with_floor=True` is passed through,
  consistent with the template, but this has not been stress-tested across
  many seeds.
- Phase 2 scientific decisions (not addressed here, per instructions):
  research question, EA A vs EA B, final target/controller/network/fitness
  design, population size, mutation sigma, stopping criterion, evaluation
  budget.
- To add a new body/world: write `create_<name>()` in `components.py` and
  register it in `SUPPORTED_BODIES`/`SUPPORTED_WORLDS`; no EA changes needed.
