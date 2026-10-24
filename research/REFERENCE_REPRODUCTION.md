# External model reproduction

**Completed follow-up:** [54 paired component trials and six restoration checks](../results/amyloid_reference_components/report.md)
now use this published engine, alongside 54 Brian2 comparator trials. The one-seed
healthy smoke run below is an earlier diagnostic; its silent washout did not
generalize to all six inputs in the completed cohort.

Reviewed source: [Jo, adfly-connectome](https://github.com/taehojo/adfly-connectome),
commit `dcc143ec703d297739bf92f825b20dceea232505`, accompanying
[arXiv:2610.19153](https://arxiv.org/abs/2610.19153). Code is MIT licensed;
MaleCNS source data are CC BY 4.0. The external checkout retains its own notices
and is excluded from this project's Git history.

## What was reproduced

- Built its full 166,700-neuron network using the three official MaleCNS files
  already downloaded by this project. All four numerical array files match
  the author's published SHA-256 digests exactly: neuron IDs, CSR row pointers,
  destinations and signed contact counts. The network has 24,469,412 signed
  connections and 120,260,398 contacts.
- Reran `facts_validation.py`: all 159 facts reproduced byte for byte from
  the author's stored result vectors. This checks the analysis, not a fresh
  simulation comparison against Brian2.
- Executed one new healthy odor-A reference run: 100 ms of 150 Hz input to
  eight projection neurons, followed by 100 ms without input. Seed 20261024.
  There were 1,064 network spikes during stimulation and 42 afterward.
  This is a technical smoke run, not reproduction of the paper's cohorts.

Exact metadata, source hashes and counts are in
[`reference_audit.json`](../results/adfly_reference/reference_audit.json).
The spike-count arrays and replayable input events are in
`results/adfly_reference/healthy_odor_smoke.npz`.

## Paired baseline diagnostic

`research/run_reference_variants.py` replays the exact 107 input events from
`results/amyloid_native_graph_check/input_trial_00.npz`, removing its 50 ms
quiet offset, through three settings of the same external engine. All use
166,700 cells and the same seed's input. Values below are total network
spikes per second; the different phase durations are normalized.

| Setting | 100 ms stimulus | First 50 ms after | Next 50 ms | Last 50 ms |
|---|---:|---:|---:|---:|
| Original signed graph | 444,660 | 506,100 | 501,780 | 502,020 |
| Original graph + adaptation | 334,680 | 259,920 | 219,720 | 196,160 |
| Reference AL deletion + adaptation | 10,640 | 840 | 0 | 0 |

The original graph sustains activity after the stimulus ends in this engine
as well as in our Brian2 baseline. Adaptation reduces that activity over the
tested interval; adding the reference's AL deletion quenches it. This does
not establish that deleting measured connections makes the model biologically
accurate. It identifies a major dependence on model assumptions before any
disease interpretation. These are one-seed diagnostics, not an animal result
or a formal equivalence test between engines.

The complete 10 ms counts, 50 ms rate blocks, provenance and limitations are
in [`baseline_variants.json`](../results/adfly_reference/baseline_variants.json).
No disease manipulation or learning is applied in this comparison.

## Important implementation differences

The reference model zeros 435,937 connections between antennal-lobe neurons,
representing 3,235,396 contacts. It also adds 1 mV of spike adaptation to
nonsensory neurons, decaying over 1,000 ms. Our Brian2 comparator retains the
original signed network, so these runs must not be treated as interchangeable.

Its optional learning rule depresses active KC-to-MBON weights by 60% when
the corresponding dopamine neuron type exceeds 5 Hz. The neural learning
score is a before/after odor-response contrast. There is no explicit slow
retention or consolidation state, and the score is not observed behavior.

The published numerical comparison uses the base Shiu equations on FlyWire
v630 (127,400 neurons), without the MaleCNS adaptations. It reports per-neuron
rate correlations of 0.9998 against its local Brian2 run at 200 Hz input.
This does not validate antennal-lobe deletion, adaptation, disease magnitudes,
memory mechanisms, or predictions for humans. The three pathology strengths
(maximum 2 mV threshold reduction, 60% contact loss, 50% neuron silencing)
are explicitly assumed rather than fitted to a common biological dataset.

The new `research/run_reference_components.py` uses the reference's healthy
defaults but directly applies our paired KC-targeted lesions to weights and
thresholds. It deliberately does not use the paper's hub-ranked severity
distribution or invoke its optional learning rule. Thus it tests our component
design in the published engine; it does not reproduce the paper's disease cohorts.

## How to rerun

Use a Python environment with numpy, pandas, scipy, numba and pyarrow. Our
run used Python 3.11.8, NumPy 2.2.6 and Numba 0.61.2; the author's environment
was different, as recorded in their `requirements-simulation.txt`.

1. Clone the source into `research/adfly-connectome` and check out the commit
   above. Do not add the nested repository to this project's Git index.
2. Point its `data/malecns_v1.0` directory to this project's `data/malecns/raw`
   (a directory symlink avoids downloading or copying the 1 GB input again).
3. From the checkout, execute `code/adfly/build_pack.py`,
   `code/adfly/build_mb_edges.py`, then `code/scripts/facts_validation.py`.
4. From this project's root run `NUMBA_NUM_THREADS=2 python
   research/run_reference_smoke.py`.

The script executes the unmodified reference API `Connectome()`,
`build_brains(cx, [Fly(...)])`, and `Brains.run(...)`. Pathology component
controls are supported through `Fly.kw`: `dth_max`, `syn_loss_max`,
`death_max`, and `vuln`. `stage=0` is healthy. Altering those parameters
alone does not create a validated disease model.
