# Biological benchmarks for the MaleCNS experiment

These measurements define tests a simulation can fail. They do not establish
that a changed voltage threshold represents Alzheimer's pathology.

## Original memory data

[Kaldun et al. (2021)](https://doi.org/10.1371/journal.pbio.3001412)
provides a downloadable [S1 workbook](https://doi.org/10.1371/journal.pbio.3001412.s008).
The unchanged workbook is `kaldun2021_s1.xlsx`. Run
`python3 research/biological_benchmarks/extract_benchmarks.py` from the repository
root to reproduce `kaldun2021_measurements.json`. It contains 371 observations
in 33 groups, with source cells and SHA-256 provenance. Every extracted group
mean and SEM matches the source summary within 1e-10.

`published_memory.png` plots the measured aversive time course and the separate
appetitive PPL1 intervention. Reproduce it with
`python3 research/biological_benchmarks/plot_published_memory.py` in an environment
with Matplotlib. No simulation measurements enter this chart.

Selected behavioral performance indices (mean ± SEM), adults aged 7–9 days:

| Assay / genotype | Immediate | 2 h | 6 h |
| --- | ---: | ---: | ---: |
| Aversive, UAS parental control | 63.66 ± 3.58 | 52.12 ± 5.67 | 40.06 ± 2.41 |
| Aversive, OK107 parental control | 50.52 ± 3.86 | 57.13 ± 4.47 | 42.07 ± 1.22 |
| Aversive, OK107 > Arctic Aβ42 | 62.10 ± 3.02 | 22.10 ± 7.02 | 1.69 ± 4.45 |
| Appetitive, OK107 > Arctic Aβ42 | 69.01 ± 6.38 | 40.05 ± 5.94 | 22.38 ± 7.75 |

Each entry has 12 experiments. An experiment combines reciprocal conditioning
groups of 50–100 mixed-sex flies; individual flies are not independent rows.
Immediate aversive testing occurs about three minutes after training.
Nonsignificant acquisition differences do not prove equivalence.

The separate Figure 3C rescue protocol gives 6-h appetitive PI **6.34 ± 4.83**
at room temperature versus **24.47 ± 3.71** after blocking c150-labelled PPL1
transmission during the first two hours (eight experiments per condition).
The driver and temperature controls must accompany this comparison.

## Electrophysiology calibration

[Ping et al. (2015)](https://doi.org/10.1371/journal.pgen.1005025), Figure 1,
reports first-spike current **35.9 ± 4.7 pA** for controls (13 cells), versus
**19.5 ± 2.2 pA** with elav-driven Aβ42 (six cells). The protocol ramps 0–150 pA
over one second from −50 to −60 mV. These are nine-day embryonic-derived
cultures, not adult MaleCNS cells. `ping2015_measurements.json` records the
reported uncertainty without assuming an unverified interval definition.

A LIF threshold change may reproduce one response summary, but cannot identify
Kv4 causality. An explicit potassium-current model should also reproduce
voltage-dependent first-spike latency and channel-restoration observations.
Kv4 loss alone did not reproduce the study's neurodegeneration phenotype.
No current-to-voltage conversion is supplied by these results.

## Proposed fitting and testing separation

This is a proposed analysis split, not a preregistration or completed fit.

1. Fit a single-cell ramp assay only to Ping's electrophysiology. Treat any
   transfer to adult neurons as an uncertainty analysis, not a measured mapping.
2. For a memory model, fit healthy acquisition and early retention separately
   within one conditioning assay, driver and age. If the disease 2-h score is
   also fitted, label it calibration rather than validation.
3. Reserve later time points and the Figure 3 intervention for predictions.
   Figure 3 uses MB247-LexA and c150-labelled MP1/MV1/V1 neurons, whereas Figure
   1 uses OK107. That mapping is a prerequisite, not a known identity between
   every KC/PPL1 prefix-selected connectome cell and the genetic driver.
4. Preserve temperature and driver controls. Shibire blocks transmission;
   setting neuronal voltage or firing to zero is a different intervention.
5. A simulated neural score needs a justified behavioral observation model
   before comparison in PI units. Learning, retention, sensory competence and
   response competence must be measured separately. Hours require an explicit
   slow state or justified temporal approximation.

The two papers use different Aβ constructs and preparations. Combining them
produces a hypothesis, not a single experimentally validated causal chain.
The memory evidence also permits a consolidation deficit. Neither dataset
validates a fixed-weight 100-ms firing assay as a memory experiment, or a
generic threshold proxy as a full Alzheimer's model.

## Audit of the current KC component assay

`run_amyloid_assay.py` compares 300-ms circuit responses to identical artificial
projection-neuron inputs, with a 1-mV KC threshold decrease, contact thinning,
and functional cell silencing. Its separate perturbations and paired inputs
support a controlled circuit sensitivity experiment. They do not test the
measured memory phenotype: the assay has no odor–reinforcement association,
learning-dependent synaptic state, dopamine-dependent memory regulation,
delayed behavioral readout, or biologically timed retention state.

| Criterion | Passing evidence | Current assay |
| --- | --- | --- |
| Intervention implementation | Affected cells emit no spikes; paired conditions replay identical input events; contact accounting reconciles | Technical checks available; judge from completed run outputs |
| Healthy acquisition | Trained response differs from unpaired/no-plasticity controls under a specified conditioning protocol | Not tested |
| Spared acquisition with Aβ | A justified equivalence test on immediate performance, or explicit uncertainty comparison without claiming equivalence | Not tested |
| Impaired retention with Aβ | Unfitted later readouts reproduce the within-assay direction and effect magnitude, with uncertainty and sensory/readout controls | Not tested |
| PPL1 intervention prediction | Unfitted first-two-hour transmission blockade improves six-hour memory with driver and temperature controls | Not tested |
| Kv4 mechanism | A conductance model predicts an independent current/latency protocol and channel-restoration measurements | Not tested by a threshold proxy |

Reject a claim of biological memory validation if any required memory criterion
is untested. This is absence of a validation test, not evidence that the model
has already made and failed a memory prediction. Pass/fail tolerances and an
observation model must be specified before fitting; this review does not invent
an acceptable error range after seeing simulation results. A cell-count loss
anchor (such as 17%) additionally needs its exact paper, age, anatomical region,
and experimental unit; functional silencing is an approximation to that loss.
