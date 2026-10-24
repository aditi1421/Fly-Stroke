"""Checks for paired inputs, independent lesions and actual tiny-network runs."""
import json

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("brian2")
import run_amyloid_assay as assay
from prepare_malecns import sha256


def test_input_events_replay_bounds_uniqueness_and_distinct_seeds():
    indices, times = assay.input_events(8, 123)
    replay_i, replay_t = assay.input_events(8, 123)
    other_i, other_t = assay.input_events(8, 124)
    np.testing.assert_array_equal(indices, replay_i)
    np.testing.assert_array_equal(times, replay_t)
    assert len(times) > 0
    assert indices.dtype == np.int32
    assert np.all((indices >= 0) & (indices < 8))
    start, duration = assay.PHASES[0][1], assay.PHASES[1][1]
    assert np.all((times >= start) & (times < start + duration))
    assert np.all(np.diff(times) >= 0)
    bins = np.rint((times - start) / .0001).astype(int)
    assert len(set(zip(indices, bins))) == len(times)
    assert not (np.array_equal(indices, other_i) and np.array_equal(times, other_t))


def test_input_probability_endpoints():
    zero_i, zero_t = assay.input_events(3, 4, rate_hz=0)
    assert zero_i.size == zero_t.size == 0
    all_i, all_t = assay.input_events(3, 4, rate_hz=10000)
    assert len(all_i) == 3 * round(assay.PHASES[1][1] / .0001)
    np.testing.assert_array_equal(np.bincount(all_i), [1000, 1000, 1000])
    assert len(np.unique(all_t)) == 1000


@pytest.mark.parametrize("rate,dt", [(-1, .0001), (10001, .0001),
                                    (150, 0), (-150, -.0001),
                                    (np.nan, .0001), (150, np.nan)])
def test_invalid_input_probabilities_and_time_steps(rate, dt):
    with pytest.raises(ValueError):
        assay.input_events(8, 1, rate_hz=rate, dt_seconds=dt)


@pytest.mark.parametrize("probability", [0., .3, 1.])
def test_damage_integer_contact_limits_and_target_restriction(probability):
    contacts = np.array([1, 12, 2, 100, 6], dtype=np.int64)
    target_edges, target_cells = np.array([1, 3]), np.array([1, 4, 8])
    kept, dead = assay.damage_draw(contacts, target_edges, target_cells, 10, 22,
                                 contact_loss=probability, cell_loss=probability)
    assert np.issubdtype(kept.dtype, np.integer)
    assert np.all((kept >= 0) & (kept <= contacts[target_edges]))
    assert dead.dtype == bool and dead.shape == (10,)
    assert not dead[np.setdiff1d(np.arange(10), target_cells)].any()
    if probability == 0:
        np.testing.assert_array_equal(kept, contacts[target_edges])
        assert not dead.any()
    if probability == 1:
        np.testing.assert_array_equal(kept, np.zeros(2))
        np.testing.assert_array_equal(np.flatnonzero(dead), target_cells)


def test_damage_streams_are_independent_and_replayable():
    contacts = np.arange(1, 1001, dtype=np.int64)
    target_edges = np.arange(1000)
    target_cells = np.arange(1000)
    args = (contacts, target_edges, target_cells, 1000, 73)
    kept, dead = assay.damage_draw(*args)
    again_kept, again_dead = assay.damage_draw(*args)
    np.testing.assert_array_equal(kept, again_kept)
    np.testing.assert_array_equal(dead, again_dead)
    # Changing the number of contact RNG draws must not move cell-loss draws.
    _, fewer_edge_dead = assay.damage_draw(contacts, target_edges[:3],
                                         target_cells, 1000, 73)
    np.testing.assert_array_equal(dead, fewer_edge_dead)
    _, no_contact_loss_dead = assay.damage_draw(*args, contact_loss=0)
    np.testing.assert_array_equal(dead, no_contact_loss_dead)
    different_cell_loss_kept, _ = assay.damage_draw(*args, cell_loss=.9)
    np.testing.assert_array_equal(kept, different_cell_loss_kept)
    changed_kept, changed_dead = assay.damage_draw(
        contacts, target_edges, target_cells, 1000, 74)
    assert not np.array_equal(kept, changed_kept)
    assert not np.array_equal(dead, changed_dead)


@pytest.mark.parametrize("contact,cell", [(-.1, .1), (1.1, .1), (.1, -.1),
                                          (.1, 1.1), (np.nan, .1)])
def test_damage_rejects_invalid_probabilities(contact, cell):
    with pytest.raises(ValueError):
        assay.damage_draw(np.array([4]), np.array([0]), np.array([0]), 1, 2,
                          contact_loss=contact, cell_loss=cell)


