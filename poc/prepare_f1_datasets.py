"""
Prepare cleaned datasets for F1 evaluation.

This script creates the files used by evaluate_f1.py:
  - evaluation/cleaned_eval_layer1.csv
  - evaluation/cleaned_eval_layer2.csv
  - evaluation/cleaned_eval_layer3.csv
  - evaluation/ambiguous_cases.csv

Run from the repository root:
  python poc/prepare_f1_datasets.py
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUT_DIR = ROOT / "evaluation"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _blank(value: object) -> bool:
    return value is None or str(value).strip() == ""


def _ambiguous_inputs(rows: list[dict[str, str]], input_col: str, degree_col: str) -> set[str]:
    seen: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        raw = row.get(input_col, "").strip()
        degree = row.get(degree_col, "").strip()
        if raw and degree:
            seen[raw].add(degree)
    return {raw for raw, degrees in seen.items() if len(degrees) > 1}


def prepare_layer1() -> tuple[int, int, list[dict[str, str]]]:
    rows = _read_csv(DATA_DIR / "layer1_exact_lookup_training.csv")
    ambiguous = _ambiguous_inputs(rows, "raw_input", "canonical_degree")
    cleaned = [row for row in rows if row["raw_input"].strip() not in ambiguous]
    ambiguous_rows = [row for row in rows if row["raw_input"].strip() in ambiguous]
    _write_csv(OUT_DIR / "cleaned_eval_layer1.csv", cleaned, list(rows[0].keys()))
    return len(rows), len(cleaned), ambiguous_rows


def prepare_layer2() -> tuple[int, int, list[dict[str, str]]]:
    rows = _read_csv(DATA_DIR / "layer2_fuzzy_training.csv")
    usable = [
        row
        for row in rows
        if row.get("noise_type", "").strip() != "hard_negative"
        and not _blank(row.get("canonical_degree"))
    ]
    ambiguous = _ambiguous_inputs(usable, "raw_input", "canonical_degree")
    cleaned = [row for row in usable if row["raw_input"].strip() not in ambiguous]
    ambiguous_rows = [row for row in usable if row["raw_input"].strip() in ambiguous]
    _write_csv(OUT_DIR / "cleaned_eval_layer2.csv", cleaned, list(rows[0].keys()))
    return len(rows), len(cleaned), ambiguous_rows


def prepare_layer3() -> tuple[int, int]:
    rows = _read_csv(DATA_DIR / "layer3_unstructured_training.csv")
    cleaned = [
        row
        for row in rows
        if not _blank(row.get("canonical_degree")) and not _blank(row.get("canonical_field"))
    ]
    _write_csv(OUT_DIR / "cleaned_eval_layer3.csv", cleaned, list(rows[0].keys()))
    return len(rows), len(cleaned)


def write_ambiguous_cases(layer1_rows: list[dict[str, str]], layer2_rows: list[dict[str, str]]) -> int:
    rows: list[dict[str, str]] = []

    for source_name, source_rows in [
        ("layer1_exact_lookup_training.csv", layer1_rows),
        ("layer2_fuzzy_training.csv", layer2_rows),
    ]:
        grouped: dict[str, set[str]] = defaultdict(set)
        examples: dict[str, dict[str, str]] = {}
        for row in source_rows:
            raw = row.get("raw_input", "").strip()
            degree = row.get("canonical_degree", "").strip()
            if not raw or not degree:
                continue
            grouped[raw].add(degree)
            examples.setdefault(raw, row)

        for raw, degrees in sorted(grouped.items()):
            example = examples[raw]
            rows.append(
                {
                    "source_file": source_name,
                    "raw_input": raw,
                    "canonical_degree_options": "|".join(sorted(degrees)),
                    "sample_id_example": example.get("sample_id", ""),
                    "note": "Exclude from F1 scoring until the business rule is decided.",
                }
            )

    _write_csv(
        OUT_DIR / "ambiguous_cases.csv",
        rows,
        ["source_file", "raw_input", "canonical_degree_options", "sample_id_example", "note"],
    )
    return len(rows)


def write_dataset_column_mapping() -> None:
    text = """# F1 Dataset Column Mapping

This note explains which columns are used for F1 scoring.

| Dataset | Input column | Expected degree | Expected field | Notes |
|---|---|---|---|---|
| `cleaned_eval_layer1.csv` | `raw_input` | `canonical_degree` | `canonical_field` | Exact alias lookup examples. Ambiguous raw inputs are excluded. |
| `cleaned_eval_layer2.csv` | `raw_input` | `canonical_degree` | `canonical_field` | Fuzzy, typo, and noisy examples. Hard negatives and ambiguous raw inputs are excluded. |
| `cleaned_eval_layer3.csv` | `raw_text` | `canonical_degree` | `canonical_field` | Unstructured sentence examples. Use carefully because Layer 3 is still a heuristic extractor. |

Rows listed in `ambiguous_cases.csv` should not be scored until the team decides the correct business rule.
"""
    (OUT_DIR / "dataset_column_mapping.md").write_text(text, encoding="utf-8")


def write_future_scope_note() -> None:
    text = """# Layer 3 Future Scope Note

Layer 3 data contains resume-like sentences and span annotations. It can be used for future extraction scoring, but it should be reported separately from Layer 1 and Layer 2.

For the first F1 pass, treat Layer 1 and Layer 2 as the main scoring targets. Layer 3 should only be scored if the team agrees that the current heuristic extractor is ready to evaluate.
"""
    (OUT_DIR / "future_scope_note.md").write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare cleaned F1 evaluation datasets.")
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR, help="Output directory.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    global OUT_DIR
    OUT_DIR = args.out_dir

    l1_total, l1_clean, l1_ambiguous_rows = prepare_layer1()
    l2_total, l2_clean, l2_ambiguous_rows = prepare_layer2()
    l3_total, l3_clean = prepare_layer3()
    ambiguous_count = write_ambiguous_cases(l1_ambiguous_rows, l2_ambiguous_rows)
    write_dataset_column_mapping()
    write_future_scope_note()

    print("F1 evaluation datasets prepared")
    print(f"Layer 1: {l1_clean:,} cleaned rows from {l1_total:,}")
    print(f"Layer 2: {l2_clean:,} cleaned rows from {l2_total:,}")
    print(f"Layer 3: {l3_clean:,} cleaned rows from {l3_total:,}")
    print(f"Ambiguous cases: {ambiguous_count:,}")
    print(f"Output directory: {OUT_DIR}")


if __name__ == "__main__":
    main()
