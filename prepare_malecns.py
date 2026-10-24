"""Download and adapt the official MaleCNS v1.0 graph for Brian2.

Measured contact counts are retained separately from assumed synaptic signs.
No small-edge threshold, cell-type aggregation, or brain-region subset is used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.ipc as ipc
import pyarrow.parquet as pq

BASE = "https://storage.googleapis.com/flyem-male-cns/v1.0/connectome-data/flat-connectome/"
FILES = {
    "annotations": "body-annotations-male-cns-v1.0-minconf-0.5.feather",
    "neurotransmitters": "body-neurotransmitters-male-cns-v1.0.feather",
    "connections": "connectome-weights-male-cns-v1.0-minconf-0.5.feather",
}
SIGNS = {"acetylcholine": 1, "gaba": -1, "glutamate": -1}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def neuron_table(annotations: pd.DataFrame, transmitters: pd.DataFrame) -> pd.DataFrame:
    # Keep all annotated neuronal superclasses, including uncertain '*_tbc' classes.
    keep = annotations.superclass.notna() & ~annotations.superclass.str.contains(
        "glia", case=False, na=False
    )
    cells = annotations.loc[keep, ["bodyId", "type", "superclass", "somaSide"]].copy()
    cells = cells.rename(columns={"bodyId": "body_id", "type": "cell_type"})
    cells = cells.sort_values("body_id").reset_index(drop=True)
    if cells.empty or cells.body_id.duplicated().any():
        raise ValueError("Neuron IDs must be nonempty and unique")
    nt = transmitters.set_index("body").consensus_nt
    if not nt.index.is_unique:
        raise ValueError("Duplicate neurotransmitter body IDs")
    cells["consensus_nt"] = cells.body_id.map(nt)
    # These are model assumptions, not receptor-specific measured effects.
    cells["sign"] = cells.consensus_nt.str.lower().map(SIGNS).fillna(0).astype("int8")
    cells.index.name = "neuron_index"
    return cells


def map_connections(frame: pd.DataFrame, cells: pd.DataFrame) -> pd.DataFrame:
    index = pd.Index(cells.body_id)
    pre = index.get_indexer(frame.body_pre)
    post = index.get_indexer(frame.body_post)
    keep = (pre >= 0) & (post >= 0)
    pre, post = pre[keep], post[keep]
    contacts = frame.loc[keep, "weight"].to_numpy(dtype=np.int64)
    if np.any(contacts <= 0) or not np.array_equal(contacts, frame.loc[keep, "weight"]):
        raise ValueError("Expected positive integer contact counts")
    return pd.DataFrame({
        "Presynaptic_Index": pre.astype(np.int32),
        "Postsynaptic_Index": post.astype(np.int32),
        "contacts": contacts,
        "Excitatory x Connectivity": contacts * cells.sign.to_numpy()[pre],
    })


def prepare(directory: Path) -> dict:
    raw = directory / "raw"
    paths = {key: raw / name for key, name in FILES.items()}
    cells = neuron_table(pd.read_feather(paths["annotations"]),
                         pd.read_feather(paths["neurotransmitters"]))
    cells.to_csv(directory / "neurons.csv")
    output = directory / "connections.parquet"
    temporary = output.with_suffix(".part")
    rows = contacts = zero_edges = excluded = 0
    writer = None
    try:
        with pa.memory_map(str(paths["connections"]), "r") as source:
            reader = ipc.open_file(source)
            for batch_number in range(reader.num_record_batches):
                frame = reader.get_batch(batch_number).to_pandas()
                edges = map_connections(frame, cells)
                excluded += len(frame) - len(edges)
                rows += len(edges)
                contacts += int(edges.contacts.sum())
                zero_edges += int((edges["Excitatory x Connectivity"] == 0).sum())
                table = pa.Table.from_pandas(edges, preserve_index=False)
                if writer is None:
                    writer = pq.ParquetWriter(temporary, table.schema)
                writer.write_table(table)
        if rows == 0:
            raise ValueError("No retained connections")
    finally:
        if writer is not None:
            writer.close()
    temporary.replace(output)
    manifest = {
        "dataset": "male-cns:v1.0", "release_date": "2026-06-08",
        "announcement_date": "2026-09-03",
        "source": "https://male-cns.janelia.org/download/",
        "attribution": "FlyEM/HHMI Janelia, University of Cambridge, MRC LMB, Google Research",
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "neuron_count": len(cells), "directed_connections": rows,
        "synaptic_contacts": contacts, "excluded_segment_connections": excluded,
        "zero_sign_neurons": int((cells.sign == 0).sum()),
        "zero_weight_connections": zero_edges,
        "selection": "All non-null neuronal superclasses; includes uncertain classes. Excludes glia and unclassified segments. Both endpoints must be retained. No edge threshold; self-connections retained.",
        "sign_assumptions": {**SIGNS, "other_or_unknown": 0},
        "limitations": "Predicted transmitter signs are simplified. Modulatory/unknown outputs have zero dynamic weight but their contacts remain recorded. No receptor-specific effects, electrical synapses, disease mechanisms, or biological validation of transferred dynamics.",
        "raw_files": {key: {"url": BASE + path.name, "bytes": path.stat().st_size,
                             "sha256": sha256(path)} for key, path in paths.items()},
        "prepared_files": {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)}
                           for p in [directory / "neurons.csv", output]},
    }
    (directory / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=Path("data/malecns"))
    parser.add_argument("--download", action="store_true", help="Fetch missing official files (~1.1 GB)")
    args = parser.parse_args()
    raw = args.data_dir / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    if args.download:
        for name in FILES.values():
            destination = raw / name
            if destination.exists():
                continue
            temporary = destination.with_suffix(".part")
            print(f"Downloading {name}", flush=True)
            with urllib.request.urlopen(BASE + name, timeout=120) as response, temporary.open("wb") as stream:
                shutil.copyfileobj(response, stream, length=4 * 1024 * 1024)
                expected = response.headers.get("Content-Length")
            if expected is not None and temporary.stat().st_size != int(expected):
                raise ValueError(f"Incomplete download: {name}")
            temporary.replace(destination)
    manifest = prepare(args.data_dir)
    print(json.dumps({k: manifest[k] for k in ["dataset", "neuron_count", "directed_connections", "synaptic_contacts", "zero_sign_neurons"]}, indent=2))


if __name__ == "__main__":
    main()
