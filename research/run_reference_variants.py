"""Diagnose effects of Jo model extensions with exactly replayed odor input.

This is a new controlled comparison in the external numerical engine, not a
reproduction of a published biological result. The full signed graph and
neuron set are retained in the first two variants.
"""
from pathlib import Path
import gc
import hashlib
import json
import subprocess
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research/adfly-connectome"
OUT = ROOT / "results/adfly_reference"
sys.path.insert(0, str(SOURCE / "code"))
from adfly.lif import Brains
from adfly.model import Connectome, ODORS


def main():
    started = time.monotonic()
    cx = Connectome()
    stim = cx.upn(ODORS["A"]).astype(np.int32)
    seed = 20261024
    input_path = ROOT / "results/amyloid_native_graph_check/input_trial_00.npz"
    source_events = np.load(input_path)
    source_ids = [10176, 10208, 10390, 10561, 10613, 10670, 71476, 73492]
    assert cx.neu.bodyId.iloc[stim].astype(int).tolist() == source_ids
    bins = np.rint((source_events["seconds"] - .05) / .0001).astype(int)
    assert np.all((bins >= 0) & (bins < 1000))
    events = np.zeros((1, 1000, len(stim)), dtype=bool)
    events[0, bins, source_events["indices"]] = True
    assert events.sum() == len(source_events["indices"])
    masks = {"KC": cx.is_kc, "MBON": np.isin(np.arange(cx.N), cx.mbon), "stimulated": np.isin(np.arange(cx.N), stim)}
    records, arrays = [], {"stimulus_events": events, "stimulus_indices": stim}
    for name, adapt, cut_al in [("native_signed_graph", False, False), ("adaptation_only", True, False), ("reference_default", True, True)]:
        begin = time.monotonic()
        br = Brains(1, pack=cx.pack)
        if adapt:
            br.da[:, ~cx.sensory] = 1.0
        if cut_al:
            br.wsets[:, cx.al_edge] = 0.0
        br.no_refractory(stim)
        br.set_groups(np.arange(cx.N), cx.N)
        drive = br.run(1000, stim[None, :], events, bin_steps=100)[0]
        wash = br.run(1500, np.zeros((1, 0), np.int32), np.zeros((1, 1500, 0), bool), bin_steps=100)[0]
        record = {"variant": name, "adaptation_increment_mV": 1.0 if adapt else 0.0, "al_connections_zeroed": int(cx.al_edge.sum()) if cut_al else 0, "elapsed_seconds": round(time.monotonic() - begin, 3)}
        for label, counts in [("driven_100ms", drive), ("poststimulus_150ms", wash)]:
            totals = counts.sum(axis=0)
            record[label] = {"spikes": int(totals.sum()), "active_neurons": int(np.count_nonzero(totals)), "spikes_per_10ms": counts.sum(axis=1).astype(int).tolist(), **{key + "_spikes": int(totals[mask].sum()) for key, mask in masks.items()}}
            record[label]["network_spikes_per_second"] = float(totals.sum() / (len(counts) * .01))
            record[label]["spikes_per_50ms"] = counts.sum(axis=1).reshape(-1, 5).sum(axis=1).astype(int).tolist()
            record[label]["network_spikes_per_second_per_50ms"] = (counts.sum(axis=1).reshape(-1, 5).sum(axis=1) / .05).tolist()
            arrays[name + "_" + label + "_per_neuron_counts"] = totals
        records.append(record)
        print(json.dumps(record), flush=True)
        del br
        gc.collect()
    report = {
        "purpose": "Diagnose healthy-baseline sensitivity to graph deletion and adaptation, using identical external events in every condition.",
        "source": "https://github.com/taehojo/adfly-connectome",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SOURCE, text=True).strip(),
        "neurons": cx.N, "signed_connections": len(cx.dst),
        "stimulus": {"odor": "A", "body_ids": cx.neu.bodyId.iloc[stim].astype(int).tolist(), "rate_hz": 150, "seed": seed, "input_events": int(events.sum()), "event_sha256": hashlib.sha256(events.tobytes()).hexdigest(), "duration_ms": 100, "washout_ms": 150, "replayed_from": str(input_path.relative_to(ROOT)), "source_file_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(), "source_prestimulus_offset_removed_seconds": .05},
        "variants": records,
        "limitations": ["One seed", "250 ms biological time", "External Numba engine, not a new numerical-equivalence test against our Brian2 implementation", "No learning or disease intervention", "The reference-default condition removes measured connections and adds assumed adaptation; lower residual activity does not establish greater biological accuracy"],
        "elapsed_seconds": round(time.monotonic() - started, 3),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "baseline_variants.json").write_text(json.dumps(report, indent=2) + "\n")
    np.savez_compressed(OUT / "baseline_variants.npz", **arrays)


if __name__ == "__main__":
    main()
