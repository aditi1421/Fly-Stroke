# Complete-brain simulation

## Current: MaleCNS v1.0

The latest completed study uses the published adfly engine and a Brian2 comparator:
[component-assay results](results/amyloid_reference_components/report.md),
[chart](results/amyloid_reference_components/comparison.png), and
[reference setup](research/REFERENCE_REPRODUCTION.md). It runs all 166,700 cells
with separate excitability, contact-loss and cell-silencing conditions. The LC4
setup below is the earlier technical baseline.

The official Google Research/Janelia MaleCNS dataset includes both brain and
ventral nerve cord. See [SOURCE_REVIEW.md](SOURCE_REVIEW.md) for the distinction
between this dataset, DeepMind's Flybody, and the linked mouse project.

Use a separate Python 3.10 environment with the tested package versions in
`requirements-whole-brain.txt`. The original reduced-model `requirements.txt`
is separate.

```sh
python3.10 -m venv .venv-malecns
source .venv-malecns/bin/activate
python -m pip install -r requirements-whole-brain.txt
python prepare_malecns.py --download
python run_malecns.py --seconds 0.1 --repeats 3 --output results/malecns_baseline
python summarize_malecns.py results/malecns_baseline
```

The checked-in run and chart are in [results/malecns_baseline/report.md](results/malecns_baseline/report.md).
To reproduce after cloning, use a new output path (for example
`results/malecns_reproduction`) in both commands, since the runner refuses to
overwrite results.

Raw and prepared data stay in ignored `data/malecns/` (several GB locally).
The adapter records URLs, SHA-256 fingerprints, retained counts and exclusions
in `manifest.json`. It preserves weak connections and self-connections. Only
annotated neuronal superclasses and edges with both endpoints retained are used;
unclassified segments are excluded. The source is licensed CC BY 4.0, attributed
to FlyEM/HHMI Janelia, Cambridge, MRC LMB and Google Research.

The runner verifies prepared-file hashes and builds the entire retained graph.
It transfers the Shiu LIF equations and default parameters to MaleCNS; these
parameters have not been fitted or biologically validated on this dataset.
Predicted acetylcholine outputs are positive, GABA/glutamate negative, and other
or unknown outputs zero. These are simplified transmitter assumptions;
modulatory signals and receptor-specific effects are absent.

Each trial starts from a restored initial network state with a new seed, paired
across conditions. The three conditions are no stimulation, baseline LC4
stimulation, and the same stimulation with every connection weight multiplied
by 0.75. The last condition weakens inhibition as well as excitation. It is a
generic sensitivity check, not an amyloid treatment. LC4 receives artificial
150 Hz Poisson drive per neuron; DNp01 is a named downstream readout. Natural
vision, escape behavior, memory, disease progression and a moving body are not
implemented.

The output directory must be new. It contains per-trial neuron counts/rates,
`trials.csv` and `summary.json` with provenance and parameters. All neurons
participate in every condition; readout selection does not reduce the network.
Run `python -m pytest -q test_malecns.py` in the Brian2 environment to check ID
mapping, signs, missing endpoints, independent trials and reproducibility.

## Historical FlyWire construction check

The old `full_brain_alzheimers.py` is retained for provenance, but should not be
used for new experiments: its seed was not applied and its repeat option copied
one run's outputs. Its misleading disease condition names are not evidence of
modeled amyloid or intrinsic hyperexcitability. The new runner corrects trial and
seed handling and uses literal perturbation names.

The repository now includes the published Shiu et al. simulator as the `whole_brain_upstream` submodule. It uses the public FlyWire v783 completeness table and connectivity table, representing 138,639 model neurons and their synapses. The upstream model is a Brian2 leaky-integrate-and-fire network.

The historical command (not recommended for new experiments) was:

```sh
python3 full_brain_alzheimers.py --seconds 0.1 --repeats 1
python3 summarize_full_brain.py
```

The script compares a healthy full-brain run with two explicitly labelled exploratory conditions:

- `amyloid_synaptic_dysfunction`: all synaptic weights scaled to 75%.
- `amyloid_plus_hyperexcitability`: the same synaptic scaling plus a 15% increase in the external stimulus rate.

These are controlled perturbations, not a biological Alzheimer’s model. The complete connectome currently has no disease state, amyloid concentration, tau dynamics, glial response, neuron death, or human anatomical mapping. The purpose of this stage is to establish a reproducible full-brain baseline and measure how network activity changes under clearly defined interventions. Later disease-specific parameters must be constrained by fly experiments.

The memory-circuit experiment remains in the repository as a validated submodel. Its results do not automatically transfer to the full brain.

Source: [Drosophila brain model](https://github.com/philshiu/Drosophila_brain_model), accompanying [Nature paper](https://www.nature.com/articles/s41586-024-07763-9). The upstream code and data retain their original licenses; see their submodule README. The wrapper is GPL-3.0-or-later.

The checked-in `results/full_brain/` run used 0.01 seconds as a construction smoke test. It confirms network loading and condition execution only. It is too short to support a disease conclusion; use the current runner above for new work.
