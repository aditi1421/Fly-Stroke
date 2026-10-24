"""Create a readable report and a compact figure from completed experiment data."""
import csv
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from model import ROOT


def read_rows(path: Path) -> list[dict]:
    with path.open() as stream:
        return list(csv.DictReader(stream))


def main():
    output = ROOT / "results"
    rows = read_rows(output / "phase_sweep.csv")
    rows = [row for row in rows if row["neuron"] == "MBON alpha3" and float(row["valence"]) == 0]
    samples = read_rows(output / "parameter_sensitivity.csv")
    samples = [row for row in samples if row["neuron"] == "MBON alpha3"]
    base = {(row["parameter_sample"], float(row["wait_seconds"])): float(row["memory_signal_hz"])
            for row in samples if row["mechanism"] == "healthy"}
    summary = []
    pairs = sorted({(row["mechanism"], row["phase"]) for row in samples if row["mechanism"] != "healthy"})
    for mechanism, phase in pairs:
        selected = [row for row in samples if row["mechanism"] == mechanism and row["phase"] == phase]
        ratios = {(row["parameter_sample"], float(row["wait_seconds"])):
                  float(row["memory_signal_hz"]) / base[row["parameter_sample"], float(row["wait_seconds"])]
                  for row in selected if base[row["parameter_sample"], float(row["wait_seconds"])] >= 1}
        ids = {row["parameter_sample"] for row in selected}
        valid = [key for key in ids if all((key, time) in ratios for time in (0., 7200., 21600.))]
        matches = [key for key in valid if .9 <= ratios[key, 0.] <= 1.1 and 0 <= ratios[key, 7200.] <= .8]
        summary.append({"mechanism": mechanism, "phase": phase,
                        "valid_parameter_draws": len(valid), "pattern_matches": len(matches),
                        "immediate_ratio_p10_p50_p90": np.percentile([ratios[key, 0.] for key in valid], [10, 50, 90]).tolist(),
                        "two_hour_ratio_p10_p50_p90": np.percentile([ratios[key, 7200.] for key in valid], [10, 50, 90]).tolist()})
    (output / "sensitivity_summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    labels = ["Healthy", "Weaker learning\nplasticity", "Weaker transmission\nat recall", "Faster decay\nbenchmark"]
    keys = [("healthy", "none", 0.), ("plasticity", "learning", .25),
            ("transmission", "recall", .25), ("decay_benchmark", "waiting", .25)]
    selected = [next(row for row in rows if (row["mechanism"], row["phase"], float(row["strength"])) == key
                     and float(row["wait_seconds"]) == 7200.) for key in keys]
    metrics = ["memory_signal_hz", "stored_trace", "restored_signal_hz"]
    proportions = np.array([[float(row[metric]) / float(selected[0][metric]) * 100 for metric in metrics]
                            for row in selected])
    fig, ax = plt.subplots(figsize=(11, 5.7), constrained_layout=True)
    positions = np.arange(4)
    for index, (label, color) in enumerate(zip(
            ["Measured response", "Stored model trace", "Response after restoring transmission"],
            ["#247ba0", "#9b5de5", "#4c956c"])):
        bars = ax.bar(positions + (index - 1) * .24, proportions[:, index], width=.23, label=label, color=color)
        ax.bar_label(bars, fmt="%.0f%%", fontsize=9, padding=3)
    ax.set_xticks(positions, labels)
    ax.set_ylim(0, 135)
    ax.set_ylabel("Percentage of healthy model value at the same delay")
    ax.set_title("A weaker response can occur while the model's stored trace remains intact\n"
                 "Two-hour model wait · neutral odors · exploratory 25% interventions", fontsize=13, pad=15)
    ax.legend(loc="upper center", frameon=False, ncol=3, fontsize=9)
    ax.spines[["top", "right"]].set_visible(False)
    ax.axhline(100, color="grey", linestyle=":", linewidth=.7)
    fig.savefig(output / "memory_vs_response.png", dpi=190)
    fig.savefig(output / "memory_vs_response.svg")
    plt.close(fig)

    validation = json.loads((output / "baseline_validation.json").read_text())
    manifest = json.loads((output / "run_manifest.json").read_text())
    table = "\n".join(f"| {label.replace(chr(10), ' ')} | {values[0]:.1f}% | {values[1]:.1f}% | {values[2]:.1f}% |"
                      for label, values in zip(labels, proportions))
    sensitivity_table = "\n".join(
        f"| {row['mechanism']} / {row['phase']} | {row['pattern_matches']}/{row['valid_parameter_draws']} | "
        f"{row['two_hour_ratio_p10_p50_p90'][1]:.3f} "
        f"({row['two_hour_ratio_p10_p50_p90'][0]:.3f}–{row['two_hour_ratio_p10_p50_p90'][2]:.3f}) |" for row in summary)
    report = f"""# First experiment: executed results

Completed: {manifest['completed_utc']}. This is an exploratory computational experiment in a published three-module fly memory model. It is not a whole-fly emulation, an animal experiment, or a calibrated simulation of Alzheimer's disease.

## Main finding

In this model, a smaller learned neural response can reflect reduced expression of an intact synaptic trace, reduced formation of that trace, or accelerated trace decay. The observed response alone does not uniquely identify the mechanism.

After a two-hour model wait, reducing effective KC-to-MBON transmission by 25% only during recall reduced the primary response from {float(selected[0]['memory_signal_hz']):.2f} to {float(selected[2]['memory_signal_hz']):.2f} Hz. The stored trace was unchanged. Restoring transmission recovered the response without additional training. This intervention also reduces general odor responsiveness: it is a demonstration of an output confound, not proof of a selective biological retrieval disorder.

![Stored trace and measured response](memory_vs_response.png)

| Condition | Measured response | Stored trace | Response after transmission is normal |
|---|---:|---:|---:|
{table}

Values are relative to the healthy model at the same delay, using the mean fitted parameters and neutral odors. These percentages are neither behavioral accuracy nor predicted human memory performance. Restoring transmission means probing the same saved state with the transmission manipulation absent; it is not a treatment experiment.

## Healthy-model verification

The Python translation matched **{validation['values_compared']:,} numeric entries** in the authors' saved Figure 5d. Maximum absolute difference: **{validation['max_absolute_error_hz']:.2e} Hz** against a 1e-8 Hz tolerance. This verifies reproduction of that saved figure, not every published result or independent biological validity. An analytic check also covers the model's change in decay time constant at three hours.

The original MATLAB implementation and fitted parameter files are preserved in `../upstream`, pinned to commit `{manifest['source_commit']}`. We did not run MATLAB or refit parameters. [Authors' model and source](https://github.com/schnitzer-lab/Luo_Huang_2024_MB_model).

## What ran

- 49 conditions: healthy, plus four mechanisms × four phases × three strengths.
- Six waiting intervals, three odor-valence settings, and three MBON output measures: {manifest['phase_sweep_readouts']:,} readouts.
- 100 parameter draws from the authors' supplied samples, eight selected conditions and three delays: {manifest['parameter_sensitivity_readouts']:,} additional readouts.
- {manifest['paired_and_unpaired_simulations']:,} paired/unpaired model simulations in those sweeps, plus controls.
- {manifest['control_readouts']} control readouts: swapped odor labels gave zero discrepancy; disabling plasticity gave zero learned response after subtracting the matched unpaired condition.

The configuration was saved before the perturbation runs. Strengths were exploratory; none were fitted to Alzheimer's data. The six-hour interval was reserved as an additional check, with no fitting performed at any interval. See [methods](../METHODS.md) for the phase definitions and measurements.

## Can the model imitate preserved early performance and poorer delayed performance?

We screened for an immediate response within 90–110% of healthy and a two-hour response at most 80% of healthy, retaining the same response sign and requiring a healthy signal of at least 1 Hz. These are exploratory thresholds, not biological cutoffs.

At the mean parameters, the 25% recall-transmission manipulation qualified: 90.3% initially, 75.0% at two hours, and 75.0% at six hours. Yet its stored trace was unchanged at every delay. The apparent delay dependence arises from the nonlinear, bounded response measure and odor adaptation, rather than additional loss of the stored trace.

This pattern is not robust to all parameter choices. For example, recall-transmission met the screen in only 50 of 100 supplied parameter draws. The table reports sensitivity across those draws; the intervals are 10th–90th percentiles, **not confidence intervals from animals or people**.

| Selected intervention | Draws matching the early/delayed screen | Two-hour response ratio, median (10th–90th percentile) |
|---|---:|---:|
{sensitivity_table}

Changing innate odor valence also changes the pattern. At valence −3, the recall-transmission ratios were 75.0% immediately and 99.8% at two hours. Thus the neutral-odor result must not be treated as a universal outcome.

Shortening decay constants produced preserved initial response and lower delayed response, as expected from directly changing a forgetting parameter. That benchmark cannot identify what causes forgetting. Some changes applied during learning also met the screen under parameter variation, reinforcing the ambiguity of response-only measures.

## A limitation exposed by the runs

Transmission, plasticity, and tonic dopamine changes confined to silent waiting did not change the trace. In the source model, waiting has no Kenyon-cell odor input and its plasticity update is gated by that input. Its stored traces change during silent waiting through explicit decay. This is a structural limitation, not evidence that those processes are irrelevant during biological memory retention.

The tonic-dopamine extension is an exploratory common drive to the three modeled DAN variables. It does not simulate sleep, spontaneous Kenyon-cell activity, molecular forgetting pathways, or Alzheimer's-related hyperexcitability in full.

## What this contributes to understanding humans

The useful hypothesis is about measurement: poor recall need not, by itself, tell us whether a memory was weakly formed, lost during retention, or poorly expressed. Human comparisons should control initial learning and measure delayed free recall, cued recall or recognition, alongside relevant biological evidence. Restoring model transmission is not equivalent to giving a person a cue.

Human evidence supports separating these components, but does not validate this fly model's mechanism. In a study of 37 people with probable Alzheimer's disease, hippocampal volume was associated with retention after accounting for initial recall. The authors also noted limited ability to control additional demographic factors. [Human retention study](https://pmc.ncbi.nlm.nih.gov/articles/PMC1820856/)

A separate human study found that combined free and cued recall was more impaired in Alzheimer's than in non-Alzheimer dementias. This is a reason to test storage-related explanations, rather than conclude that Alzheimer's memory problems are simply a recoverable output failure. [Human free/cued recall study](https://pmc.ncbi.nlm.nih.gov/articles/PMC2929322/)

The motivating fly study observed preserved immediate performance with lower later performance under restricted amyloid-beta expression, but could not exclude impaired consolidation. Our screen resembles that pattern qualitatively; we did not fit or independently predict its experimental data. [Fly Alzheimer's study](https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.3001412)

There are no disease-specific amyloid/tau dynamics, glial mechanisms, neuronal death, or human anatomical mappings in this implementation. The next scientific step is to constrain a specific cellular disturbance with measured fly data and test an intervention or time point not used to set its parameters. A disease mechanism has not been established by this pilot.

## Files

- [Compact figure](memory_vs_response.png) and [all four mechanism plots](phase_comparison.png).
- [Baseline reproduction](baseline_validation.png), [numeric comparison](baseline_validation.json).
- [All mean-parameter results](phase_sweep.csv), [parameter sensitivity](parameter_sensitivity.csv), [controls](controls.csv).
- [Run configuration](config_used.json), [run manifest](run_manifest.json), [pattern screen](pattern_screen.json).
"""
    (output / "report.md").write_text(report)
    provenance = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in sorted(ROOT.glob("*.py"))}
    provenance["study_config.json"] = hashlib.sha256((ROOT / "study_config.json").read_bytes()).hexdigest()
    (output / "code_hashes.json").write_text(json.dumps(provenance, indent=2) + "\n")
    print("Wrote results/report.md, memory_vs_response.png/.svg, and sensitivity_summary.json")


if __name__ == "__main__":
    main()
