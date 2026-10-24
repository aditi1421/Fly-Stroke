"""Run whole-brain FlyWire v783 simulations with explicit AD-inspired perturbations.

This wraps the published Shiu et al. Brian2 model. Every condition uses the full
public v783 connectivity table; disease changes are exploratory interventions,
not fitted biological parameters. Install the upstream environment first.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from brian2 import second

ROOT = Path(__file__).resolve().parent
UPSTREAM = ROOT / "whole_brain_upstream"
sys.path.insert(0, str(UPSTREAM))
import model as brain_model  # noqa: E402


@dataclass(frozen=True)
class DiseaseCondition:
    name: str
    synapse_scale: float = 1.0
    excitability_scale: float = 1.0


CONDITIONS = (
    DiseaseCondition("healthy"),
    DiseaseCondition("amyloid_synaptic_dysfunction", synapse_scale=0.75),
    DiseaseCondition("amyloid_plus_hyperexcitability", synapse_scale=0.75, excitability_scale=1.15),
)


def build_params(seconds: float, repeats: int, seed: int) -> dict:
    params = dict(brain_model.default_params)
    params.update(t_run=seconds * second, n_run=repeats)
    params["seed"] = seed
    return params


def apply_synaptic_disease(synapses, scale: float):
    if scale != 1.0:
        synapses.w *= scale
    return synapses


def run_condition(condition: DiseaseCondition, config: dict) -> pd.DataFrame:
    params = build_params(config["seconds"], config["repeats"], config["seed"])
    neurons, synapses, spikes = brain_model.create_model(
        config["completeness"], config["connectivity"], params
    )
    apply_synaptic_disease(synapses, condition.synapse_scale)
    exc = [config["stimulus_index"]]
    # Hyperexcitability is represented by a higher sensory drive in the same
    # whole-brain model; it is a controlled perturbation, not a claim about all AD.
    params["r_poi"] *= condition.excitability_scale
    inputs, neurons = brain_model.poi(neurons, exc, [], params)
    net = brain_model.Network(neurons, synapses, spikes, *inputs)
    net.run(duration=params["t_run"])
    spike_trains = brain_model.get_spk_trn(spikes)
    rows = []
    for index in range(len(neurons)):
        times = spike_trains.get(index, np.array([]))
        for repeat in range(config["repeats"]):
            # Brian2 monitor times are grouped by trial only when the model is
            # run repeatedly through run_trial; this direct smoke path reports
            # a single whole-brain run explicitly.
            rows.append({"condition": condition.name, "neuron_index": index,
                         "spike_count": int(len(times)), "rate_hz": float(len(times) / config["seconds"])})
    return pd.DataFrame(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=float, default=0.1)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--stimulus-index", type=int, default=0)
    parser.add_argument("--output", type=Path, default=ROOT / "results/full_brain")
    args = parser.parse_args()
    comp = UPSTREAM / "Completeness_783.csv"
    con = UPSTREAM / "Connectivity_783.parquet"
    if not comp.exists() or not con.exists():
        raise FileNotFoundError("Initialize whole_brain_upstream and fetch the v783 data files first.")
    config = {"seconds": args.seconds, "repeats": args.repeats, "seed": args.seed,
              "stimulus_index": args.stimulus_index, "completeness": comp, "connectivity": con}
    args.output.mkdir(parents=True, exist_ok=True)
    metadata = {"neuron_count": int(sum(1 for _ in open(comp)) - 1),
                "connectivity_file": str(con.relative_to(ROOT)),
                "conditions": [c.__dict__ for c in CONDITIONS],
                "config": {k: str(v.relative_to(ROOT)) if isinstance(v, Path) else v for k, v in config.items()},
                "interpretation": "Exploratory perturbations; no AD parameters fitted; no human clinical inference."}
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    for condition in CONDITIONS:
        frame = run_condition(condition, config)
        frame.to_parquet(args.output / f"{condition.name}.parquet", index=False)
        print(f"completed {condition.name}: {len(frame):,} neuron rows")


if __name__ == "__main__":
    main()
