# Fly memory and Alzheimer's: first experiment

Status: first computational pilot executed on 24 October 2026. See [results](results/report.md) and [implemented methods](METHODS.md). The healthy reference was reproduced, exploratory phase perturbations and controls were run, and parameter sensitivity was checked. No animal experiments or disease-specific model fitting were performed. The spontaneous-activity exploration was limited to a tonic dopamine drive; the model lacks ongoing Kenyon-cell activity during silent waiting.

## Question

Does Alzheimer's-related circuit dysfunction impair forming, retaining, or retrieving an odor memory, and which predictions could be tested against human evidence?

We will start with a computational model of the fly mushroom body, a memory circuit. The eventual human goal is to identify a plausible mechanism and a distinguishing prediction, not to convert fly performance into a person's symptoms.

## Evidence that shapes the design

In one fly experiment, restricting the Arctic variant of human amyloid-beta to mushroom-body neurons left immediate memory performance comparable to controls but reduced later performance. The authors interpreted this as accelerated forgetting while explicitly retaining impaired consolidation as an alternative. Effects depended on age and where the peptide was expressed. This is a useful target pattern, not a universal account of Alzheimer's. [Kaldun et al., PLOS Biology, 2021](https://journals.plos.org/plosbiology/article?id=10.1371/journal.pbio.3001412)

A published mushroom-body model combines connectivity and physiological measurements to study interactions between short- and long-term learning modules. Its authors provide code. It is a candidate starting point; reproducing its healthy results must precede any disease extension. It is not a complete FlyWire brain or a validated Alzheimer's model. [Huang, Luo et al., Nature, 2024](https://www.nature.com/articles/s41586-024-07819-w); [author code](https://github.com/schnitzer-lab/Luo_Huang_2024_MB_model).

In a small human study with 21 participants, hippocampal SV2A PET binding, a proxy for synaptic density, correlated with episodic memory across the combined clinical and control sample. This supports investigating a synapse–memory relationship but does not distinguish encoding, retention, or retrieval, or establish causation. [Chen et al., JAMA Neurology, 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC6233853/)

## Experiment

First reproduce the candidate model's published healthy conditioning and memory dynamics using its native protocol. Use an odor paired with reinforcement and an unpaired control odor. Its initial aversive protocol differs from the earlier food example; a reward-learning extension would require its own validation.

Then apply each candidate disturbance in separate phases:

| Condition | Learning phase | Waiting phase | Recall test | Purpose |
|---|---|---|---|---|
| Healthy reference | Healthy | Healthy | Healthy | Establish baseline learning and retention |
| Learning perturbation | Disturbed | Healthy | Healthy | Test impaired formation |
| Retention perturbation | Healthy | Disturbed | Healthy | Test changes occurring after learning |
| Recall perturbation | Healthy | Healthy | Disturbed | Test impaired expression of an established memory |
| Persistent perturbation | Disturbed | Disturbed | Disturbed | Compare with sustained dysfunction |

These reversible manipulations are tools for separating mechanisms in a model; they do not imply that biological Alzheimer's damage switches on and off.

Test candidate mechanisms separately: reduced synaptic transmission, impaired learning-related plasticity, and altered spontaneous activity. A faster memory-decay parameter may serve as a descriptive benchmark, but building faster forgetting into the model cannot demonstrate why it happens. Disease-specific parameter values must come from experiments; arbitrary parameter sweeps must be labelled exploratory.

Measure the learned response to each odor immediately and after delays, alongside synaptic state and activity in the model. Use the published model's response measure before adding any behavioral readout. Map simulated intervals to hours only after validating the time scale. An immediate test can itself change a memory: evaluate each delay on a separate cloned state or independent replicate.

## Controls and interpretation

- Swap the paired odor and include unpaired reinforcement and no-learning controls.
- Check odor discrimination and output responsiveness so sensory or general response failure is not mislabelled as memory loss.
- Pair starting states across conditions. For stochastic models, report variation across independent runs; for deterministic models, report parameter sensitivity. Simulation runs are not biological sample sizes.
- Predefine exploratory parameter ranges and reserve a delay or perturbation response for evaluation after fitting. Show absolute performance as well as change from baseline.
- Poor immediate performance can involve formation or expression. Poor delayed performance alone cannot distinguish unstable storage, consolidation failure, and retrieval difficulty.
- Restoring transmission during recall, without retraining, can test whether the model retains accessible information. Recovery would support an expression deficit within that model, not prove a human treatment effect.

## Human connection

The transferable prediction is a pattern: impaired initial acquisition, disproportionate loss after a delay, or impaired access despite a retained trace. Compare these predictions with appropriately designed human memory studies that measure learning and delayed performance separately, preferably alongside relevant biological markers.

SV2A PET binding is not synaptic strength or plasticity. A percentage reduction in model weights must not be equated with a percentage reduction in PET signal. Likewise, the fly mushroom body is not a one-to-one anatomical substitute for the human hippocampus.

## First deliverable

Reproduce healthy learning from the published model, then report which disturbances can reproduce preserved immediate performance with poorer delayed performance. Preserve a competing explanation when several mechanisms fit. Record model version, configuration, data provenance, and all attempted conditions. A successful fit generates a hypothesis for further fly and human work; it does not establish the cause of human Alzheimer's memory loss.
