"""Checks for direction, identity preservation, and independent trial execution."""
import json

import numpy as np
import pandas as pd
import pytest

from prepare_malecns import neuron_table, map_connections, sha256


def test_ids_signs_and_missing_endpoints():
    large_id = 2**53 + 7
    cells = neuron_table(pd.DataFrame({
        "bodyId": [large_id, 5, 99, 11], "type": ["in", "out", "glia", "unknown"],
        "superclass": ["cb_sensory", "cb_motor", "glia", "cb_intrinsic"],
        "somaSide": ["L"] * 4,
    }), pd.DataFrame({"body": [large_id, 5, 11],
                     "consensus_nt": ["acetylcholine", "gaba", "dopamine"]}))
    edges = map_connections(pd.DataFrame({
        "body_pre": [large_id, 5, 11, 99, large_id],
        "body_post": [5, large_id, 5, 5, 999], "weight": [3, 2, 7, 9, 8],
    }), cells)
    assert cells.body_id.tolist() == [5, 11, large_id]
    assert edges.Presynaptic_Index.tolist() == [2, 0, 1]
    assert edges.Postsynaptic_Index.tolist() == [0, 2, 0]
    assert edges["Excitatory x Connectivity"].tolist() == [3, -2, 0]
    assert edges.contacts.tolist() == [3, 2, 7]


def test_actual_trials_are_reproducible_and_paired(tmp_path):
    pytest.importorskip("brian2")
    from run_malecns import run_trials
    data = tmp_path / "data"
    data.mkdir()
    pd.DataFrame({"body_id": [10, 20], "cell_type": ["LC4", "DNp01"]}).rename_axis(
        "neuron_index").to_csv(data / "neurons.csv")
    pd.DataFrame({"Presynaptic_Index": [0], "Postsynaptic_Index": [1],
                  "Excitatory x Connectivity": [100]}).to_parquet(data / "connections.parquet")
    (data / "manifest.json").write_text(json.dumps({"prepared_files": {
        name: {"sha256": sha256(data / name)} for name in ["neurons.csv", "connections.parquet"]}}))
    a = run_trials(data, tmp_path / "a", .1, 2, 123, "LC4", "DNp01", 150)
    b = run_trials(data, tmp_path / "b", .1, 2, 123, "LC4", "DNp01", 150)
    counts = []
    for row in a["trials"]:
        filename = f'{row["condition"]}_trial_{row["trial"]:03d}.parquet'
        pd.testing.assert_frame_equal(pd.read_parquet(tmp_path / "a" / filename),
                                      pd.read_parquet(tmp_path / "b" / filename))
        if row["condition"] == "no_stimulus":
            assert row["total_spikes"] == 0
        if row["condition"] == "baseline":
            counts.append(row["stimulus_spikes"])
            paired = next(x for x in a["trials"] if x["condition"] == "weights_75_percent"
                          and x["trial"] == row["trial"])
            assert row["stimulus_spikes"] == paired["stimulus_spikes"]
    assert counts[0] != counts[1]  # Fixed seeds on the feedforward test graph.
    assert len(a["trials"]) == len(b["trials"]) == 6
    with pytest.raises(FileExistsError):
        run_trials(data, tmp_path / "a", .1, 2, 123, "LC4", "DNp01", 150)
