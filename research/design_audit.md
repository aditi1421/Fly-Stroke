# Design audit: an amyloid-inspired full-CNS circuit experiment

Audit date: 2026-10-24. This is an independent design review, not a report of
new simulations or biological validation. Reviewed `run_malecns.py`,
`prepare_malecns.py`, `ALZHEIMERS_EXPERIMENT.md`, the prepared MaleCNS manifest
and annotations, and `adfly-connectome` commit
`dcc143ec703d297739bf92f825b20dceea232505`.

## Decision

Run a paired **circuit-function perturbation experiment** with all 166,700
MaleCNS neurons retained. The current fixed-weight LIF model can test how
assumed excitability, contact loss and neuronal silencing alter circuit
responses. It cannot establish Alzheimer's causation, memory retention, or a
human treatment. State the imposed mechanisms and their arbitrary magnitudes
beside the results. This is useful mechanistic hypothesis testing even when
the answer differs from expectations.

The existing memory proposal remains a separate scientific objective. A
short odor-response assay does not complete its learning/retention aims.

## What the newer reference actually contributes

[Jo's October 2026 preprint](https://arxiv.org/pdf/2610.19153), pp. 6–9,
uses threshold lowering, contact thinning and neuron silencing; their sizes
are assumed. It adds adaptation and removes chemical connections within the
antennal lobe to suppress persistent odor activity. The reported comparison
with Brian2 excludes those extensions. Thus the paper supplies a reproducible
modeling precedent, not a calibration of adult CNS disease severity.

The local reference code confirms those choices in
`code/adfly/model.py` (`Connectome.al_edge`, `build_brains`) and documents them
in its module docstring. Its `learn` function explicitly depresses selected
KC→MBON weights after pairing. A resulting neural learning score therefore
requires additional controls before being treated as a prediction of memory.
[Reference repository](https://github.com/taehojo/adfly-connectome).

**Antennal-lobe changes should not be adopted silently for this assay.** They
are a workaround for the reference model's odor dynamics, rather than
evidence that the anatomical edges should be removed. Preserve native edges
in the primary experiment. If later odor simulations persist or recruit
unreasonably many cells, document that failure and compare native wiring,
adaptation alone, and the reference feedforward approximation as explicitly
different model variants. Do not tune wiring until an expected disease
effect appears. A graph with all vertices but removed AL connections is not
the same intact-connectome model.

## Bounded paired design

The agreed first cohort is six independent simulated individuals, each
run through nine conditions. This is a pilot size, not a power calculation.
Use an independent random stream for each individual's stimulus, synapse
loss, and neuron loss; save seeds and mask hashes. Reuse the exact input
events and underlying damage masks in component and combined comparisons.
Rebuild or restore all neural state, delayed events and monitors each trial.

Agreed protocol: 50 ms unstimulated, 100 ms of 150 Hz direct projection-neuron
drive, then 150 ms with drive removed. The eight ALPN cells matching
`^(DM1|DM4|VA2)_` are body IDs 10176, 10208, 10390, 10561, 10613, 10670,
71476 and 73492. These are modeling choices; this bypasses olfactory receptor
processing and is not a full natural-odor stimulus. Inspect recovery rather
than silently deleting recurrent connections if activity persists. Given the
reference model's known odor attractor, a 150 ms washout is a diagnostic, not
proof of stable healthy odor processing.

Only the 4,064 prefix-selected Kenyon cells are eligible for damage: a 1 mV
threshold decrease, outgoing contact thinning with probability 0.30, and
neuronal silencing with probability 0.17. The first two magnitudes are assumed.
The last loosely anchors the expected cell-loss fraction to one reported
MB-restricted fly experiment, but is not a fitted cross-genotype calibration
or an age mapping. All other CNS cells remain simulated. Input PNs and MBON
readout cells are protected by this restricted damage scope.

| Condition | Manipulation | Role |
|---|---|---|
| No drive | Healthy network, no external events | Numerical/rest control |
| Baseline | Healthy network, fixed stimulus events | Paired comparator |
| Excitability only | Lower selected cells' intrinsic spike threshold | Proxy for increased intrinsic excitability |
| Contact loss only | Binomial thinning of integer contact counts | Distinguish structural loss from uniform weight scaling |
| Neuron loss only | Fixed sampled cells unable to spike | Independent degeneration proxy |
| Combined | Same thresholds, contact draws and dead-cell mask | Test interaction of mechanisms |
| Contact restoration | Combined, restore lost contacts only among surviving cells | Conditional model attribution |
| Excitability normalization | Combined, restore original thresholds only | Distinguish compensatory excitation from impairment |
| Neuron restoration | Combined, allow selected cells to spike again, with other damage retained | Conditional model attribution |

An optional full-restoration test is an informative implementation check.
Full restoration should reproduce the
paired baseline exactly when all state and input events match. It is not a
treatment discovery. Partial restoration leaves other damage intact and is
the more informative counterfactual. Call every restoration a modeled
counterfactual, not demonstrated therapeutic rescue.

The chosen KC cohort uses uniform vulnerability within that population.
Any later hub map imports an extra assumption, and equal neuron-loss
fractions do not equalize synaptic burden. Do not attribute differences
between maps to location unless contact loss and input/output exposure are
also controlled. Candidate sensitivity runs can use half and twice the
chosen perturbation, provided thresholds stay above resting potential and
probabilities remain valid. Severity is not fly age or a clinical stage.

## Target and readout audit

The initial olfactory readouts should include all 4,064 KCs and all 97 MBONs
with fixed denominators, plus surviving-cell summaries clearly identified.
Record direct PN event delivery and PN firing separately. With no training
or plasticity mechanism, these rates measure evoked neural responses, not
learning or memory.

For a subsequent independent visual control, local prepared annotations
contain 71 left/55 right LC4 cells and 94 left/91
right LPLC2 cells. DNp01 has two cells: body ID 10010 on the left and 10001 on
the right. Select exact recorded IDs and retain them in experiment metadata.
Unilateral stimulation should report ipsilateral DNp01 separately from the
bilateral mean. The latter can conceal the loss of one command neuron.

For a subsequent mushroom-body study, the prefix selections currently give
4,064 KC, 97 MBON, 316 PAM and 16 PPL1 cells. These counts do not establish
equivalence to a particular experimental genetic driver. Inspect annotation
class and compartment before claiming such a match.

Required response measures:

1. Nonstimulated-cell spike count during drive: the primary propagation
   measure, with a fixed population denominator for rates.
2. KC and MBON spike counts/rates and recruitment fractions during stimulus
   and washout. If subsequently running the visual assay, report DNp01 rates
   by side and first-spike latency. No response has missing/censored latency,
   not zero latency.
3. Total CNS spikes and active-cell fraction; include silenced cells in
   denominators, and optionally report survivor rates separately.
4. Injected event count and actual stimulated-cell spike count. Identical
   input events need not imply identical source spiking: recurrent input
   changes the source neurons' responses.
5. Post-stimulus activity and rate time courses to reveal persistent activity
   or near-refractory saturation hidden by totals.
6. Lost neuron counts by class; contact loss separately due to thinning and
   dead endpoints, without counting their overlap twice; input and readout
   cells affected; lost excitatory and inhibitory contacts separately.

The previous baseline illustrates item 4: trial 0 gave 2,214 LC4 spikes at
baseline versus 2,078 after weight scaling with the same seed. This is
compatible with changed recurrent input, not proof of changed Poisson draws.
The agreed KC-only scope protects input and output populations from direct
lesion. A pan-neuronal extension would need an input-protected companion
comparison before attributing reduced downstream activity specifically to
internal processing failure. If the
readout itself is silenced, report that direct consequence separately.

## Acceptance criteria before interpreting results

- **Identity and provenance:** all 166,700 nodes retain their original IDs;
  manifest/checksums are verified; prepared baseline has 25,582,938 directed
  anatomical edges and 124,177,617 contacts. Report the 1,113,526 zero-weight
  edges separately. Recorded anatomy is broader than modeled dynamics.
- **Component isolation:** a zero-severity condition equals baseline;
  threshold-only leaves contacts and dead mask unchanged; contact-only
  preserves signs and uses nonnegative integer counts no larger than the
  original; dead cells emit no spikes even when directly stimulated.
- **Pairing:** identical externally supplied event arrays have matching
  hashes across paired conditions. Repeated identical runs match counts;
  independent seeds actually change input/damage realizations. Do not use
  all neurons as independent statistical replicates.
- **Restoration:** full restoration exactly reproduces baseline; partial
  restoration does not alter the nonrestored component or resurrect contacts
  through still-dead endpoints. Zero damage makes every restoration a no-op.
- **Numerics:** verify synaptic delay, refractory handling, inhibition and
  threshold shift on a small directed network. With a new engine, compare
  per-neuron counts/spike times against Brian2 on identical event inputs,
  not only a high correlation dominated by a few active neurons. A longer
  stimulus run at a finer time step should not reverse the main comparison;
  any important sensitivity must be reported.
- **Healthy assay:** stimulus produces downstream activity, no-drive remains
  at rest under the stated deterministic baseline, and no numerical NaNs
  appear. A silent no-drive model is an implementation control, not realistic
  evidence about spontaneous fly-brain activity.
- **Statistics:** publish every individual and paired difference; summarize
  uncertainty across independent individuals. Bootstrap whole paired
  individuals, never neurons. With a small cohort, emphasize distributions
  and effect sizes rather than a definitive significance claim.

## Red flags that constrain the conclusion

Glutamate is assigned a universally inhibitory sign, unknown/modulatory
transmitters have zero fast output, and all neurons share most membrane
parameters. These are approximations, including for dopamine-dependent
learning. The connectome contains CNS/VNC neurons, so "whole CNS" is the
accurate scope. Direct 150 Hz drive is artificial stimulation, not a natural
odor or looming image. A lowered LIF voltage threshold is not a measured Kv4 conductance
change. Reduced synapse numbers can remove inhibition as well as excitation;
the sign of the effect must emerge from the simulation. A lower total spike
count is not automatically worse function. Damage and counterfactual reversal
under assumed rules cannot validate Alzheimer's biology or predict humans.

This pilot is complete when its controls, paired cohort, figures, provenance
and limitations are delivered. Biological validation remains a separate
comparison with independent fly measurements; it cannot be declared by
passing software tests or matching another simulator.
