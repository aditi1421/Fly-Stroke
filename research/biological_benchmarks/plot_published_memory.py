"""Plot original experiment-level summaries; no simulation data enter this figure."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent


def main():
    dataset = json.loads((ROOT / "kaldun2021_measurements.json").read_text())
    groups = dataset["groups"]
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 10,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.titleweight": "bold", "axes.labelcolor": "#263341",
        "text.color": "#263341", "xtick.color": "#263341", "ytick.color": "#263341",
        "savefig.facecolor": "white",
    })
    fig, (left, right) = plt.subplots(1, 2, figsize=(12, 7), gridspec_kw={"width_ratios": [1.5, 1]})
    fig.subplots_adjust(left=.075, right=.98, top=.76, bottom=.32, wspace=.32)
    fig.suptitle("Published fly measurements — not simulation", fontsize=18, fontweight="bold", y=.97)
    fig.text(.075, .89, "Kaldun et al. (2021)  •  Adult flies aged 7–9 days  •  Points and bars show mean ± SEM", fontsize=11)

    selections = [
        ("UAS-Arc/+", "UAS parental control", "#1B6CA8", "o"),
        ("Ok107-Gal4/+", "OK107 parental control", "#16857A", "s"),
        ("Ok107 > Arc", "OK107 > Arctic Aβ42", "#C44343", "D"),
    ]
    for genotype, label, color, marker in selections:
        selected = sorted([
            row for row in groups
            if row["assay"] == "aversive" and row["genotype_verbatim"] == genotype
            and row["figure"] in {"1C", "1D", "S1H"}
        ], key=lambda row: row["retention_hours_label"])
        assert [row["retention_hours_label"] for row in selected] == [0, 2, 4, 6]
        assert all(row["n_experiments"] == 12 for row in selected)
        left.errorbar([row["retention_hours_label"] for row in selected],
                      [row["mean"] for row in selected],
                      yerr=[row["sem"] for row in selected],
                      color=color, marker=marker, label=label, linewidth=2,
                      markersize=6, elinewidth=1.3, capsize=4)
    left.set_title("A  Aversive memory retention", loc="left", pad=30)
    left.set(xlabel="Time after conditioning (hours)",
             ylabel="Behavioral performance index (points)", xticks=[0, 2, 4, 6], ylim=(-10, 80))
    left.text(0, 1.025, "OK107 driver; n = 12 experiments per point", transform=left.transAxes, fontsize=10)
    left.axhline(0, color="#A8B0B8", linewidth=.8)
    left.grid(axis="y", color="#E7EBEF", zorder=0)
    left.legend(loc="upper right", frameon=False, fontsize=9)

    selected = [row for row in groups if row["figure"] == "3C" and row["retention_hours_label"] == 6]
    assert len(selected) == 2 and all(row["n_experiments"] == 8 for row in selected)
    assert selected[0]["intervention"] == "21–22 C"
    means = [row["mean"] for row in selected]
    errors = [row["sem"] for row in selected]
    right.bar([0, 1], means, color=["#C44343", "#7E63B6"], width=.57, alpha=.86,
              yerr=errors, capsize=5, error_kw={"elinewidth": 1.3}, zorder=3)
    for x, mean, error in zip([0, 1], means, errors):
        right.text(x, mean + error + 2, f"{mean:.1f} ± {error:.1f}", ha="center", fontsize=10)
    right.set_title("B  Intervention experiment", loc="left", pad=30)
    right.set(ylabel="6-hour performance index (points)",
              xticks=[0, 1], xticklabels=["Room-temperature\ncomparison", "PPL1 transmission\nblocked for first 2 h"],
              ylim=(-5, 42))
    right.text(0, 1.025, "Appetitive; MB247/c150 drivers; n = 8 per bar", transform=right.transAxes, fontsize=9)
    right.axhline(0, color="#A8B0B8", linewidth=.8)
    right.grid(axis="y", color="#E7EBEF", zorder=0)

    fig.text(.075, .13,
             "A: “0 h” was tested about 3 minutes after training. Lines connect independent group summaries.\n"
             "B: Both groups express Arctic Aβ42 in mushroom bodies. Blockade: 2 h at 30°C, then 4 h recovery.\n"
             "Different assays and drivers: the panels should not be pooled. Temperature/driver controls are in the source dataset.",
             fontsize=9, linespacing=1.5)
    fig.text(.075, .035,
             "Source: Kaldun et al., PLOS Biology 19(10), e3001412 (2021), Figs 1C–D, S1H, 3C; S1 Table.\n"
             "doi:10.1371/journal.pbio.3001412  •  Experimental unit: reciprocal conditioning experiment, not an individual fly.",
             fontsize=8.5, color="#52606E", linespacing=1.4)
    output = ROOT / "published_memory.png"
    fig.savefig(output, dpi=220)
    plt.close(fig)
    print(output)


if __name__ == "__main__":
    main()
