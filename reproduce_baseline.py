"""Validate the Python port against numeric data in the authors' saved figure."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.io import loadmat

from model import ROOT, NAMES, figure5d_protocol, load_parameters, simulate

FIGURE_FILE = ROOT / "upstream/matlab_code/figure_code_examples/figures/figure5d27-Mar-2023_3modules.fig"


def find_images(node):
    if isinstance(node, dict):
        if node.get("type") == "image":
            yield node["properties"]
        for value in node.values():
            yield from find_images(value)
    elif isinstance(node, (list, np.ndarray)):
        for value in node:
            yield from find_images(value)


def reproduce(output: Path):
    output.mkdir(exist_ok=True)
    images = list(find_images(loadmat(FIGURE_FILE, simplify_cells=True)["hgS_070000"]))
    assert len(images) == 18
    reference = np.array([image["CData"] for image in images]).reshape(6, 3, 9, 12)
    predicted = np.zeros_like(reference)
    for v_index, valence in enumerate(range(-4, 5)):
        parameters = load_parameters(valence=float(valence))
        for t_index, seconds in enumerate(range(300, 3601, 300)):
            result = simulate(parameters, figure5d_protocol(seconds)).imaging
            predicted[:, 0, v_index, t_index] = result[:, 0, -1] - result[:, 0, 0]
            predicted[:, 1, v_index, t_index] = result[:, 1, -1] - result[:, 1, 0]
            predicted[:, 2, v_index, t_index] = result[:, 0, -1] - result[:, 1, -1]
    errors = np.abs(predicted - reference)
    report = {
        "reference": str(FIGURE_FILE.relative_to(ROOT)),
        "source_commit": "5d7c08a9a88f923169a0c3008aca68af421e9a7f",
        "values_compared": int(reference.size),
        "max_absolute_error_hz": float(errors.max()),
        "rmse_hz": float(np.sqrt(np.mean(errors ** 2))),
        "tolerance_hz": 1e-8,
        "passed": bool(errors.max() < 1e-8),
        "scope": "Saved Figure 5d numeric reproduction; not an independent biological validation.",
    }
    (output / "baseline_validation.json").write_text(json.dumps(report, indent=2) + "\n")
    np.savez_compressed(output / "baseline_reference_and_prediction.npz", reference=reference, predicted=predicted)
    fig, axes = plt.subplots(3, 3, figsize=(11, 8), constrained_layout=True)
    for col in range(3):
        for row, data in enumerate((reference, predicted, predicted - reference)):
            ax = axes[row, col]
            panel = data[col + 3, 2]
            scale = 40 if row < 2 else max(1e-12, errors.max())
            im = ax.imshow(panel, aspect="auto", origin="lower", extent=[5, 60, -4.5, 4.5],
                           cmap="RdBu_r", vmin=-scale, vmax=scale)
            if row == 0:
                ax.set_title(NAMES[col + 3])
            if col == 0:
                ax.set_ylabel(("Authors' saved values", "Python reproduction", "Difference")[row] + "\nOdor valence")
            if row == 2:
                ax.set_xlabel("Source protocol time (minutes)")
            fig.colorbar(im, ax=ax, label="CS+ minus CS− (Hz)")
    fig.suptitle("Healthy baseline: numerical reproduction of saved Figure 5d", fontsize=15)
    fig.savefig(output / "baseline_validation.png", dpi=180)
    plt.close(fig)
    print(json.dumps(report, indent=2))
    if not report["passed"]:
        raise AssertionError("The Python model does not match the authors' saved values.")
    return report


if __name__ == "__main__":
    reproduce(ROOT / "results")
