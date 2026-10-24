# Methods and interpretation

## Source and scope

This project translates the deterministic, three-module recurrent model from Huang, Luo et al., Nature (2024), DOI 10.1038/s41586-024-07819-w. Source commit: `5d7c08a9a88f923169a0c3008aca68af421e9a7f`.

There are six modeled DAN/MBON activity variables, two odor input channels, and three learned effective KC-to-MBON weights per odor. This is not the full FlyWire connectome. The source's steady-state solver uses ten fixed-point updates; the translation preserves those iterations and the upstream initial matrix orientation. Adaptation, baseline offsets, output limits and the three-hour decay switch are preserved.

## Healthy reference

`reproduce_baseline.py` recreates the Figure 5d protocol and compares all 18 numeric heatmaps with CData extracted from the authors' saved MATLAB `.fig`. This is stronger than visual comparison, but covers one saved figure. We did not rerun MATLAB or reproduce every figure. Several other upstream plotting scripts refer to a function name absent from the repository; the chosen reproduction uses the available source function directly.

## Pilot protocol

The healthy imaging preamble is followed by six aversive training bouts. Each contains paired odor for 30 s, 135 s without odor, control odor for 30 s, and a final 135 s without odor. The last interval is represented as 30 + 105 s in both arms. In the paired arm, punishment coincides with the first odor. In the unpaired arm, equal-duration punishment occurs in the 30 s portion of the last interval with no odor input. Total time and odor exposure are matched.

The learning intervention covers the training block, including its interstimulus intervals. Waiting begins at the end of that block, including the last 135 s interval. Thus zero waiting time does not mean zero time since the last paired stimulus. The model inherits time constants expressed in seconds; these times are not human disease progression times.

After each waiting interval, each odor is probed for 5 s from a separate clone of the same state. The response is taken before any probe-induced weight update, and no clone is reused for another odor or delay. The full training protocol is independently rerun for each delay. Probe adaptation follows the source equation; probe plasticity and decay updates are omitted because they occur after the measured response.

## Exploratory interventions

| Name | Implementation | Strengths |
|---|---|---|
| transmission | Multiply effective KC-to-MBON couplings by `1 − strength` during the selected phase; retain stored weight changes | 10%, 25%, 50% |
| plasticity | Multiply new learning-related weight updates by `1 − strength`; preserve existing trace decay | 10%, 25%, 50% |
| tonic_dopamine | Add a common drive to all three DAN inputs and the corresponding teaching-signal term | 0.5, 2, 5 Hz |
| decay_benchmark | Multiply all decay time constants by `1 − strength` during the selected phase | 10%, 25%, 50% shorter constants |

The first three are exploratory circuit manipulations, not measurements of Alzheimer's severity. The decay manipulation directly assumes faster forgetting and serves only as a descriptive benchmark. Effective KC-to-MBON couplings can be signed in the source model; scaling them does not simulate deleting a percentage of anatomical synapses.

Each intervention is confined to learning, waiting, recall, or all three phases. Baseline imaging is always unperturbed. During waiting the source model has zero odor input, so input-gated plasticity cannot be driven by tonic DAN activity alone. No unobserved background KC activation was introduced to force a retention effect.

## Measurements

The primary outcome is the MBON alpha3 response contrast:

`S = (response_CS− − response_CS+)_paired − (response_CS− − response_CS+)_unpaired`

The response is in model Hz relative to the source baseline. The same contrasts are recorded for gamma1 and alpha2. We also retain all raw paired and unpaired odor responses to expose broad gain changes and nonlinear response limits. This readout is a circuit-response proxy, not a behavioral performance index, memory accuracy, or direct information measure.

The stored-trace measure applies the same paired-minus-unpaired subtraction to the learned weight difference `delta_CS− − delta_CS+`. It measures the source model's stored state, not a biological engram. The restoration probe uses that same state with the intervention absent; it does not retrain the circuit or rebuild a healthy state.

The source model's adaptation and bounded responses can conceal or amplify trace changes. Consequently, a delayed response curve need not track the stored trace monotonically. Attenuating all transmission during recall can also reduce unlearned odor responses, so an observed deficit cannot automatically be called memory-specific.

## Sensitivity and controls

Mean-parameter sweeps use odor valences −3, 0 and +3. The primary analysis was set to neutral valence and alpha3 before the run. One hundred indices are sampled without replacement from the authors' 10,000 supplied parameter draws using seed 20261024; indices are recorded in the manifest. These are parameter sensitivity checks, not additional flies or people, and their percentiles are not biological confidence intervals.

Odor-label swapping and zero-plasticity controls are evaluated for every intervention at zero and two-hour waits. Unit tests cover the source numeric reference, the three-hour decay switch, zero-strength interventions, clone independence, restoration, silent-waiting gating, and equal-duration pairing controls. The model has no explicit peripheral olfactory system or motor system, so these controls cannot establish biological sensation or movement is preserved.

The six-hour delay is reserved for checking whether the pattern persists; no fitting is performed anywhere. The qualitative early/delayed screen uses thresholds from `study_config.json`. A successful screen is not a quantitative reproduction of the Alzheimer's fly study.
