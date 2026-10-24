"""Paired whole-CNS, KC-targeted amyloid-inspired component assay.

Parameters are exploratory, not fitted adult physiology or a disease clock.
All CNS neurons are instantiated; selected KCs can be functionally silenced.
No learning/retention mechanism is claimed by this circuit assay.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import time

import brian2 as b2
import numpy as np
import pandas as pd

from prepare_malecns import sha256
from run_malecns import ROOT, load_engine


@dataclass(frozen=True)
class Condition:
    name: str
    excitation: bool = False
    contact_loss: bool = False
    cell_loss: bool = False
    stimulated: bool = True


CONDITIONS = (
    Condition("no_input", stimulated=False),
    Condition("baseline"),
    Condition("excitability_only", excitation=True),
    Condition("contact_loss_only", contact_loss=True),
    Condition("cell_silencing_only", cell_loss=True),
    Condition("combined", True, True, True),
    Condition("restore_excitability", False, True, True),
    Condition("restore_contacts", True, False, True),
    Condition("restore_cells", True, True, False),
)
ODOR_A_IDS = [10176, 10208, 10390, 10561, 10613, 10670, 71476, 73492]
PHASES = (("pre", .05), ("stimulus", .1), ("washout", .15))


def input_events(n_inputs, seed, rate_hz=150., dt_seconds=.0001):
    """Bernoulli-per-bin input, exactly replayed for each paired condition."""
    if n_inputs < 1 or not np.isfinite(dt_seconds) or dt_seconds <= 0:
        raise ValueError("Input count and time step must be positive")
    if not np.isfinite(rate_hz) or not 0 <= rate_hz * dt_seconds <= 1:
        raise ValueError("Input probability outside [0,1]")
    rng = np.random.default_rng(seed)
    bins = round(PHASES[1][1] / dt_seconds)
    step, index = np.nonzero(rng.random((bins, n_inputs)) < rate_hz * dt_seconds)
    return index.astype(np.int32), PHASES[0][1] + step * dt_seconds


def damage_draw(contacts, target_edges, target_cells, n_cells, seed,
                contact_loss=.3, cell_loss=.17):
    """One draw reused across all component and restoration conditions."""
    if not (0 <= contact_loss <= 1 and 0 <= cell_loss <= 1):
        raise ValueError("Loss probabilities must lie in [0,1]")
    contact_rng, cell_rng = [np.random.default_rng(s) for s in np.random.SeedSequence(seed).spawn(2)]
    retained = contact_rng.binomial(contacts[target_edges], 1 - contact_loss)
    dead = np.zeros(n_cells, dtype=bool)
    dead[target_cells] = cell_rng.random(len(target_cells)) < cell_loss
    return retained, dead


def run(output: Path, repeats=6, seed=20261024, baseline_only=False):
    if repeats < 1 or not 0 <= seed <= 2**32 - repeats:
        raise ValueError("Invalid repeats or seed")
    directory = ROOT / "data/malecns"
    provenance = json.loads((directory / "manifest.json").read_text())
    for name, value in provenance["prepared_files"].items():
        if sha256(directory / name) != value["sha256"]:
            raise ValueError(f"Input checksum changed: {name}")
    cells = pd.read_csv(directory / "neurons.csv", index_col="neuron_index")
    n = len(cells)
    kc = cells.cell_type.str.startswith("KC", na=False).to_numpy()
    mbon = cells.cell_type.str.startswith("MBON", na=False).to_numpy()
    stim = pd.Index(cells.body_id).get_indexer(ODOR_A_IDS)
    if np.any(stim < 0) or not kc.any() or not mbon.any():
        raise ValueError("Missing expected neuron populations")
    if kc[stim].any() or np.any(kc & mbon):
        raise ValueError("Input/readout must not overlap the affected population")
    output.mkdir(parents=True, exist_ok=False)
    (output / "neurons").mkdir()
    engine = load_engine()
    params = dict(engine.default_params)
    params["eqs"] += "\nthreshold_voltage : volt\nalive : boolean\n"
    params["eq_th"] = "(v > threshold_voltage) and alive"
    b2.start_scope()
    b2.prefs.codegen.target = "numpy"
    b2.defaultclock.dt = .1 * b2.ms
    neurons, synapses, old_monitor = engine.create_model(
        directory / "neurons.csv", directory / "connections.parquet", params)
    neurons.threshold_voltage = params["v_th"]
    neurons.alive = True
    neurons.rfc[stim] = 0 * b2.ms
    monitor = b2.SpikeMonitor(neurons, record=False)
    # No stochastic process inside the network: replay identical explicit events.
    source = b2.SpikeGeneratorGroup(len(stim), [], [] * b2.second)
    drive = b2.Synapses(source, neurons, on_pre="v_post += input_voltage",
                       namespace={"input_voltage": params["w_syn"] * params["f_poi"]})
    drive.connect(i=np.arange(len(stim)), j=stim)
    network = b2.Network(neurons, synapses, monitor, source, drive)
    network.store("initial")
    # Anatomical contact counts include edges with unmodelled transmitter signs.
    contacts = pd.read_parquet(directory / "connections.parquet", columns=["contacts"]).contacts.to_numpy()
    pre, post = np.asarray(synapses.i[:]), np.asarray(synapses.j[:])
    target_edges = np.flatnonzero(kc[pre])
    original_target_weights = np.asarray(synapses.w[target_edges] / b2.mV)
    dynamic = np.asarray(synapses.w[:] / b2.mV) != 0
    populations = {"all": np.ones(n, dtype=bool), "KC": kc, "MBON": mbon,
                   "input": np.isin(np.arange(n), stim)}
    conditions = CONDITIONS[:2] if baseline_only else CONDITIONS
    metadata = {
        "status": "running", "dataset": provenance, "repeats": repeats,
        "input": {"body_ids": ODOR_A_IDS, "rate_hz_per_cell": 150,
                  "dt_ms": .1, "kind": "Recorded Bernoulli events; strong voltage kicks into 8 projection neurons, not physical odors",
                  "selection_source": "https://github.com/taehojo/adfly-connectome (DM1/DM4/VA2 ALPN protocol)"},
        "phases_seconds": dict(PHASES), "conditions": [asdict(x) for x in conditions],
        "target": {"selector": "cell_type prefix KC", "count": int(kc.sum()),
                   "mapping_limit": "Not a validated match to a GAL4 driver expression pattern"},
        "parameters": {"threshold_drop_mV": 1., "outgoing_contact_loss_probability": .3,
                       "cell_silencing_probability": .17,
                       "basis": "Exploratory threshold/contact magnitudes; cell fraction loosely anchored to Ping2015Fig7B: approximately17% fewer labelled MB cells at40days with201y-driven Aβ42, counted in selected confocal sections. Bernoulli silencing of all prefix-selectedKCs is an approximation, not matched-driver cell death, age mapping, or human severity.",
                       "cell_loss_reference": "https://doi.org/10.1371/journal.pgen.1005025.g007"},
        "biological_validation": {"memory_retention": "not_tested", "Kv4_mechanism": "not_tested",
                                  "human_disease": "not_tested"},
        "source": {"runner_sha256": sha256(Path(__file__)),
                   "engine_sha256": sha256(ROOT / "whole_brain_upstream/model.py"),
                   "brian2": b2.__version__, "numpy": np.__version__},
        "scope": "All retained CNS nodes/edges instantiated. No AL wiring removed. Dopamine modulation, plasticity and memory retention absent. Counterfactual restorations are model bookkeeping, not therapies.",
    }
    (output / "summary.json").write_text(json.dumps(metadata, indent=2) + "\n")
    records, burdens, checks = [], [], []
    for trial in range(repeats):
        event_i, event_t = input_events(len(stim), seed + trial)
        event_hash = hashlib.sha256(event_i.tobytes() + event_t.tobytes()).hexdigest()
        np.savez_compressed(output / f"input_trial_{trial:02d}.npz", indices=event_i, seconds=event_t)
        retained, dead = damage_draw(contacts, target_edges, np.flatnonzero(kc), n, seed + trial)
        incident = dead[pre] | dead[post]
        lost_at_target = contacts[target_edges] - retained
        both = int(lost_at_target[incident[target_edges]].sum())
        np.savez_compressed(output / f"damage_trial_{trial:02d}.npz",
                            dead_indices=np.flatnonzero(dead),
                            target_edge_indices=target_edges, retained_contacts=retained)
        for condition in conditions:
            network.restore("initial")
            source.set_spikes(event_i, event_t * b2.second)
            drive.active = condition.stimulated
            if condition.excitation:
                neurons.threshold_voltage[np.flatnonzero(kc)] = params["v_th"] - 1 * b2.mV
            if condition.contact_loss:
                synapses.w[target_edges] = (original_target_weights * retained / contacts[target_edges]) * b2.mV
            if condition.cell_loss:
                neurons.alive = ~dead
                synapses.w[np.flatnonzero(incident)] = 0 * b2.mV
            dead_contacts = int(contacts[incident].sum()) if condition.cell_loss else 0
            thinned_contacts = int(lost_at_target.sum()) if condition.contact_loss else 0
            overlap = both if condition.cell_loss and condition.contact_loss else 0
            dynamic_dead = int(contacts[incident & dynamic].sum()) if condition.cell_loss else 0
            dynamic_thinned = int(lost_at_target[dynamic[target_edges]].sum()) if condition.contact_loss else 0
            dynamic_overlap = int(lost_at_target[incident[target_edges] & dynamic[target_edges]].sum()) if overlap else 0
            burdens.append({"trial": trial, "condition": condition.name,
                "seed": seed + trial, "input_sha256": event_hash,
                "input_event_count": len(event_i) if condition.stimulated else 0,
                "silenced_cells": int(dead.sum()) if condition.cell_loss else 0,
                "silenced_input_cells": int(dead[stim].sum()) if condition.cell_loss else 0,
                "silenced_MBON_cells": int((dead & mbon).sum()) if condition.cell_loss else 0,
                "contacts_lost_to_silencing": dead_contacts,
                "contacts_lost_to_thinning": thinned_contacts,
                "overlap_contacts": overlap,
                "total_contacts_lost": dead_contacts + thinned_contacts - overlap,
                "dynamic_contacts_lost": dynamic_dead + dynamic_thinned - dynamic_overlap})
            previous = np.zeros(n, dtype=np.int64)
            phase_counts = []
            began = time.perf_counter()
            for phase, duration in PHASES:
                network.run(duration * b2.second)
                total = np.asarray(monitor.count[:], dtype=np.int64)
                counts = total - previous
                previous = total.copy()
                phase_counts.append(counts)
                for population, mask in populations.items():
                    live_mask = mask & ~dead if condition.cell_loss else mask
                    records.append({"trial": trial, "condition": condition.name,
                        "phase": phase, "seconds": duration, "population": population,
                        "neurons": int(mask.sum()), "surviving_neurons": int(live_mask.sum()),
                        "spikes": int(counts[mask].sum()), "active_neurons": int(np.count_nonzero(counts[mask])),
                        "mean_rate_hz_fixed_population": float(counts[mask].sum() / duration / mask.sum())})
            if condition.cell_loss:
                silent_ok = int(previous[dead].sum()) == 0
                if not silent_ok:
                    raise AssertionError("Silenced neurons emitted spikes")
            else:
                silent_ok = True
            checks.append({"trial": trial, "condition": condition.name,
                           "silenced_cells_emit_zero": silent_ok,
                           "pre_input_spikes": int(phase_counts[0].sum()),
                           "wall_seconds": time.perf_counter() - began})
            np.savez_compressed(output / "neurons" / f"{condition.name}_{trial:02d}.npz",
                                body_ids=cells.body_id.to_numpy(), phase_counts=np.stack(phase_counts))
            pd.DataFrame(records).to_csv(output / "readouts.csv", index=False)
            pd.DataFrame(burdens).to_csv(output / "damage_burden.csv", index=False)
            print(json.dumps({"trial": trial, "condition": condition.name,
                "phase_spikes": [int(x.sum()) for x in phase_counts],
                "KC_stimulus_spikes": int(phase_counts[1][kc].sum()),
                "MBON_stimulus_spikes": int(phase_counts[1][mbon].sum()),
                "wall_seconds": checks[-1]["wall_seconds"]}), flush=True)
    metadata.update(status="completed", checks=checks)
    (output / "summary.json").write_text(json.dumps(metadata, indent=2) + "\n")
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=6)
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--baseline-only", action="store_true")
    args = parser.parse_args()
    run(args.output, args.repeats, args.seed, args.baseline_only)
