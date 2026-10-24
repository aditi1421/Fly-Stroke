# Complete-brain simulation

The repository now includes the published Shiu et al. simulator as the `whole_brain_upstream` submodule. It uses the public FlyWire v783 completeness table and connectivity table, representing 138,639 model neurons and their synapses. The upstream model is a Brian2 leaky-integrate-and-fire network.

Install the upstream environment from `whole_brain_upstream/environment_full.yml`, then run:

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

The checked-in `results/full_brain/` run used 0.01 seconds as a construction smoke test. It confirms that the complete network loads and all three conditions execute. It is deliberately too short to support a disease conclusion; use a longer run after installing Brian2 with the upstream environment.
