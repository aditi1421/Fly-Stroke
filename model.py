"""Python translation of the Huang/Luo 2024 three-module memory model.

Derived from schnitzer-lab/Luo_Huang_2024_MB_model, commit recorded in README.
Original copyright (C) 2024 Junjie Luo, Cheng Huang, Mark J. Schnitzer.
SPDX-License-Identifier: GPL-3.0-or-later

The unperturbed numerical path preserves the upstream ten-iteration solver,
event-wise adaptation, and piecewise decay, including their conventions.
This is a reduced circuit model, not a full connectome or disease simulator.
"""
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

import numpy as np
from numpy.typing import NDArray
from scipy.io import loadmat

Array = NDArray[np.float64]
ROOT = Path(__file__).resolve().parent
PARAMETER_FILE = ROOT / "upstream/data_and_parameters/Dx_steady_state_nonlinear_3_27-Mar-2023_3modules.mat"
NAMES = ("DAN gamma1", "DAN alpha2", "DAN alpha3", "MBON gamma1", "MBON alpha2", "MBON alpha3")
PUNISHMENT = np.array([27.85, 0, 11.38, 0, 0, 0.])
BASELINE = np.array([0, 0, 0, 35.2, 9.0, 11.2])
CEILING = BASELINE[3:] + np.array([36.46, 8.9, 19.96])


@dataclass(frozen=True)
class Parameters:
    kc_weights: Array
    plasticity: float
    punishment_plasticity: float
    recurrent: Array
    decay: Array
    adaptation_recovery: float


@dataclass(frozen=True)
class Event:
    name: str
    duration: float
    odor: tuple[float, float] = (0., 0.)
    punishment: float = 0.
    imaging: int = 0
    phase: str = "baseline"


@dataclass
class State:
    adaptation: Array
    delta: Array

    def copy(self):
        return State(self.adaptation.copy(), self.delta.copy())


@dataclass
class Simulation:
    imaging: Array
    activity: Array
    weights: Array
    final_state: State


@dataclass(frozen=True)
class Perturbation:
    mechanism: Literal["transmission", "plasticity", "tonic_dopamine", "decay_benchmark"]
    phase: Literal["learning", "waiting", "recall", "persistent"]
    strength: float

    def active(self, phase: str) -> bool:
        return phase != "baseline" and (self.phase == phase or self.phase == "persistent")


def load_parameters(sample: int | None = None, valence: float | None = 0.) -> Parameters:
    data = loadmat(PARAMETER_FILE)
    vector = data["para_mu"].ravel() if sample is None else data["para_rand"][:, sample]
    matrices = []
    offset = 0
    for bounds in data["mat_lu_cell"].ravel(order="F"):
        values = bounds[:, :, 0].copy().ravel(order="F")
        mask = (bounds[:, :, 0] != bounds[:, :, 1]).ravel(order="F")
        count = int(mask.sum())
        values[mask] = vector[offset:offset + count]
        offset += count
        matrices.append(values.reshape(bounds.shape[:2], order="F"))
    assert offset == vector.size
    recurrent = matrices[3]
    if valence is None:
        kc = matrices[0][0, :6]
    else:
        firing = np.array([valence, valence, valence, 31.6, 5.8, 17.8])
        kc = (np.eye(6) - recurrent.T) @ firing * (2 / (1 + np.exp(-0.05 * 5)))
    return Parameters(kc, float(matrices[1][0, 0]), float(matrices[2][0, 0]),
                      recurrent, matrices[4].ravel(), float(matrices[5][0, 0]))


def session(name: str, repeats: int = 1, isi: float = 120., phase: str = "baseline") -> list[Event]:
    duration = 30. if name == "training" else 5.
    punishment = 1. if name == "training" else 0.
    imaging = name in ("imaging", "extinction")
    return [event for _ in range(repeats) for event in (
        Event(name, duration, (1., 0.), punishment, 1 if imaging else 0, phase),
        Event(name, isi, phase=phase),
        Event(name, duration, (0., 1.), 0., 2 if imaging else 0, phase),
        Event(name, isi, phase=phase),
    )]