def test_conditions_isolate_components_and_restore_only_one():
    conditions = {item.name: item for item in assay.CONDITIONS}
    assert len(conditions) == len(assay.CONDITIONS) == 9
    flags = lambda item: (item.excitation, item.contact_loss, item.cell_loss)
    assert flags(conditions["baseline"]) == (False, False, False)
    assert flags(conditions["no_input"]) == (False, False, False)
    assert not conditions["no_input"].stimulated
    assert all(item.stimulated for name, item in conditions.items() if name != "no_input")
    assert flags(conditions["excitability_only"]) == (True, False, False)
    assert flags(conditions["contact_loss_only"]) == (False, True, False)
    assert flags(conditions["cell_silencing_only"]) == (False, False, True)
    assert flags(conditions["combined"]) == (True, True, True)
    assert flags(conditions["restore_excitability"]) == (False, True, True)
    assert flags(conditions["restore_contacts"]) == (True, False, True)
    assert flags(conditions["restore_cells"]) == (True, True, False)


def test_tiny_network_replay_silencing_burden_and_full_restoration(tmp_path, monkeypatch):
    """Execute the actual Brian2 runner, not a mocked dynamics implementation."""
    data = tmp_path / "data/malecns"
    data.mkdir(parents=True)
    n_inputs, n_kc = len(assay.ODOR_A_IDS), 16
    n = n_inputs + n_kc + 1
    cells = pd.DataFrame({
        "body_id": assay.ODOR_A_IDS + list(range(100000, 100000 + n_kc)) + [200000],
        "cell_type": ["PN"] * n_inputs + ["KCtest"] * n_kc + ["MBONtest"],
    }).rename_axis("neuron_index")
    cells.to_csv(data / "neurons.csv")
    edges = pd.DataFrame({
        "Presynaptic_Index": list(np.repeat(np.arange(n_inputs), 2)) + list(range(n_inputs, n - 1)),
        "Postsynaptic_Index": list(range(n_inputs, n - 1)) + [n - 1] * n_kc,
        "contacts": [100] * (2 * n_kc),
        "Excitatory x Connectivity": [100] * (2 * n_kc),
    })
    edges.to_parquet(data / "connections.parquet", index=False)
    (data / "manifest.json").write_text(json.dumps({"prepared_files": {
        filename: {"sha256": sha256(data / filename)}
        for filename in ("neurons.csv", "connections.parquet")}}))
    engine_dir = tmp_path / "whole_brain_upstream"
    engine_dir.mkdir()
    # The imported engine still comes from the real repository. This copy is
    # only the provenance file the runner hashes under the temporary ROOT.
    original_root = assay.ROOT
    (engine_dir / "model.py").write_bytes((original_root / "whole_brain_upstream/model.py").read_bytes())
    monkeypatch.setattr(assay, "ROOT", tmp_path)
    monkeypatch.setattr(assay, "CONDITIONS", assay.CONDITIONS + (assay.Condition("full_restoration"),))
    output = tmp_path / "output"
    result = assay.run(output, repeats=1, seed=20261024)
    assert result["status"] == "completed"
    assert all(item["silenced_cells_emit_zero"] for item in result["checks"])
    assert all(item["pre_input_spikes"] == 0 for item in result["checks"])
    readouts = pd.read_csv(output / "readouts.csv")
    assert readouts.loc[readouts.condition.eq("no_input"), "spikes"].eq(0).all()
    identity = ["phase", "population", "neurons", "surviving_neurons", "spikes", "active_neurons"]
    baseline = readouts[readouts.condition.eq("baseline")][identity].reset_index(drop=True)
    restored = readouts[readouts.condition.eq("full_restoration")][identity].reset_index(drop=True)
    pd.testing.assert_frame_equal(baseline, restored)
    assert baseline.spikes.sum() > 0
    burdens = pd.read_csv(output / "damage_burden.csv").set_index("condition")
    assert burdens.input_sha256.nunique() == 1
    assert burdens.silenced_input_cells.eq(0).all()
    assert burdens.silenced_MBON_cells.eq(0).all()
    combined = burdens.loc["combined"]
    assert combined.silenced_cells > 0
    assert combined.total_contacts_lost == (
        combined.contacts_lost_to_silencing + combined.contacts_lost_to_thinning - combined.overlap_contacts)
    assert burdens.loc["restore_contacts", "total_contacts_lost"] == burdens.loc["cell_silencing_only", "total_contacts_lost"]
    assert burdens.loc["restore_cells", "total_contacts_lost"] == burdens.loc["contact_loss_only", "total_contacts_lost"]
    assert burdens.loc["full_restoration", "total_contacts_lost"] == 0
    # Per-neuron files preserve the exact same identity/order across conditions.
    for filename in (output / "neurons").glob("*.npz"):
        with np.load(filename) as saved:
            np.testing.assert_array_equal(saved["body_ids"], cells.body_id)
            assert saved["phase_counts"].shape == (len(assay.PHASES), n)
