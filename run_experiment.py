"""Phase-controlled exploratory perturbations of the verified memory model."""
import csv
import hashlib
import json
from dataclasses import replace
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Literal

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from model import (ROOT, PARAMETER_FILE, NAMES, Event, Parameters, Perturbation,
                   State, advance, load_parameters, session, simulate)

Phase = Literal["learning", "waiting", "recall", "persistent"]


class StudyConfig(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    training_bouts: int = Field(gt=0)
    training_isi_seconds: float = Field(ge=30)
    wait_seconds: list[float]
    primary_valence: float
    sensitivity_valences: list[float]
    fractional_strengths: list[float]
    tonic_dopamine_hz: list[float]
    phases: list[Phase]
    primary_neuron: Literal["MBON alpha3"]
    parameter_sample_count: int = Field(gt=0, le=10000)
    sample_seed: int
    primary_delay_seconds: float
    reserved_delay_seconds: float
    preserved_immediate_ratio: tuple[float, float]
    impaired_delayed_ratio: float
    minimum_healthy_signal_hz: float


def protocol(config: StudyConfig, wait: float, paired: bool = True, swap: bool = False) -> list[Event]:
    events = session("imaging")
    events[3] = replace(events[3], duration=300.)
    for _ in range(config.training_bouts):
        # The unpaired shock uses 30 s within the last ISI; total odor exposure
        # and duration are identical. Both arms use the same event subdivision.
        events += [
            Event("training", 30., (1., 0.), float(paired), phase="learning"),
            Event("training", config.training_isi_seconds, phase="learning"),
            Event("training", 30., (0., 1.), phase="learning"),
            Event("training", 30., punishment=float(not paired), phase="learning"),
            Event("training", config.training_isi_seconds - 30., phase="learning"),
        ]
    events.append(Event("rest", wait, phase="waiting"))
    if swap:
        events = [replace(event, odor=event.odor[::-1]) for event in events]
    return events


def probe(parameters: Parameters, state: State, wait: float, intervention: Perturbation | None,
          swap: bool = False) -> np.ndarray:
    """Probe each odor from its own clone: no test can alter another test."""
    outputs = []
    for odor in ((1., 0.), (0., 1.)):
        if swap:
            odor = odor[::-1]
        event = Event("probe", 5., odor, phase="recall")
        activity, _ = advance(parameters, state.copy(), event, wait + 5,
                              intervention, update_memory=False)
        outputs.append(activity)
    return np.array(outputs)


def evaluate(parameters: Parameters, config: StudyConfig, wait: float,
             intervention: Perturbation | None, swap: bool = False,
             no_learning: bool = False) -> list[dict]:
    if no_learning:
        parameters = replace(parameters, plasticity=0., punishment_plasticity=0.)
    measured, restored, traces, raw = [], [], [], []
    for paired in (True, False):
        result = simulate(parameters, protocol(config, wait, paired, swap), intervention)
        response = probe(parameters, result.final_state, wait, intervention, swap)
        restoration = probe(parameters, result.final_state, wait, None, swap)
        measured.append(response[1] - response[0])
        restored.append(restoration[1] - restoration[0])
        delta = result.final_state.delta
        traces.append((delta[0] - delta[1]) if swap else (delta[1] - delta[0]))
        raw.append(response)
    return [{
        "neuron": NAMES[index],
        "paired_contrast_hz": float(measured[0][index]),
        "unpaired_contrast_hz": float(measured[1][index]),
        "memory_signal_hz": float(measured[0][index] - measured[1][index]),
        "restored_signal_hz": float(restored[0][index] - restored[1][index]),
        "stored_trace": float(traces[0][index - 3] - traces[1][index - 3]),
        "paired_cs_plus_response_hz": float(raw[0][0, index]),
        "paired_cs_minus_response_hz": float(raw[0][1, index]),
        "unpaired_cs_plus_response_hz": float(raw[1][0, index]),
        "unpaired_cs_minus_response_hz": float(raw[1][1, index]),
    } for index in range(3, 6)]


def conditions(config: StudyConfig) -> list[Perturbation | None]:
    result = [None]
    for mechanism in ("transmission", "plasticity", "tonic_dopamine", "decay_benchmark"):
        strengths = config.tonic_dopamine_hz if mechanism == "tonic_dopamine" else config.fractional_strengths
        result += [Perturbation(mechanism, phase, value) for phase in config.phases for value in strengths]
    return result


def metadata(intervention: Perturbation | None) -> dict:
    return {"mechanism": intervention.mechanism if intervention else "healthy",
            "phase": intervention.phase if intervention else "none",
            "strength": intervention.strength if intervention else 0.}


def write_csv(path: Path, rows: list[dict]):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def classify(rows: list[dict], config: StudyConfig) -> list[dict]:
    primary = [row for row in rows if row["neuron"] == config.primary_neuron
               and row["valence"] == config.primary_valence]
    baseline = {row["wait_seconds"]: row["memory_signal_hz"] for row in primary if row["mechanism"] == "healthy"}
    results = []
    for intervention in conditions(config)[1:]:
        info = metadata(intervention)
        group = {row["wait_seconds"]: row for row in primary
                 if all(row[key] == value for key, value in info.items())}
        ratio = {time: group[time]["memory_signal_hz"] / baseline[time]
                 if abs(baseline[time]) >= config.minimum_healthy_signal_hz else None
                 for time in (0., config.primary_delay_seconds, config.reserved_delay_seconds)}
        early, delayed, reserved = (ratio[t] for t in (0., config.primary_delay_seconds, config.reserved_delay_seconds))
        preserved = early is not None and config.preserved_immediate_ratio[0] <= early <= config.preserved_immediate_ratio[1]
        impaired = delayed is not None and 0 <= delayed <= config.impaired_delayed_ratio
        results.append({**info, "immediate_ratio": early, "delayed_ratio": delayed,
                        "reserved_delay_ratio": reserved, "matches_exploratory_pattern": bool(preserved and impaired),
                        "descriptive_benchmark_only": intervention.mechanism == "decay_benchmark"})
    return results


def plot_results(rows: list[dict], output: Path, config: StudyConfig):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
    primary = [row for row in rows if row["neuron"] == config.primary_neuron
               and row["valence"] == config.primary_valence]
    healthy = sorted([row for row in primary if row["mechanism"] == "healthy"], key=lambda x: x["wait_seconds"])
    fig, axes = plt.subplots(2, 2, figsize=(12, 8.3), constrained_layout=True)
    titles = {"transmission": "Reduced KC → MBON transmission (25%)",
              "plasticity": "Reduced learning-related plasticity (25%)",
              "tonic_dopamine": "Added tonic dopamine drive (+2 Hz)",
              "decay_benchmark": "Shorter decay time constant (25%): benchmark"}
    colors = {"learning": "#277da1", "waiting": "#e76f51", "recall": "#9b5de5", "persistent": "#588157"}
    for ax, mechanism in zip(axes.ravel(), titles):
        ax.plot([r["wait_seconds"] / 60 for r in healthy], [r["memory_signal_hz"] for r in healthy],
                color="#202b36", lw=2.5, marker="o", label="Healthy")
        for phase in config.phases:
            group = sorted([r for r in primary if r["mechanism"] == mechanism and r["phase"] == phase
                            and r["strength"] == (2. if mechanism == "tonic_dopamine" else 0.25)],
                           key=lambda x: x["wait_seconds"])
            ax.plot([r["wait_seconds"] / 60 for r in group], [r["memory_signal_hz"] for r in group],
                    color=colors[phase], marker=".", linestyle="--", label=phase.capitalize())
        ax.set_title(titles[mechanism], fontsize=11)
        ax.set_xscale("symlog", linthresh=5)
        ax.set_xticks([0, 5, 30, 120, 360, 1440], ["0", "5", "30", "120", "360", "1440"])
        ax.set_xlabel("Wait after training protocol (model minutes)")
        ax.set_ylabel("α3 learned response contrast (Hz)")
        ax.grid(alpha=0.15)
        ax.axhline(0, color="grey", lw=0.5)
    axes[0, 0].legend(fontsize=8)
    fig.suptitle("Exploratory memory-circuit perturbations\nNeural response measure; not fly behavior or a calibrated Alzheimer's simulation", fontsize=14)
    fig.savefig(output / "phase_comparison.png", dpi=180)
    fig.savefig(output / "phase_comparison.svg")
    plt.close(fig)


def main():
    output = ROOT / "results"
    output.mkdir(exist_ok=True)
    validation = json.loads((output / "baseline_validation.json").read_text())
    if not validation["passed"]:
        raise RuntimeError("Healthy baseline validation must pass first.")
    config = StudyConfig.model_validate_json((ROOT / "study_config.json").read_text())
    snapshot = config.model_dump_json(indent=2)
    (output / "config_used.json").write_text(snapshot + "\n")
    started = datetime.now(timezone.utc).isoformat()
    print("Configuration saved before perturbation runs; no parameter fitting.", flush=True)
    rows = []
    for valence in [config.primary_valence, *config.sensitivity_valences]:
        parameters = load_parameters(valence=valence)
        for intervention in conditions(config):
            for wait in config.wait_seconds:
                rows.extend({**metadata(intervention), "valence": valence, "wait_seconds": wait, **row}
                            for row in evaluate(parameters, config, wait, intervention))
        print(f"Completed mean-parameter sweep, valence={valence:g}.", flush=True)
    write_csv(output / "phase_sweep.csv", rows)
    classification = classify(rows, config)
    (output / "pattern_screen.json").write_text(json.dumps(classification, indent=2) + "\n")
    plot_results(rows, output, config)

    # Preselected medium-strength conditions; uncertainty is parameter
    # sensitivity across author-supplied draws, not a biological confidence interval.
    selected = [None,
                Perturbation("transmission", "learning", .25),
                Perturbation("transmission", "recall", .25),
                Perturbation("plasticity", "learning", .25),
                Perturbation("tonic_dopamine", "learning", 2.),
                Perturbation("tonic_dopamine", "waiting", 2.),
                Perturbation("decay_benchmark", "waiting", .25),
                Perturbation("decay_benchmark", "persistent", .25)]
    sample_indices = np.random.default_rng(config.sample_seed).choice(10000, config.parameter_sample_count, replace=False)
    samples = []
    for number, sample_index in enumerate(sample_indices):
        parameters = load_parameters(sample=int(sample_index), valence=config.primary_valence)
        for intervention in selected:
            for wait in (0., config.primary_delay_seconds, config.reserved_delay_seconds):
                samples.extend({"parameter_sample": int(sample_index), **metadata(intervention),
                                "wait_seconds": wait, **row}
                               for row in evaluate(parameters, config, wait, intervention))
        if (number + 1) % 20 == 0:
            print(f"Parameter sensitivity: {number + 1}/{len(sample_indices)} draws.", flush=True)
    write_csv(output / "parameter_sensitivity.csv", samples)

    # Controls cover every configured perturbation at both primary times.
    controls = []
    parameters = load_parameters(valence=config.primary_valence)
    for intervention in conditions(config):
        for wait in (0., config.primary_delay_seconds):
            standard = evaluate(parameters, config, wait, intervention)
            swapped = evaluate(parameters, config, wait, intervention, swap=True)
            disabled = evaluate(parameters, config, wait, intervention, no_learning=True)
            for first, second, third in zip(standard, swapped, disabled):
                controls.append({**metadata(intervention), "wait_seconds": wait, "neuron": first["neuron"],
                                 "odor_swap_error_hz": abs(first["memory_signal_hz"] - second["memory_signal_hz"]),
                                 "no_learning_signal_hz": third["memory_signal_hz"]})
    write_csv(output / "controls.csv", controls)
    assert max(row["odor_swap_error_hz"] for row in controls) < 1e-9
    assert max(abs(row["no_learning_signal_hz"]) for row in controls) < 1e-9
    manifest = {
        "started_utc": started, "completed_utc": datetime.now(timezone.utc).isoformat(),
        "source_commit": validation["source_commit"],
        "config_sha256": hashlib.sha256(snapshot.encode()).hexdigest(),
        "parameter_file_sha256": hashlib.sha256(PARAMETER_FILE.read_bytes()).hexdigest(),
        "parameter_sample_indices": sample_indices.tolist(),
        "phase_sweep_readouts": len(rows), "parameter_sensitivity_readouts": len(samples),
        "control_readouts": len(controls),
        "paired_and_unpaired_simulations": (len(rows) + len(samples)) // 3 * 2,
        "max_odor_swap_error_hz": max(row["odor_swap_error_hz"] for row in controls),
        "max_no_learning_signal_hz": max(abs(row["no_learning_signal_hz"]) for row in controls),
        "fitted_to_disease_data": False,
        "scope": "Exploratory reduced-model study; no new biological data or human predictions validated.",
    }
    (output / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == "__main__":
    main()
