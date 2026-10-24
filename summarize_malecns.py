"""Summarize measured trial outputs without interpreting them as disease effects."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path, nargs="?", default=Path("results/malecns_baseline"))
    args = parser.parse_args()
    metadata = json.loads((args.directory / "summary.json").read_text())
    trials = pd.read_csv(args.directory / "trials.csv")
    order = ["no_stimulus", "baseline", "weights_75_percent"]
    means = trials.groupby("condition").mean(numeric_only=True).reindex(order)
    duration = metadata["seconds_per_trial"]
    repeats = metadata["repeats"]
    plt.rcParams.update({"font.size": 11, "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    colors = ["#a6b1bc", "#247ba0", "#d87831"]
    for ax, field, title in zip(axes, ["total_spikes", "readout_spikes"],
                                ["Entire retained network", f'{metadata["readout_type"]} readout']):
        for seed, rows in trials.groupby("seed"):
            values = rows.set_index("condition").reindex(order)[field]
            ax.plot([1, 2], values.iloc[1:], color="#9ca3af", alpha=.6, linewidth=1)
            ax.scatter(range(3), values, color=colors, s=45, alpha=.8, zorder=3)
        for x, value in enumerate(means[field]):
            ax.annotate(f"mean {value:,.1f}", (x, value), xytext=(0, 14),
                        textcoords="offset points", ha="center", fontsize=10)
        ax.set_xticks(range(3), ["No input", "Baseline", "All weights\n× 0.75"])
        ax.set_ylabel(f"Spikes per {duration:g} s trial")
        ax.set_title(title)
        ax.set_ylim(-max(means[field].max() * .06, 1), max(means[field].max() * 1.28, 1))
        ax.grid(axis="y", alpha=.18)
    fig.suptitle("MaleCNS: technical baseline and weight sensitivity", fontsize=16, y=.98)
    fig.text(.5, .89, f'{metadata["dataset"]["neuron_count"]:,} neurons · {repeats} paired seeds · {duration:g} s per trial', ha="center")
    fig.text(.5, .03, "Dots are individual trials; lines pair seeds. Transferred dynamics, no disease calibration.", ha="center", fontsize=10)
    fig.subplots_adjust(top=.78, bottom=.2, wspace=.3)
    fig.savefig(args.directory / "comparison.png", dpi=180)
    plt.close(fig)
    baseline = means.loc["baseline"]
    weakened = means.loc["weights_75_percent"]
    reduction = 100 * (1 - weakened.total_spikes / baseline.total_spikes)
    rows = "\n".join(f"| {name} | {row.total_spikes:,.1f} | {row.active_neurons:,.1f} | {row.nonstimulus_spikes:,.1f} | {row.readout_spikes:,.1f} |"
                     for name, row in means.iterrows())
    report = f"""# MaleCNS technical baseline

![Measured trial outputs](comparison.png)

The full retained graph executed with {metadata['dataset']['neuron_count']:,} neurons,
{metadata['dataset']['directed_connections']:,} directed neuron-pair connections and
{metadata['dataset']['synaptic_contacts']:,} measured contacts. Every neuron was present
in every run. Each condition used {repeats} independent trials of {duration:g} seconds;
seeds were paired across conditions. The inputs stimulate {len(metadata['stimulus_body_ids'])}
{metadata['stimulus_type']} neurons at {metadata['stimulus_hz_per_neuron']:g} Hz per neuron.

Means across trials (individual values are in [trials.csv](trials.csv)):

| Condition | Total spikes | Active neurons | Spikes outside stimulated cells | Readout spikes |
|---|---:|---:|---:|---:|
{rows}

The no-input control remained silent. Input drove activity beyond the stimulated
cells and reached the named {metadata['readout_type']} readout. Uniform 25% weight
reduction lowered mean total spike count by {reduction:.1f}% in this configuration.
This intervention weakens both excitation and inhibition. It is a model sensitivity
result, not a measurement of Alzheimer's damage or behavior.

The stimulus is artificial, the duration is short, and the Shiu dynamics were
transferred from FlyWire without calibration to MaleCNS. Transmitter signs are
simplified; {metadata['dataset']['zero_sign_neurons']:,} cells have zero modeled output
sign because modulatory/unknown effects are unimplemented. No learning, memory,
amyloid, tau, glial response, body behavior or human disease was tested.

Data: [official MaleCNS v1.0](https://male-cns.janelia.org/download/),
CC BY 4.0, FlyEM/HHMI Janelia, Cambridge, MRC LMB and Google Research.
See [summary.json](summary.json) for source hashes, filters, parameters and
individual trials, and [source review](../../SOURCE_REVIEW.md) for project selection.
"""
    (args.directory / "report.md").write_text(report)
    print(rows)


if __name__ == "__main__":
    main()
