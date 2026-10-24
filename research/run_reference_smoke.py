"""Bounded, independent execution of Jo's unmodified external model.

Clone https://github.com/taehojo/adfly-connectome into research/adfly-connectome,
build its real MaleCNS pack following its README, then run this script. This is
a technical smoke run, not reproduction of its paper's cohorts or AD validation.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

import numpy as np
import numba

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research/adfly-connectome"
OUT = ROOT / "results/adfly_reference"
sys.path.insert(0, str(SOURCE / "code"))
from adfly.lif import poisson_events
from adfly.model import Connectome, Fly, ODORS, build_brains


def main():
    started = time.monotonic()
    OUT.mkdir(parents=True, exist_ok=True)
    cx = Connectome()
    br = build_brains(cx, [Fly(fly_id=0, seed=20261024)])
    stim = cx.upn(ODORS["A"]).astype(np.int32)
    br.no_refractory(stim)
    br.set_groups(np.arange(cx.N), cx.N)
    steps = 1000  # 100 ms at the upstream default 0.1 ms step
    seed = 20261024
    events = poisson_events(np.random.default_rng(seed), np.full((1, len(stim)), 150.0), steps, br.p.dt)
    driven = br.run(steps, stim[None, :], events)[0, 0]
    gap = br.run(steps, np.zeros((1, 0), np.int32), np.zeros((1, steps, 0), bool))[0, 0]
    source_facts = SOURCE / "results/facts/facts_validation.json"
    facts_bytes = source_facts.read_bytes()
    committed_facts = subprocess.check_output(["git", "show", "HEAD:results/facts/facts_validation.json"], cwd=SOURCE)
    facts = json.loads(facts_bytes)
    published_digests = json.loads((SOURCE / "connectome/network_digests.json").read_text())["sha256"]
    array_digest_checks = {}
    for name in ("neuron_ids.npy", "row_ptr.npy", "dst.npy", "signed_w.npy"):
        digest = hashlib.sha256((cx.pack / name).read_bytes()).hexdigest()
        array_digest_checks[name] = {"sha256": digest, "matches_published": digest == published_digests[name]}
    report = {
        "purpose": "Technical reference execution only; no disease perturbation, learning or retention assay.",
        "source": "https://github.com/taehojo/adfly-connectome",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=SOURCE, text=True).strip(),
        "source_license": "MIT; data/results CC BY 4.0 except identified FlyWire-derived files CC BY-NC 4.0",
        "neurons": cx.N,
        "signed_connections": len(cx.dst),
        "official_input_sha256": json.loads((cx.pack / "manifest.json").read_text())["sources"],
        "network_array_checks": array_digest_checks,
        "al_connections_zeroed_by_reference_model": int(cx.al_edge.sum()),
        "al_contacts_zeroed_by_reference_model": int(np.abs(cx.signed[cx.al_edge]).sum()),
        "model_extensions": ["All AL-to-AL chemical connections zeroed", "1 mV spike adaptation in nonsensory neurons, tau 1000 ms"],
        "stimulus": {"odor": "A", "glomeruli": ODORS["A"], "body_ids": cx.neu.bodyId.iloc[stim].astype(int).tolist(), "rate_hz": 150, "duration_ms": steps * br.p.dt, "seed": seed, "input_events": int(events.sum()), "event_sha256": hashlib.sha256(events.tobytes()).hexdigest()},
        "driven": {"total_spikes": int(driven.sum()), "active_neurons": int(np.count_nonzero(driven)), "KC_spikes": int(driven[cx.is_kc].sum()), "MBON_spikes": int(driven[cx.mbon].sum()), "stimulated_neuron_spikes": int(driven[stim].sum())},
        "poststimulus_100ms": {"total_spikes": int(gap.sum()), "active_neurons": int(np.count_nonzero(gap)), "KC_spikes": int(gap[cx.is_kc].sum()), "MBON_spikes": int(gap[cx.mbon].sum())},
        "stored_validation_audit": {"description": "facts_validation.py rerun on the author's stored results; this is arithmetic reproduction, not a new engine comparison", "byte_identical_to_commit": facts_bytes == committed_facts, "sha256": hashlib.sha256(facts_bytes).hexdigest(), "facts_count": len(facts["_meaning"]), "network": facts["val_network"], "neurons": facts["val_neurons"], "pearson_200hz_engine_vs_local_brian2_range": facts["val_cmp_engine_200_discard_vs_local_pearson_range"]},
        "versions": {"python": sys.version.split()[0], "numpy": np.__version__, "numba": numba.__version__},
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "limitations": ["Single healthy realization", "Only 200 ms biological time", "Different software versions from published environment", "Published numerical comparison covers FlyWire base equations, not MaleCNS adaptation, removed AL edges or disease biology", "No independent animal or human validation"],
    }
    np.savez_compressed(OUT / "healthy_odor_smoke.npz", driven_spike_counts=driven, poststimulus_spike_counts=gap, stimulus_indices=stim, stimulus_events=events)
    (OUT / "reference_audit.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