def figure5d_protocol(delay_seconds: float) -> list[Event]:
    events = session("imaging") + session("training", isi=135., phase="learning")
    events[3] = replace(events[3], duration=300.)
    events += [Event("rest", delay_seconds - 135., phase="waiting")]
    events += session("imaging", phase="recall")
    return events


def solve_activity(parameters: Parameters, kc_input: Array, punishment: float, weights: Array,
                   tonic_dopamine: float = 0.) -> Array:
    drive = weights.T @ kc_input + PUNISHMENT * punishment
    drive[:3] += tonic_dopamine
    value = np.linalg.solve(np.eye(6) - parameters.recurrent, drive)
    for _ in range(10):
        value = drive + BASELINE + parameters.recurrent.T @ value
        value[3:] = np.clip(value[3:], 0, CEILING)
        value -= BASELINE
    return value


def decay_factors(parameters: Parameters, duration: float, elapsed: float) -> Array:
    """Match the upstream 3-hour switch, even for an event crossing it."""
    early = parameters.decay[[0, 1, 1]]
    late = parameters.decay[[0, 2, 2]]
    if elapsed <= 10800:
        return np.exp(-duration / early)
    if 10800 > elapsed - duration:
        before = 10800 - (elapsed - duration)
        return np.exp(-before / early - (duration - before) / late)
    return np.exp(-duration / late)


def advance(parameters: Parameters, state: State, event: Event, elapsed: float,
            perturbation: Perturbation | None = None, update_memory: bool = True) -> tuple[Array, Array]:
    """One source-model event, with explicitly exploratory intervention hooks."""
    initial = np.tile(parameters.kc_weights, (2, 1))
    weights = initial.copy()
    weights[:, 3:] += state.delta
    transmission, plasticity, tonic = 1., 1., 0.
    decay_parameters = parameters
    if perturbation is not None and perturbation.active(event.phase):
        strength = perturbation.strength
        if perturbation.mechanism == "transmission":
            transmission = 1 - strength
        elif perturbation.mechanism == "plasticity":
            plasticity = 1 - strength
        elif perturbation.mechanism == "tonic_dopamine":
            tonic = strength
        elif perturbation.mechanism == "decay_benchmark":
            decay_parameters = replace(parameters, decay=parameters.decay * (1 - strength))
    effective = weights.copy()
    effective[:, 3:] *= transmission
    odor = np.array(event.odor)
    end = state.adaptation * np.exp(-0.05 * event.duration * odor)
    end = 1 - (1 - end) * np.exp(-event.duration / parameters.adaptation_recovery)
    kc_input = (state.adaptation + end) / 2 * odor
    state.adaptation = end
    activity = solve_activity(parameters, kc_input, event.punishment, effective, tonic)
    if update_memory:
        teaching = parameters.plasticity * (
            effective[:, :3].T @ kc_input + parameters.recurrent[3:, :3].T @ activity[3:] + tonic
        ) + parameters.punishment_plasticity * PUNISHMENT[:3] * event.punishment
        state.delta += plasticity * np.outer(kc_input, teaching) * event.duration / 90.
        state.delta *= decay_factors(decay_parameters, event.duration, elapsed)
    weights = initial.copy()
    weights[:, 3:] += state.delta
    return activity, weights


def simulate(parameters: Parameters, events: list[Event],
             perturbation: Perturbation | None = None) -> Simulation:
    state = State(np.ones(2), np.zeros((2, 3)))
    imaging = np.zeros((6, 2, sum(event.imaging == 1 for event in events)))
    imaging_index = 0
    activities, weight_history = [], []
    last_training = max((i for i, event in enumerate(events) if event.name == "training"), default=-1)
    elapsed = 0.
    for index, event in enumerate(events):
        if index > last_training:
            elapsed += event.duration
        activity, weights = advance(parameters, state, event, elapsed, perturbation)
        if event.imaging:
            imaging[:, event.imaging - 1, imaging_index] = activity
            imaging_index += event.imaging == 2
        activities.append(activity)
        weight_history.append(weights.copy())
    return Simulation(imaging, np.array(activities), np.array(weight_history), state)
