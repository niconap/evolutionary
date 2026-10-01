"""ARIEL-specific construction helpers: body/world factories, controller, fitness.

Isolates everything that depends on `ariel` APIs so that `a2_experiment.py`
(the EA loop) never has to know how a body or world is built. To add a new
body/world later, write a `create_*` function and register it in
`SUPPORTED_BODIES` / `SUPPORTED_WORLDS` below - the EA loop does not change.
"""

from __future__ import annotations

from typing import Any, Callable

import mujoco as mj
import numpy as np
import numpy.typing as npt

from ariel.body_phenotypes.robogen_lite.modules.core import CoreModule
from ariel.body_phenotypes.robogen_lite.prebuilt_robots.john_set import spider_12
from ariel.simulation.environments import CraterTerrainWorld
from ariel.simulation.environments._compound_world import CompoundWorld
from ariel.utils.runners import simple_runner

# --- TASK / EXPERIMENT CONSTANTS --- #
# Copied from A2_template_2026.py - not experiment parameters we vary.
SPAWN_POS: list[float] = [0.0, 0.0, 0.1]
TARGET_POSITION: list[float] = [2.0, 0.0, 0.1]
SIM_DURATION: float = 15.0

# ============================================================================ #
#  BODY FACTORY
# ============================================================================ #


def create_spider_12() -> CoreModule:
    """Build the spider_12 prebuilt robot body."""
    return spider_12()


SUPPORTED_BODIES: dict[str, Callable[[], CoreModule]] = {
    "spider_12": create_spider_12,
}


def create_body(name: str) -> CoreModule:
    """Build a robot body by its configuration name."""
    try:
        factory = SUPPORTED_BODIES[name]
    except KeyError as exc:
        supported = ", ".join(sorted(SUPPORTED_BODIES))
        msg = f"Unsupported body '{name}'.\nCurrently supported bodies: {supported}"
        raise ValueError(msg) from exc
    return factory()


# ============================================================================ #
#  WORLD FACTORY
# ============================================================================ #


def create_crater_world() -> CompoundWorld:
    """Build the CraterTerrainWorld environment with default parameters."""
    return CraterTerrainWorld()


SUPPORTED_WORLDS: dict[str, Callable[[], CompoundWorld]] = {
    "CraterTerrainWorld": create_crater_world,
}


def create_world(name: str) -> CompoundWorld:
    """Build a world by its configuration name."""
    try:
        factory = SUPPORTED_WORLDS[name]
    except KeyError as exc:
        supported = ", ".join(sorted(SUPPORTED_WORLDS))
        msg = f"Unsupported world '{name}'.\nCurrently supported worlds: {supported}"
        raise ValueError(msg) from exc
    return factory()


# ============================================================================ #
#  NEURAL-NETWORK CONTROLLER (architecture copied from A2_template_2026.py)
# ============================================================================ #


def network_shapes(
    input_size: int,
    hidden_size: int,
    output_size: int,
) -> list[tuple[int, int]]:
    """Return the (rows, cols) shape of each weight matrix, in order."""
    return [(input_size, hidden_size), (hidden_size, output_size)]


def num_weights(input_size: int, hidden_size: int, output_size: int) -> int:
    """Total number of evolved parameters for the given architecture."""
    return sum(r * c for r, c in network_shapes(input_size, hidden_size, output_size))


def flatten_weights(weights: list[npt.NDArray[np.float64]]) -> npt.NDArray[np.float64]:
    """Flatten [w1, w2] layer matrices into a single 1-D genotype vector."""
    return np.concatenate([w.ravel() for w in weights])


def restore_weights(
    genotype: npt.NDArray[np.float64],
    input_size: int,
    hidden_size: int,
    output_size: int,
) -> list[npt.NDArray[np.float64]]:
    """Reshape a flat genotype vector back into [w1, w2] layer matrices."""
    shapes = network_shapes(input_size, hidden_size, output_size)
    weights = []
    offset = 0
    for rows, cols in shapes:
        size = rows * cols
        chunk = genotype[offset : offset + size]
        weights.append(chunk.reshape(rows, cols))
        offset += size
    return weights


def create_random_genotype(
    rng: np.random.Generator,
    input_size: int,
    hidden_size: int,
    output_size: int,
    scale: float = 0.5,
) -> npt.NDArray[np.float64]:
    """Draw a random flat genotype vector (same init as A2_template_2026.py)."""
    n = num_weights(input_size, hidden_size, output_size)
    return rng.normal(scale=scale, size=n)


def nn_controller(
    data: mj.MjData,
    weights: list[npt.NDArray[np.float64]],
) -> npt.NDArray[np.float64]:
    """Map robot state to hinge commands: in -> hidden -> actions.

    Identical architecture/behaviour to `nn_controller` in A2_template_2026.py.
    """
    w1, w2 = weights
    inputs = data.qpos
    layer1 = np.tanh(inputs @ w1)
    outputs = np.tanh(layer1 @ w2)
    return outputs * (np.pi / 2)


# ============================================================================ #
#  POSITION AND FITNESS (copied from A2_template_2026.py)
# ============================================================================ #


def get_core_position(data: mj.MjData) -> npt.NDArray[np.float64]:
    """Return the robot core's current (x, y, z) world position."""
    return np.asarray(data.qpos[0:3]).copy()


def fitness_function(
    final_position: npt.NDArray[np.float64],
    target_position: list[float],
) -> float:
    """Euclidean distance (x, y only) between final position and target. Lower is better."""
    target = np.asarray(target_position)
    return float(np.linalg.norm(final_position[:2] - target[:2]))


# ============================================================================ #
#  ONE EVALUATION
# ============================================================================ #


def evaluate_genotype(
    genotype: npt.NDArray[np.float64],
    cfg: dict[str, Any],
) -> float:
    """Build body+world, run one headless simulation with `genotype`, return fitness."""
    mj.set_mjcb_control(None)

    body = create_body(cfg["body"])
    world = create_world(cfg["world"])

    world.spawn(
        body.spec,
        position=SPAWN_POS,
        correct_collision_with_floor=True,
    )

    model = world.spec.compile()
    data = mj.MjData(model)

    mj.mj_resetData(model, data)
    mj.mj_forward(model, data)

    input_size = len(data.qpos)
    output_size = model.nu
    hidden_size = cfg["network"]["hidden_size"]
    weights = restore_weights(genotype, input_size, hidden_size, output_size)

    def control_callback(m: mj.MjModel, d: mj.MjData) -> None:
        d.ctrl[:] = nn_controller(d, weights)

    mj.set_mjcb_control(control_callback)
    simple_runner(model, data, duration=SIM_DURATION)
    mj.set_mjcb_control(None)

    final_position = get_core_position(data)
    return fitness_function(final_position, TARGET_POSITION)


def inspect_dimensions(cfg: dict[str, Any]) -> tuple[int, int, int]:
    """Build body+world once to discover (input_size, hidden_size, output_size)."""
    mj.set_mjcb_control(None)
    body = create_body(cfg["body"])
    world = create_world(cfg["world"])
    world.spawn(
        body.spec,
        position=SPAWN_POS,
        correct_collision_with_floor=True,
    )
    model = world.spec.compile()
    data = mj.MjData(model)
    input_size = len(data.qpos)
    output_size = model.nu
    hidden_size = cfg["network"]["hidden_size"]
    return input_size, hidden_size, output_size
