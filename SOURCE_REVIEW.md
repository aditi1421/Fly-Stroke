# Source review — 24 October 2026

## Which Google project?

The recent fly announcement is **MaleCNS**, a collaboration involving Google
Research, HHMI Janelia, Cambridge and MRC LMB. It is a measured wiring dataset,
not a pretrained brain or a disease simulator. The September 3, 2026
announcement describes the male brain and ventral nerve cord. The project's
release notes date v1.0 to June 8, 2026.

- [Google announcement](https://research.google/blog/a-connectomics-milestone-mapping-the-complete-male-fruit-fly-brain/)
- [Official releases](https://male-cns.janelia.org/release/)
- [Official data and download instructions](https://male-cns.janelia.org/download/)

Google DeepMind and Janelia's **Flybody** is a different component: an anatomical
body, MuJoCo physics, and locomotion control tasks. Its accompanying Nature paper
is from 2025. It could provide a body for future experiments; connecting it to
the measured connectome requires an explicitly designed neural-to-motor interface.

- [Flybody code and publication](https://github.com/TuragaLab/flybody)

## What awesome-fly provides

[awesome-fly](https://github.com/cobanov/awesome-fly) is a curated directory of
datasets, neural simulators, bodies, viewers and community demonstrations. Its
linked starter supplies a MaleCNS soma atlas, Flybody mesh and web workbench;
the user supplies the brain model. Neither the directory nor the starter is a
validated disease simulator.

Useful projects inspected:

- [fault-lines](https://github.com/dhruvin-sarkar/fault-lines) tests targeted versus
  random removal on a cell-type-aggregated MaleCNS graph. Its routing controls
  could inform lesion experiments. The authors explicitly describe static graph
  results, without neural dynamics, rather than disease or behavior predictions.
- [MaleCNS on Apple MPS](https://github.com/seohyunjun/mps-malecns-model) supplies
  an experimental simulator and data preparation. Its own documentation states
  that its stimulation example activates only the two directly stimulated cells.
  Its normalized, dimensionless LIF rules differ from the Shiu model; switching
  to it would change both the data and the dynamics. We did not install or copy it.
- [Eon fly-brain](https://github.com/eonsystemspbc/fly-brain) offers multiple
  backends of the Shiu model. It still uses FlyWire; a newer implementation date
  alone does not make it the MaleCNS dataset.

## Decision implemented here

Use the official MaleCNS v1.0 tables, with all annotated neuronal superclasses
and connections between them, in a new `prepare_malecns.py` adapter. Keep the
published Shiu Brian2 dynamics as an explicitly identified modeling assumption
in `run_malecns.py`. This is **new connectivity with transferred dynamics**, not
an official Google simulator or a reproduction of a validated MaleCNS model.
Keep the previous FlyWire and reduced-memory results separately.

First establish reproducible stimulation, no-input controls, and downstream
activity. A uniformly weakened-weight condition is a generic sensitivity check;
an Alzheimer's interpretation needs independently supported mechanisms,
parameter ranges and behavioral validation. No such disease claim is made here.

## Mouse-brain link

The [provided Google article](https://research.google/blog/google-research-embarks-on-effort-to-map-a-mouse-brain/)
is dated September 26, 2023. It announces a five-year effort to map the
hippocampal formation, approximately 2–3% of the mouse brain. The article does
not supply a completed whole-mouse connectome or runnable Alzheimer's model.
We use it as research context, not input data for this fly simulation.

A separate available resource, [MICrONS](https://www.microns-explorer.org/cortical-mm3),
contains wiring and activity measurements from a cubic-millimeter volume of
mouse visual cortex. That could support a later mammalian circuit comparison;
it is a different region and project, and is not an Alzheimer's dataset.
No mouse data was downloaded or combined with the fly graph.
