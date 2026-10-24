"""Run the full retained MaleCNS graph using the published Shiu Brian2 dynamics.

This transfers a model to a different animal/connectome. It is a technical
baseline and perturbation experiment, not a validated Alzheimer's simulation.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import time

import brian2 as b2
import numpy as np
import pandas as pd

from prepare_malecns import sha256

ROOT = Path(__file__).resolve().parent


def load_engine():
    path = ROOT / "whole_brain_upstream/model.py"
    spec = importlib.util.spec_from_file_location("shiu_brain_engine", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_trials(data_dir: Path, output: Path, seconds: float, repeats: int,
               seed: int, stimulus_type: str, readout_type: str, rate_hz: float) -> dict:
    if seconds <= 0 or repeats < 1 or rate_hz <= 0:
        raise ValueError("Duration, repeats, and stimulus rate must be positive")
    if not 0 <= seed <= 2**32 - repeats:
        raise ValueError("Seeds must fit uint32")
    cells = pd.read_csv(data_dir / "neurons.csv", index_col="neuron_index")
    if not np.array_equal(cells.index, np.arange(len(cells))):
        raise ValueError("Neuron indices must match graph row order")
    stimulus = np.flatnonzero(cells.cell_type.eq(stimulus_type).to_numpy())
    readout = np.flatnonzero(cells.cell_type.eq(readout_type).to_numpy())
    if not len(stimulus) or not len(readout):
        raise ValueError("Stimulus/readout types must occur in this dataset")
    manifest = json.loads((data_dir / "manifest.json").read_text())
    for filename, expected in manifest["prepared_files"].items():
        if sha256(data_dir / filename) != expected["sha256"]:
            raise ValueError(f"Prepared graph changed: {filename}; rerun preparation")
    # Never silently overwrite an earlier experiment.
    output.mkdir(parents=True, exist_ok=False)
    b2.start_scope()
    b2.prefs.codegen.target = "numpy"
    b2.defaultclock.dt = 0.1 * b2.ms
    engine = load_engine()
    params = dict(engine.default_params)
    params["r_poi"] = rate_hz * b2.Hz
    setup_start = time.perf_counter()
    neurons, synapses, monitor = engine.create_model(
        data_dir / "neurons.csv", data_dir / "connections.parquet", params
    )
    inputs, neurons = engine.poi(neurons, stimulus, [], params)
    network = b2.Network(neurons, synapses, monitor, *inputs)
    network.store("initial")
    setup_seconds = time.perf_counter() - setup_start
    conditions = [("no_stimulus", 1.0, False), ("baseline", 1.0, True),
                  ("weights_75_percent", 0.75, True)]
    summaries = []
    for condition, weight_scale, stimulated in conditions:
        for trial in range(repeats):
            network.restore("initial")
            b2.seed(seed + trial)
            for source in inputs:
                source.active = stimulated
            synapses.w *= weight_scale
            started = time.perf_counter()
            network.run(seconds * b2.second)
            elapsed = time.perf_counter() - started
            counts = np.asarray(monitor.count[:], dtype=np.int64)
            frame = pd.DataFrame({"body_id": cells.body_id.to_numpy(),
                                  "spike_count": counts, "rate_hz": counts / seconds})
            frame.to_parquet(output / f"{condition}_trial_{trial:03d}.parquet", index=False)
            direct = int(counts[stimulus].sum())
            row = {"condition": condition, "trial": trial, "seed": seed + trial,
                   "seconds": seconds, "total_spikes": int(counts.sum()),
                   "active_neurons": int(np.count_nonzero(counts)),
                   "stimulus_neurons": len(stimulus), "stimulus_spikes": direct,
                   "nonstimulus_spikes": int(counts.sum()) - direct,
                   "readout_type": readout_type, "readout_neurons": len(readout),
                   "readout_spikes": int(counts[readout].sum()),
                   "wall_seconds": elapsed}
            summaries.append(row)
            pd.DataFrame(summaries).to_csv(output / "trials.csv", index=False)
            print(json.dumps(row), flush=True)
    revision = subprocess.check_output(
        ["git", "-C", str(ROOT / "whole_brain_upstream"), "rev-parse", "HEAD"], text=True
    ).strip()
    metadata = {
        "status": "completed", "dataset": manifest, "seconds_per_trial": seconds,
        "repeats": repeats, "base_seed": seed, "stimulus_type": stimulus_type,
        "stimulus_body_ids": cells.body_id.iloc[stimulus].tolist(),
        "readout_type": readout_type, "readout_body_ids": cells.body_id.iloc[readout].tolist(),
        "stimulus_hz_per_neuron": rate_hz, "dt_ms": 0.1,
        "conditions": [{"name": name, "weight_scale": scale, "stimulated": active}
                       for name, scale, active in conditions],
        "engine": "Shiu et al. Brian2 model transferred to MaleCNS; parameters not refitted",
        "engine_commit": revision, "engine_sha256": sha256(ROOT / "whole_brain_upstream/model.py"),
        "runner_sha256": sha256(Path(__file__)), "brian2_version": b2.__version__,
        "numpy_version": np.__version__, "backend": "numpy", "setup_wall_seconds": setup_seconds,
        "trial_design": "Reset network to initial state for every trial; distinct seeds per trial, same seed across conditions. Uniform weight scaling includes excitatory and inhibitory connections. No-stimulus control disables external Poisson inputs.",
        "interpretation": "Technical baseline only. LC4 stimulation is an artificial drive, not simulated natural vision. A DNp01 response is a neural readout, not measured escape behavior. No disease calibration, learning, memory, body, amyloid, tau, glia, or human disease inference.",
        "trials": summaries,
    }
    (output / "summary.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data/malecns")
    parser.add_argument("--output", type=Path, default=ROOT / "results/malecns_baseline")
    parser.add_argument("--seconds", type=float, default=0.1)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--stimulus-type", default="LC4")
    parser.add_argument("--readout-type", default="DNp01")
    parser.add_argument("--rate-hz", type=float, default=150)
    args = parser.parse_args()
    run_trials(args.data_dir, args.output, args.seconds, args.repeats,
               args.seed, args.stimulus_type, args.readout_type, args.rate_hz)


if __name__ == "__main__":
    main()
