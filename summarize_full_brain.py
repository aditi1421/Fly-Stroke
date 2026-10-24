"""Summarize whole-brain smoke outputs without loading the connectivity graph."""
from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "results/full_brain"

def main():
    rows = []
    for path in sorted(DATA.glob("*.parquet")):
        frame = pd.read_parquet(path)
        rows.append({
            "condition": path.stem,
            "neurons": int(len(frame)),
            "active_neurons": int((frame.rate_hz > 0).sum()),
            "total_spikes": int(frame.spike_count.sum()),
            "max_rate_hz": float(frame.rate_hz.max()),
            "mean_rate_hz_all_neurons": float(frame.rate_hz.mean()),
        })
    report = {
        "connectome": "FlyWire FAFB v783",
        "neuron_count": 138639,
        "run_duration_seconds": 0.01,
        "conditions": rows,
        "interpretation": "Smoke run verifies full network construction and condition execution; 10 ms is too short for disease conclusions.",
    }
    (DATA / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
