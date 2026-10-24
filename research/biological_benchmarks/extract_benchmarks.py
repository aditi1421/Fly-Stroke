"""Read published XLSX XML without modifying the original workbook."""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from statistics import mean, stdev
from xml.etree import ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parent
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def read_workbook(path: Path) -> dict:
    with ZipFile(path) as archive:
        strings = ["".join(x.itertext()) for x in ET.fromstring(archive.read("xl/sharedStrings.xml"))]
        relationships = {x.attrib["Id"]: x.attrib["Target"] for x in ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))}
        sheets = {}
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        for sheet in workbook.find("m:sheets", NS):
            key = sheet.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
            root = ET.fromstring(archive.read("xl/" + relationships[key]))
            cells = {}
            for c in root.findall(".//m:sheetData/m:row/m:c", NS):
                value = c.find("m:v", NS)
                if value is None:
                    continue
                value = strings[int(value.text)] if c.attrib.get("t") == "s" else float(value.text)
                formula = c.find("m:f", NS)
                cells[c.attrib["r"]] = {"value": value, "formula": formula.text if formula is not None else None}
            sheets[sheet.attrib["name"]] = cells
        return sheets


def extract_group(workbook, sheet, panel, mean_cell, sem_cell, label_cell, assay, hours, role, intervention="none", data_range=None):
    cells = workbook[sheet]
    formula = cells[mean_cell]["formula"]
    match = re.fullmatch(r"AVERAGE\(([A-Z]+)(\d+):([A-Z]+)(\d+)\)", formula or f"AVERAGE({data_range})")
    if match is None or match[1] != match[3]:
        raise ValueError(f"Unsupported source range {formula}")
    column, start, stop = match[1], int(match[2]), int(match[4])
    addresses = [f"{column}{row}" for row in range(start, stop + 1)]
    observations = [{"cell": addr, "value": cells[addr]["value"]} for addr in addresses]
    values = [x["value"] for x in observations]
    if not all(isinstance(x, (int, float)) for x in values):
        raise ValueError("Nonnumeric observation")
    average = mean(values)
    sem = stdev(values) / math.sqrt(len(values))
    assert abs(average - cells[mean_cell]["value"]) < 1e-10
    assert abs(sem - cells[sem_cell]["value"]) < 1e-10
    return {
        "paper": "Kaldun et al. 2021", "figure": panel, "source_sheet": sheet,
        "source_range": f"{addresses[0]}:{addresses[-1]}",
        "source_mean_cell": mean_cell, "source_sem_cell": sem_cell,
        "source_genotype_cell": label_cell, "genotype_verbatim": cells[label_cell]["value"],
        "age_days": [7, 9], "sex": "mixed", "assay": assay,
        "retention_hours_label": hours,
        "immediate_test_note": "0 h denotes about 3 min after training in aversive protocol; not instantaneous",
        "intervention": intervention, "proposed_use": role,
        "unit": "behavioral performance index points (scale -100 to 100)",
        "experimental_unit": "experiment combining two reciprocal conditioning groups; 50–100 flies per group",
        "n_experiments": len(values), "mean": average, "sem": sem,
        "uncertainty": "SEM recomputed from experiment-level observations; not a 95% interval or individual-fly uncertainty",
        "observations": observations,
    }


def main():
    path = ROOT / "kaldun2021_s1.xlsx"
    workbook = read_workbook(path)
    groups = []
    specifications = [
        ("1C", "Q", "R", "S", "O", [3,17,31], "aversive", 0, "calibration candidate"),
        ("1D", "X", "Y", "Z", "V", [3,17,31], "aversive", 2, "calibration candidate"),
        ("1K", "X", "Y", "Z", "V", [56,70,84], "appetitive", 0, "calibration candidate"),
        ("1L", "AE", "AF", "AG", "AC", [56,70,84], "appetitive", 2, "calibration candidate"),
        ("1M", "AL", "AM", "AN", "AJ", [56,70,84], "appetitive", 6, "held-out prediction candidate"),
        ("1N", "J", "K", "L", "H", [110,124,138], "appetitive", 24, "held-out prediction candidate; distinct feeding protocol"),
    ]
    for panel, data_col, avg_col, sem_col, label_col, starts, assay, hours, role in specifications:
        for row in starts:
            groups.append(extract_group(workbook, "Figure 1", panel, f"{avg_col}{row}", f"{sem_col}{row}", f"{label_col}{row}", assay, hours, role, data_range=f"{data_col}{row}:{data_col}{row + 11}"))
    for hours, starts in ((4, [59,73,87]), (6, [111,125,139])):
        for row in starts:
            groups.append(extract_group(workbook, "S1", "S1H", f"R{row}", f"S{row}", f"O{row}", "aversive", hours, "held-out prediction candidate", data_range=f"Q{row}:Q{row + 11}"))
    for panel, avg_col, sem_col, label_col, starts in (
        ("3A", "D", "E", "A", [3,15,25]),
        ("3B", "K", "L", "H", [3,13,23]),
        ("3C", "R", "S", "O", [3,13,23]),
    ):
        for position, row in enumerate(starts):
            intervention = "2 h at 30 C immediately after training, then 4 h at 21–22 C" if position == 2 else "21–22 C"
            groups.append(extract_group(workbook, "Figure 3", panel, f"{avg_col}{row}", f"{sem_col}{row}", f"{label_col}{row}", "appetitive", 0 if position == 0 else 6, "held-out intervention candidate; different driver from Figure 1", intervention))
    metadata = {
        "source_url": "https://journals.plos.org/plosbiology/article/file?id=10.1371/journal.pbio.3001412.s008&type=supplementary",
        "source_doi": "10.1371/journal.pbio.3001412.s008", "retrieved_date": "2026-10-24",
        "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "license": "CC BY 4.0; Kaldun et al. 2021 PLOS Biology",
        "extraction": "Original numeric XLSX cells, not figure digitization; original workbook preserved unchanged",
        "checks": "All group means and sample-SD/sqrt(n) SEMs independently recomputed and matched stored source summaries within 1e-10; some source summaries contain formulas and others literal values",
        "split_status": "Proposed calibration/holdout roles, not a preregistration. No model fitting performed by this extractor.",
        "cautions": [
            "Nonsignificant acquisition contrasts do not demonstrate statistical equivalence.",
            "Do not pool parental controls, assays, ages, genetic drivers or temperature protocols.",
            "S1H 0 h/2 h reuse Figure 1C/1D; these were not duplicated in extraction.",
            "A neurally defined simulated memory score is not this behavioral performance index.",
            "Rows do not establish longitudinally paired experiments or independent biological batches.",
        ],
        "groups": groups,
    }
    (ROOT / "kaldun2021_measurements.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n")
    print(f"Extracted {len(groups)} groups, {sum(g['n_experiments'] for g in groups)} observations; all source mean/SEM checks passed.")
    for group in groups:
        print(group["figure"], group["genotype_verbatim"], group["retention_hours_label"], group["intervention"], f"{group['mean']:.3f} +/- {group['sem']:.3f}", group["n_experiments"])


if __name__ == "__main__":
    main()
