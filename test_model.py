"""Numerical and causal-control checks for the research prototype."""
from dataclasses import replace

import numpy as np
import pytest
from scipy.io import loadmat

from model import (ROOT, Event, Perturbation, State, advance, decay_factors,
                   figure5d_protocol, load_parameters, simulate)
from reproduce_baseline import FIGURE_FILE, find_images
from run_experiment import StudyConfig, evaluate, probe, protocol


@pytest.fixture
def config():
    return StudyConfig.model_validate_json((ROOT / "study_config.json").read_text())


def test_author_figure_numeric_reference():
    images = list(find_images(loadmat(FIGURE_FILE, simplify_cells=True)["hgS_070000"]))
    reference = np.array([image["CData"] for image in images]).reshape(6, 3, 9, 12)
    for v_index, valence in enumerate(range(-4, 5)):
        for t_index, seconds in enumerate(range(300, 3601, 300)):
            result = simulate(load_parameters(valence=float(valence)), figure5d_protocol(seconds)).imaging
            predicted = np.stack([result[:, 0, -1] - result[:, 0, 0],
                                  result[:, 1, -1] - result[:, 1, 0],
                                  result[:, 0, -1] - result[:, 1, -1]], axis=1)
            np.testing.assert_allclose(predicted, reference[:, :, v_index, t_index], rtol=0, atol=1e-8)


def test_decay_switch_matches_analytic_split():
    p = load_parameters()
    # An event starts two hours after training and ends four hours after it.
    expected = np.exp(-3600 / p.decay[[0, 1, 1]] - 3600 / p.decay[[0, 2, 2]])
    np.testing.assert_allclose(decay_factors(p, 7200., 14400.), expected)
    a = decay_factors(p, 3600., 10800.)
    b = decay_factors(p, 3600., 14400.)
    np.testing.assert_allclose(a * b, expected)


@pytest.mark.parametrize("mechanism", ["transmission", "plasticity", "tonic_dopamine", "decay_benchmark"])
def test_zero_intervention_is_identity(config, mechanism):
    p = load_parameters()
    events = protocol(config, 7200.)
    base = simulate(p, events)
    changed = simulate(p, events, Perturbation(mechanism, "persistent", 0.))
    np.testing.assert_array_equal(base.weights, changed.weights)
    np.testing.assert_array_equal(base.activity, changed.activity)


def test_probe_does_not_change_stored_memory(config):
    p = load_parameters()
    state = simulate(p, protocol(config, 7200.)).final_state
    before = state.copy()
    normal = probe(p, state, 7200., None)
    probe(p, state, 7200., Perturbation("transmission", "recall", .5))
    np.testing.assert_array_equal(state.delta, before.delta)
    np.testing.assert_array_equal(state.adaptation, before.adaptation)
    np.testing.assert_array_equal(probe(p, state, 7200., None), normal)


def test_recall_transmission_restoration_recovers_original_response(config):
    p = load_parameters()
    base = evaluate(p, config, 7200., None)
    changed = evaluate(p, config, 7200., Perturbation("transmission", "recall", .25))
    assert abs(changed[-1]["memory_signal_hz"] - base[-1]["memory_signal_hz"]) > .01
    for original, restored in zip(base, changed):
        assert restored["stored_trace"] == original["stored_trace"]
        assert restored["restored_signal_hz"] == original["memory_signal_hz"]


def test_no_learning_and_swapped_odors(config):
    p = load_parameters()
    change = Perturbation("tonic_dopamine", "persistent", 2.)
    a = evaluate(p, config, 7200., change)
    b = evaluate(p, config, 7200., change, swap=True)
    disabled = evaluate(p, config, 7200., change, no_learning=True)
    for first, second, third in zip(a, b, disabled):
        assert first["memory_signal_hz"] == pytest.approx(second["memory_signal_hz"], abs=1e-10)
        assert third["memory_signal_hz"] == pytest.approx(0., abs=1e-10)


def test_silent_waiting_has_no_activity_dependent_learning(config):
    p = load_parameters()
    baseline = simulate(p, protocol(config, 7200.))
    for mechanism, strength in (("transmission", .25), ("plasticity", .25), ("tonic_dopamine", 2.)):
        altered = simulate(p, protocol(config, 7200.), Perturbation(mechanism, "waiting", strength))
        np.testing.assert_array_equal(altered.final_state.delta, baseline.final_state.delta)


def test_paired_and_unpaired_protocols_are_duration_matched(config):
    p = protocol(config, 7200., paired=True)
    u = protocol(config, 7200., paired=False)
    assert [(e.odor, e.duration) for e in p] == [(e.odor, e.duration) for e in u]
    assert sum(e.duration * e.punishment for e in p) == sum(e.duration * e.punishment for e in u)
    assert all(e.odor == (0., 0.) for e in u if e.punishment)
