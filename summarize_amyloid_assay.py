"""Verify and summarize the completed paired component assays."""
from pathlib import Path
import hashlib
import json
import os
os.environ.setdefault('MPLCONFIGDIR', '/private/tmp/fly-stroke-matplotlib')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'results/amyloid_reference_components'
CONDITIONS = ['baseline', 'excitability_only', 'contact_loss_only', 'cell_silencing_only',
              'combined', 'restore_excitability', 'restore_contacts', 'restore_cells']
LABELS = ['Baseline', 'Higher excitability only', 'Contact loss only', 'Cell silencing only',
          'Combined changes', 'Combined: restore excitability', 'Combined: restore contacts', 'Combined: restore cells']


def main():
    aggregates, frames = {}, {}
    for key, folder in [('reference', 'amyloid_reference_components'), ('native', 'amyloid_components')]:
        path = ROOT / 'results' / folder
        metadata = json.loads((path / 'summary.json').read_text())
        assert metadata['status'] == 'completed' and metadata['repeats'] == 6
        frame = pd.read_csv(path / 'readouts.csv')
        assert len(frame) == 648
        assert not frame.duplicated(['trial', 'condition', 'phase', 'population']).any()
        assert frame.query("condition == 'no_input' or phase == 'pre'").spikes.sum() == 0
        assert len(frame.condition.unique()) == 9
        frames[key] = frame
        aggregates[key] = {'readouts_sha256': hashlib.sha256((path/'readouts.csv').read_bytes()).hexdigest(), 'stimulus': {}}
        for population in ['all', 'KC', 'MBON', 'input']:
            table = frame.query("phase == 'stimulus' and population == @population").pivot(index='trial', columns='condition', values='spikes')
            assert (table.baseline > 0).all()
            aggregates[key]['stimulus'][population] = {}
            for condition in CONDITIONS:
                ratio = 100 * table[condition] / table.baseline
                aggregates[key]['stimulus'][population][condition] = {
                    'mean_spikes': float(table[condition].mean()), 'spikes_per_trial': table[condition].tolist(),
                    'paired_percent_baseline_mean': float(ratio.mean()),
                    'paired_percent_baseline_range': [float(ratio.min()), float(ratio.max())],
                    'paired_percent_baseline_per_trial': ratio.tolist()}
    checks = json.loads((OUT/'summary.json').read_text())['checks']
    assert len(checks) == 6 and all(c['full_restoration_exactly_matches_baseline'] for c in checks)
    fig, axes = plt.subplots(1, 2, figsize=(12, 6), sharey=True)
    colors = {'reference': '#067a8d', 'native': '#b45b3b'}
    for ax, population in zip(axes, ['KC', 'MBON']):
        for key, offset in [('reference', -.13), ('native', .13)]:
            for i, condition in enumerate(CONDITIONS):
                a = aggregates[key]['stimulus'][population][condition]
                x = a['paired_percent_baseline_per_trial']
                ax.scatter(x, np.full(6, i+offset), s=20, alpha=.38, color=colors[key])
                ax.plot(a['paired_percent_baseline_mean'], i+offset, '|', ms=13, mew=2.4, color=colors[key])
            ax.scatter([], [], color=colors[key], label='Published model' if key=='reference' else 'Original graph, no adaptation')
        ax.axvline(100, color='0.5', lw=1, ls='--')
        ax.set_title('Kenyon cells (4,064)' if population=='KC' else 'Mushroom-body outputs (97)')
        ax.set_xlabel('Stimulus spikes (% of paired baseline)')
        ax.grid(axis='x', alpha=.15)
        ax.spines[['top','right']].set_visible(False)
        ax.set_yticks(range(len(CONDITIONS)), LABELS)
    axes[0].invert_yaxis()
    axes[1].legend(loc='lower right', fontsize=8)
    fig.suptitle('Whole-CNS circuit response to amyloid-inspired perturbations', fontsize=15)
    fig.text(.02, .02, '166,700 neurons; six paired input/damage seeds; dots = runs, bars = means. 100 ms stimulus. No learned-memory test.', fontsize=9)
    fig.tight_layout(rect=[0, .06, 1, .94])
    fig.savefig(OUT/'comparison.png', dpi=180)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(10,4), sharey=True)
    for ax, key in zip(axes, ['reference','native']):
        d = frames[key].query("condition=='baseline' and population=='all'")
        for trial in range(6):
            t = d.query('trial==@trial').set_index('phase').loc[['stimulus','washout']]
            ax.plot([0,1], t.spikes/t.seconds, 'o-', alpha=.65, label=f'Seed {trial+1}')
        ax.set_xticks([0,1], ['100 ms stimulus', '150 ms after stimulus'])
        ax.set_title('Published model' if key=='reference' else 'Original graph, no adaptation')
        ax.set_yscale('log')
        ax.grid(alpha=.15)
    axes[0].set_ylabel('Whole-network spikes / second (log scale)')
    axes[1].legend(fontsize=7)
    fig.suptitle('Healthy baseline depends strongly on model assumptions')
    fig.tight_layout()
    fig.savefig(OUT/'baseline_diagnostic.png', dpi=180)
    plt.close(fig)
    (OUT/'aggregate.json').write_text(json.dumps(aggregates, indent=2)+'\n')
    lines = ['# Completed whole-CNS component experiment', '',
      '**Question:** How do higher excitability, contact loss and cell silencing change an odor-evoked response in the full fly CNS?', '',
      'Used the unmodified [Jo adfly-connectome engine](https://github.com/taehojo/adfly-connectome), commit `dcc143ec703d297739bf92f825b20dceea232505`, with its default adaptation and antennal-lobe connection suppression. This is a new controlled assay using that engine, not a reproduction of the preprint\'s disease cohorts.', '',
      '**Completed:** 54 reference-model trials (nine conditions × six paired seeds), six exact full-restoration checks, and 54 trials on the original signed graph using Brian2. Each trial includes all 166,700 neurons, 50 ms quiet, 100 ms input and 150 ms washout. These are simulation seeds, not animals.', '',
      '![Paired circuit responses](comparison.png)', '',
      '## Results', '',
      'MBON spikes below are summed across all 97 mushroom-body output neurons during the 100 ms stimulus. Percentages are means of six within-seed ratios, not ratios of pooled means. Ranges describe run variability, not confidence intervals.', '',
      '| Condition | Mean spikes | Mean % of paired baseline | Range (%) |', '|---|---:|---:|---:|']
    for condition, label in zip(CONDITIONS, LABELS):
        a=aggregates['reference']['stimulus']['MBON'][condition]
        lo,hi=a['paired_percent_baseline_range']
        lines.append(f"| {label} | {a['mean_spikes']:.2f} | {a['paired_percent_baseline_mean']:.1f} | {lo:.1f}–{hi:.1f} |")
    lines += ['', 'Combined changes reduced the stimulus response in every reference seed. Restoring contacts raised that response in every paired seed, sometimes above baseline. Restoring excitability alone usually lowered it further. This means spike response is not a monotonic measure of disease severity; these parameter reversals are not treatment predictions.', '',
      'Baseline MBON responses were sparse (8–19 spikes), so percentage changes can be large. The original-graph comparator had roughly 822 baseline spikes on average: the model assumptions change the operating regime substantially.', '',
      '![Baseline sensitivity](baseline_diagnostic.png)', '',
      'Post-stimulus activity did not reliably disappear across seeds, even with the reference defaults. The single-seed diagnostic that became silent was therefore not representative of all runs. Washout rates are normalized for its longer duration; this plot does not measure memory retention.', '',
      '## Perturbations and checks', '',
      'The same 4,064 annotated Kenyon cells were eligible for a 1 mV threshold reduction, independent 30% thinning of outgoing synaptic contacts, and independent 17% cell-silencing probability. The threshold and contact magnitudes are assumed sensitivity settings. The cell-loss setting is approximately anchored to Ping et al. Fig. 7B, but silencing is not physical degeneration and the experimental cell selection is not identical. This replaces the reference paper\'s hub-ranked severity distribution with a KC-targeted component design. Input events, lost contacts and silenced IDs are paired across conditions and engines; input neurons are protected.', '',
      'Both cohorts passed complete-output, unique-row, zero-input and quiet-preperiod checks. The reference runner confirmed silenced cells emitted no spikes and all six complete restorations reproduced baseline neuron counts exactly. The Brian2 implementation passed 21 targeted automated tests including its adapter. Prepared arrays matched the reference author\'s four numerical hashes; analysis of 159 stored reference facts reproduced exactly. These are execution/provenance checks, not disease validation.', '',
      '## What this says about Alzheimer\'s', '',
      'It demonstrates how specified amyloid-inspired circuit disturbances interact in this model. It does not simulate amyloid or tau chemistry, learn an odor association, measure hours-long forgetting, or predict human Alzheimer\'s. The model\'s optional plasticity rule was not invoked in this component assay. A separate [biological benchmark](../../research/biological_benchmarks/README.md) contains 371 published measurements for testing future retention models; [the biological memory chart](../../research/biological_benchmarks/published_memory.png) is experimental data, not this simulation.', '',
      '## Reproduce and audit', '',
      'Follow [reference setup](../../research/REFERENCE_REPRODUCTION.md) and [whole-CNS data setup](../../WHOLE_BRAIN.md). Preserve existing result folders before rerunning because runners refuse to overwrite them. Run:', '',
      '```sh', 'python run_amyloid_assay.py --repeats 6 --output results/amyloid_components', 'NUMBA_NUM_THREADS=2 python research/run_reference_components.py', 'python summarize_amyloid_assay.py', '```', '',
      'The first command uses the Brian2 Python 3.10 environment; the reference command uses Python 3.11 with Numba. Source commits, actual runner hashes, shared draw hashes, model parameters and full-restoration checks are in [summary.json](summary.json). See [readouts.csv](readouts.csv), [aggregates](aggregate.json), [native-graph outputs](../amyloid_components/summary.json), and [independent design audit](../../research/design_audit.md). Raw inputs, damage draws and native per-neuron counts are retained.']
    (OUT/'report.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(aggregates['reference']['stimulus']['MBON'], indent=2))


if __name__ == '__main__':
    main()
