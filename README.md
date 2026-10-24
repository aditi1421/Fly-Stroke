# Fly-Stroke: fly memory experiment

The first computational pilot has run. Read [results/report.md](results/report.md) and view [the compact result](results/memory_vs_response.png).

The implementation reproduces a published reduced memory-circuit model and explores disturbances during learning, waiting and recall. It does not simulate a complete fruit fly or establish a human Alzheimer's mechanism.

## Reproduce

Python 3.11 was used. Dependency versions are in `requirements.txt`. The original source and fitted parameters are pinned as the `upstream/` Git submodule at commit `5d7c08a9a88f923169a0c3008aca68af421e9a7f`.

```sh
git clone --recurse-submodules https://github.com/aditi1421/Fly-Stroke.git
cd Fly-Stroke
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 reproduce_baseline.py
python3 -m pytest -q
python3 run_experiment.py
python3 summarize_results.py
```

For an existing clone, first run `git submodule update --init --recursive`. The experiment commands write to `results/`; copy that folder before rerunning if you want to preserve the existing run. No model service calls or API keys are required.

The repository currently studies memory-circuit disturbances motivated by Alzheimer's research. A stroke model has not been implemented.

The complete-brain extension is documented in [WHOLE_BRAIN.md](WHOLE_BRAIN.md). It uses the published 138,639-neuron FlyWire model and compares healthy and explicitly exploratory Alzheimer’s-inspired perturbations.

The baseline check compares 1,944 saved reference values. The experiment uses the authors' fitted parameters rather than refitting them. Configuration, sampled parameter indices, source commit and hashes are recorded with the results. See [METHODS.md](METHODS.md) for definitions and limitations.

## Source and license

Numerical model translated from [schnitzer-lab/Luo_Huang_2024_MB_model](https://github.com/schnitzer-lab/Luo_Huang_2024_MB_model), accompanying [Huang, Luo et al., Nature (2024)](https://www.nature.com/articles/s41586-024-07819-w).

Original model copyright (C) 2024 Junjie Luo, Cheng Huang, Mark J. Schnitzer. The source is offered under GNU GPL version 3 or later, as stated in its README. The derived implementation and study scripts here use the same GPL-3.0-or-later license; see [LICENSE](LICENSE). The upstream source is preserved without edits.
