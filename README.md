# Fly-Stroke: fly memory experiment

**Latest completed experiment:** the published [adfly-connectome model](https://github.com/taehojo/adfly-connectome)
ran all **166,700 neurons** across 54 paired component trials, with 54 original-graph
comparison trials and six complete-restoration checks. Combined amyloid-inspired
changes reduced mean mushroom-body output spikes from 11.2 to 5.5 during stimulation.
See the [results and interpretation](results/amyloid_reference_components/report.md),
[chart](results/amyloid_reference_components/comparison.png), and
[reproduction instructions](research/REFERENCE_REPRODUCTION.md).
These are circuit-response measurements; learned memory and human disease were not tested.

The current whole-network work uses the **MaleCNS v1.0 brain and ventral nerve
cord dataset** announced by Google Research and Janelia in September 2026.
See [source review](SOURCE_REVIEW.md) and [whole-network setup](WHOLE_BRAIN.md).
This is a technical baseline with transferred neuron dynamics, not a validated
Alzheimer's model. Earlier results below remain separate.

The first MaleCNS run is complete: [report](results/malecns_baseline/report.md)
and [chart](results/malecns_baseline/comparison.png). It exercises 166,700 neurons
over three paired seeds per condition; the 100 ms trials establish technical
operation and generic weight sensitivity only.

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

The earlier 138,639-neuron FlyWire run is retained under `results/full_brain/` as
a 10 ms construction check. Its zero-versus-one-spike outputs support no disease
conclusion. Use the new MaleCNS runner for current work.

The baseline check compares 1,944 saved reference values. The experiment uses the authors' fitted parameters rather than refitting them. Configuration, sampled parameter indices, source commit and hashes are recorded with the results. See [METHODS.md](METHODS.md) for definitions and limitations.

## Source and license

Numerical model translated from [schnitzer-lab/Luo_Huang_2024_MB_model](https://github.com/schnitzer-lab/Luo_Huang_2024_MB_model), accompanying [Huang, Luo et al., Nature (2024)](https://www.nature.com/articles/s41586-024-07819-w).

Original model copyright (C) 2024 Junjie Luo, Cheng Huang, Mark J. Schnitzer. The source is offered under GNU GPL version 3 or later, as stated in its README. The derived implementation and study scripts here use the same GPL-3.0-or-later license; see [LICENSE](LICENSE). The upstream source is preserved without edits.
