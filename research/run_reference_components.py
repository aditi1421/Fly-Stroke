"""Run paired KC component assays in the published adfly model.

Replays this project's recorded inputs and lesions in the reference model's
documented adaptation/feedforward-AL variant. No memory or therapy claims.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research/adfly-connectome"
sys.path.insert(0, str(SOURCE / "code"))
from adfly.model import Connectome, Fly, build_brains


def main():
    draws = ROOT / "results/amyloid_components"
    output = ROOT / "results/amyloid_reference_components"
    output.mkdir(parents=True, exist_ok=False)
    configuration = json.loads((draws / "summary.json").read_text())
    cx = Connectome()
    root_cells = pd.read_csv(ROOT / "data/malecns/neurons.csv")
    np.testing.assert_array_equal(root_cells.body_id, cx.neu.bodyId)
    stim = pd.Index(cx.neu.bodyId).get_indexer(configuration["input"]["body_ids"]).astype(np.int32)
    kc = cx.is_kc
    mbon = np.zeros(cx.N, bool)
    mbon[cx.mbon] = True
    populations = {"all": np.ones(cx.N, bool), "KC": kc, "MBON": mbon,
                   "input": np.isin(np.arange(cx.N), stim)}
    edges = pd.read_parquet(ROOT / "data/malecns/connections.parquet")
    target_root = np.flatnonzero(kc[edges.Presynaptic_Index.to_numpy()])
    selected = edges.iloc[target_root]
    keys = selected.Presynaptic_Index.to_numpy(dtype=np.int64) * cx.N + selected.Postsynaptic_Index.to_numpy()
    target_ref = np.flatnonzero(kc[cx.src])
    reference_keys = cx.src[target_ref].astype(np.int64) * cx.N + cx.dst[target_ref]
    position = pd.Index(reference_keys).get_indexer(keys)
    found = position >= 0
    if np.any(selected["Excitatory x Connectivity"].to_numpy()[~found] != 0):
        raise AssertionError("Reference mapping lost a signed KC edge")
    reference_edges = target_ref[position[found]]
    original_contacts = selected.contacts.to_numpy()[found]
    del edges, selected, keys, reference_keys
    br = build_brains(cx, [Fly(fly_id=0, seed=20261024)])
    br.no_refractory(stim)
    br.set_groups(np.arange(cx.N), cx.N)
    baseline_weights = br.wsets[0].copy()
    empty_i, empty_e = np.zeros((1, 0), np.int32), np.zeros((1, 1500, 0), bool)
    rows, checks, provenance = [], [], []
    for trial in range(configuration["repeats"]):
        event_path = draws / f"input_trial_{trial:02d}.npz"
        damage_path = draws / f"damage_trial_{trial:02d}.npz"
        event = np.load(event_path)
        damage = np.load(damage_path)
        np.testing.assert_array_equal(damage["target_edge_indices"], target_root)
        events = np.zeros((1, 1000, len(stim)), bool)
        steps = np.rint((event["seconds"] - .05) / .0001).astype(int)
        events[0, steps, event["indices"]] = True
        assert int(events.sum()) == len(steps)
        dead = np.zeros(cx.N, bool)
        dead[damage["dead_indices"]] = True
        incident = dead[cx.src] | dead[cx.dst]
        retained = damage["retained_contacts"][found]
        provenance.append({"trial": trial, "input_sha256": hashlib.sha256(event_path.read_bytes()).hexdigest(),
                           "damage_sha256": hashlib.sha256(damage_path.read_bytes()).hexdigest(),
                           "injected_events": int(events.sum()), "silenced_KCs": int(dead.sum())})
        baseline_counts = None
        for condition in configuration["conditions"] + [{"name": "full_restoration_check"}]:
            br.reset_state()
            br.wsets[0] = baseline_weights
            br.vth.fill(br.p.v_th)
            if condition.get("excitation", False):
                br.vth[0, kc] -= 1.
            if condition.get("contact_loss", False):
                br.wsets[0, reference_edges] = baseline_weights[reference_edges] * retained / original_contacts
            if condition.get("cell_loss", False):
                br.vth[0, dead] = np.inf
                br.wsets[0, incident] = 0.
            counts = [br.run(500, empty_i, empty_e[:, :500])[0, 0]]
            if condition.get("stimulated", True):
                counts.append(br.run(1000, stim[None, :], events)[0, 0])
            else:
                counts.append(br.run(1000, empty_i, empty_e[:, :1000])[0, 0])
            counts.append(br.run(1500, empty_i, empty_e)[0, 0])
            if condition.get("cell_loss", False):
                assert sum(int(c[dead].sum()) for c in counts) == 0
            assert counts[0].sum() == 0
            if condition["name"] == "baseline":
                baseline_counts = np.stack(counts)
            if condition["name"] == "full_restoration_check":
                np.testing.assert_array_equal(counts, baseline_counts)
                checks.append({"trial": trial, "full_restoration_exactly_matches_baseline": True})
                continue
            for (phase, seconds), c in zip([("pre", .05), ("stimulus", .1), ("washout", .15)], counts):
                for population, mask in populations.items():
                    rows.append({"trial": trial, "condition": condition["name"], "phase": phase,
                        "seconds": seconds, "population": population, "neurons": int(mask.sum()),
                        "spikes": int(c[mask].sum()), "active_neurons": int(np.count_nonzero(c[mask])),
                        "mean_rate_hz_fixed_population": float(c[mask].sum() / seconds / mask.sum())})
            print(json.dumps({"trial": trial, "condition": condition["name"],
                              "CNS_phase_spikes": [int(c.sum()) for c in counts],
                              "MBON_stimulus_spikes": int(counts[1][mbon].sum())}), flush=True)
            pd.DataFrame(rows).to_csv(output / "readouts.csv", index=False)
    report = {"status": "completed", "source": "https://github.com/taehojo/adfly-connectome",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SOURCE, text=True).strip(),
        "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "neurons": cx.N, "repeats": configuration["repeats"], "conditions": configuration["conditions"],
        "KC_edges_mapped": int(found.sum()), "KC_zero_sign_edges_not_in_reference": int((~found).sum()),
        "al_edges_disabled": int(cx.al_edge.sum()), "adaptation_increment_mV": 1.,
        "assay_configuration": configuration, "paired_draws": provenance, "checks": checks,
        "interpretation": "New controlled runs of published engine with its default adaptation/AL assumptions and our shared KC-targeted perturbations. Not reproduction of paper cohorts, fitted disease severity, learned memory, or therapy validation."}
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
