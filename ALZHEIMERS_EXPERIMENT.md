# An evidence-based Alzheimer's-related experiment

Research question: **Can amyloid-associated changes in neuronal excitability
disrupt memory retention in the intact MaleCNS network, and can a circuit
intervention improve retention without changing initial learning?**

This is a proposed experiment, not a completed result. We need not simulate
every molecular pathway to test one disease-related hypothesis. Validation means
comparing specified model predictions with independent biological observations.
Successful execution and agreement between two simulators are separate checks.

## Evidence that specifies the experiment

1. **Intrinsic excitability.** Ping et al. (2015) linked human Aβ42 expression
   in flies to loss of the Kv4 potassium channel. In nine-day embryonic-derived
   neuronal cultures, firing began at 19.5 ± 2.2 pA versus 35.9 ± 4.7 pA in
   controls. This is an injected-current measurement, not a measured voltage
   threshold shift in adult MaleCNS neurons. Kv4 restoration ameliorated several
   phenotypes, but Kv4 loss alone did not produce the observed degeneration.
   [Paper, Figs 1, 4 and 9](https://doi.org/10.1371/journal.pgen.1005025).

2. **A memory phenotype and rescue.** Kaldun et al. (2021) found that
   mushroom-body-restricted Arctic Aβ42 expression spared immediate learning but
   impaired later retention. They could not exclude impaired consolidation.
   Suppressing forgetting-circuit activity improved retention; suppressing PPL1
   activity during the first two hours improved the six-hour outcome. These are
   different genotypes and protocols from Ping et al., so they must not be
   treated as a single calibration dataset.
   [Paper, Figs 1 and 3](https://doi.org/10.1371/journal.pbio.3001412);
   [underlying measurements, S1 Table](https://doi.org/10.1371/journal.pbio.3001412.s008).

3. **Existing whole-network implementation.** Jo's October 13, 2026
   [preprint](https://arxiv.org/abs/2610.19153) and
   [adfly-connectome code](https://github.com/taehojo/adfly-connectome) address
   amyloid-like perturbations on MaleCNS. They combine lower thresholds, contact
   deletion and neuronal silencing with assumed magnitudes. This is directly
   relevant prior work, not independent biological validation. Its model also
   adds adaptation and removes chemical connections within the antennal lobe;
   the reported Brian2 agreement does not validate those extensions. Inspect
   and reproduce its reference comparisons before adopting any implementation.

## What our current code lacks

The current `run_malecns.py` tests artificial LC4 stimulation and DNp01 activity
for 100 ms. It has fixed weights and no memory acquisition, retention, or
dopamine-dependent plasticity. Dopamine-labelled outputs currently receive zero
fast synaptic weight. Those neurons need an explicit modulatory learning rule;
assigning them ordinary positive weights would not supply that mechanism.

Local annotation inspection found 4,064 `KC*`, 97 `MBON*`, 316 `PAM*` and 16
`PPL1*` cells. These prefix selections are candidates, not verified matches to
the genetic drivers in the experiments. Keep all 166,700 model neurons while
auditing the affected population and its measured connections.

## Implementation and validation order

1. Build a healthy odor-conditioning assay with two odors, a specified teaching
   signal, and a documented neural readout. Establish acquisition, retention,
   sensory responses and the effect of disabling plasticity. A neural score
   must not be labelled a measured behavioral performance index.
2. Fit an intrinsic-excitability change against an appropriate electrophysiology
   protocol. Use a potassium-current model if claiming Kv4 causality; a changed
   LIF threshold is only a proxy. Do not translate the culture current ratio
   directly into a millivolt shift or apply it uniformly to adult cell types.
3. Compare baseline, altered excitability, an intervention during retention,
   and intervention-only controls using paired inputs and independent seeds.
   Test immediate and delayed memory separately. Hold out rescue conditions
   from fitting; do not hard-code a faster decay and call its recovery a discovery.
4. Audit input detection and motor/readout competence so sensory failure or
   inability to express a response cannot masquerade as forgetting. Report
   uncertainty and sensitivity to unknown parameter values and affected cells.
5. Test synapse loss and neuron loss separately in a later degeneration study.
   Match contact burden when comparing locations of damage, and record whether
   stimulus or output neurons were affected. Do not bundle these interventions
   into the first early-memory hypothesis.

Biological hours of retention and days of aging need explicit slow-state
dynamics or justified approximations; a millisecond spiking run cannot stand
in for them by relabelling its time axis. Success on the fly assay would support
that limited model. Human relevance would require separate mammalian evidence
and validation; the mouse mapping announcement alone does not supply it.
