"""
Run F1 scoring for CV Manager normalization datasets.

Run from the repository root:
  python poc/prepare_f1_datasets.py
  python poc/evaluate_f1.py --dataset all --max-rows 500

For full scoring, omit --max-rows.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
POC_DIR = ROOT / "poc"
DATA_DIR = ROOT / "data"
EVAL_DIR = ROOT / "evaluation"

sys.path.insert(0, str(POC_DIR))

NONE_LABEL = "__NONE__"


DATASETS = {
    "layer1": {
        "file": "cleaned_eval_layer1.csv",
        "input_col": "raw_input",
        "degree_col": "canonical_degree",
        "field_col": "canonical_field",
        "engine": "rapidfuzz",
        "failure_file": "layer1_failures.csv",
    },
    "layer2": {
        "file": "cleaned_eval_layer2.csv",
        "input_col": "raw_input",
        "degree_col": "canonical_degree",
        "field_col": "canonical_field",
        "engine": "rapidfuzz",
        "failure_file": "layer2_failures.csv",
    },
    "layer3": {
        "file": "cleaned_eval_layer3.csv",
        "input_col": "raw_text",
        "degree_col": "canonical_degree",
        "field_col": "canonical_field",
        "engine": "rapidfuzz",
        "failure_file": "layer3_failures.csv",
    },
    "indian_usa": {
        "file": "cleaned_eval_indian_usa.csv",
        "input_col": "raw_input",
        "degree_col": "canonical_degree",
        "field_col": None,
        "engine": "rapidfuzz",
        "failure_file": "indian_usa_failures.csv",
    },
    "indian_uk": {
        "file": "cleaned_eval_indian_uk.csv",
        "input_col": "raw_input",
        "degree_col": "canonical_degree",
        "field_col": None,
        "engine": "rapidfuzz",
        "failure_file": "indian_uk_failures.csv",
    },
    "indian_world": {
        "file": "cleaned_eval_indian_world.csv",
        "input_col": "raw_input",
        "degree_col": "canonical_degree",
        "field_col": None,
        "engine": "rapidfuzz",
        "failure_file": "indian_world_failures.csv",
    },
}


def is_missing(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    text = str(value).strip()
    return text == "" or text.lower() == "nan"


def label(value: object) -> str:
    if is_missing(value):
        return NONE_LABEL
    return str(value).strip()


def pair_label(degree: object, field: object) -> str:
    degree_part = "" if is_missing(degree) else str(degree).strip()
    field_part = "" if is_missing(field) else str(field).strip()
    return f"{degree_part}||{field_part}"


def precision_recall_f1(y_true: Iterable[str], y_pred: Iterable[str], ignore_none: bool = True) -> dict[str, float]:
    true_values = list(y_true)
    pred_values = list(y_pred)
    labels = sorted(set(true_values) | set(pred_values))
    if ignore_none:
        labels = [item for item in labels if item != NONE_LABEL]

    tp = fp = fn = 0
    per_label_f1: list[float] = []

    for item in labels:
        item_tp = sum(1 for t, p in zip(true_values, pred_values) if t == item and p == item)
        item_fp = sum(1 for t, p in zip(true_values, pred_values) if t != item and p == item)
        item_fn = sum(1 for t, p in zip(true_values, pred_values) if t == item and p != item)
        tp += item_tp
        fp += item_fp
        fn += item_fn

        precision = item_tp / (item_tp + item_fp) if item_tp + item_fp else 0.0
        recall = item_tp / (item_tp + item_fn) if item_tp + item_fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_label_f1.append(f1)

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    macro_f1 = sum(per_label_f1) / len(per_label_f1) if per_label_f1 else 0.0

    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "macro_f1": macro_f1,
        "label_count": len(labels),
    }


def exact_f1(y_true: Iterable[str], y_pred: Iterable[str]) -> dict[str, float]:
    true_values = list(y_true)
    pred_values = list(y_pred)
    total = len(true_values)
    correct = sum(1 for t, p in zip(true_values, pred_values) if t == p)
    score = correct / total if total else 0.0
    return {"precision": score, "recall": score, "f1": score, "macro_f1": score}


def load_rows(path: Path, max_rows: int | None) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if max_rows is not None:
        return rows[:max_rows]
    return rows


def load_engine(name: str):
    if name != "rapidfuzz":
        raise ValueError(f"Unsupported engine: {name}")
    from normalizer_rapidfuzz import Normalizer

    return Normalizer(str(DATA_DIR))


def classify_failure(expected_degree: str, predicted_degree: str, expected_field: str, predicted_field: str, result: dict) -> str:
    status = result.get("status", "")
    layer_used = result.get("layer_used", "")

    if status == "unresolved" or layer_used == "unresolved":
        return "unresolved_below_confidence_threshold"
    if expected_degree != predicted_degree and expected_field != predicted_field:
        return "wrong_degree_and_field"
    if expected_degree != predicted_degree:
        return "wrong_degree"
    if expected_field != predicted_field:
        return "wrong_field"
    return "other"


def write_failure_file(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "raw_input",
        "expected_degree",
        "predicted_degree",
        "expected_field",
        "predicted_field",
        "status",
        "layer_used",
        "confidence",
        "fuzzy_score",
        "error_category",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def evaluate_dataset(key: str, eval_dir: Path, max_rows: int | None) -> dict[str, object]:
    cfg = DATASETS[key]
    rows = load_rows(eval_dir / cfg["file"], max_rows)
    engine = load_engine(cfg["engine"])
    has_field_col = cfg["field_col"] is not None

    true_degree: list[str] = []
    pred_degree: list[str] = []
    true_field: list[str] = []
    pred_field: list[str] = []
    true_pair: list[str] = []
    pred_pair: list[str] = []
    failure_rows: list[dict[str, object]] = []
    status_counts: Counter[str] = Counter()

    start = time.perf_counter()
    for row in rows:
        raw_input = row[cfg["input_col"]]
        expected_degree = label(row.get(cfg["degree_col"]))
        expected_field = label(row.get(cfg["field_col"])) if cfg["field_col"] else NONE_LABEL

        result = engine.normalize(raw_input)
        predicted_degree = label(result.get("canonical_degree"))
        predicted_field = label(result.get("canonical_field")) if has_field_col else NONE_LABEL

        true_degree.append(expected_degree)
        pred_degree.append(predicted_degree)
        true_field.append(expected_field)
        pred_field.append(predicted_field)
        true_pair.append(pair_label(expected_degree, expected_field))
        pred_pair.append(pair_label(predicted_degree, predicted_field))
        status_counts[str(result.get("status", "unknown"))] += 1

        if true_pair[-1] != pred_pair[-1]:
            failure_rows.append(
                {
                    "raw_input": raw_input,
                    "expected_degree": "" if expected_degree == NONE_LABEL else expected_degree,
                    "predicted_degree": "" if predicted_degree == NONE_LABEL else predicted_degree,
                    "expected_field": "" if expected_field == NONE_LABEL else expected_field,
                    "predicted_field": "" if predicted_field == NONE_LABEL else predicted_field,
                    "status": result.get("status", ""),
                    "layer_used": result.get("layer_used", ""),
                    "confidence": result.get("confidence", 0),
                    "fuzzy_score": result.get("fuzzy_score", 0),
                    "error_category": classify_failure(
                        expected_degree,
                        predicted_degree,
                        expected_field,
                        predicted_field,
                        result,
                    ),
                }
            )

    elapsed_ms = (time.perf_counter() - start) * 1000

    degree = precision_recall_f1(true_degree, pred_degree)
    field = precision_recall_f1(true_field, pred_field)
    pair = exact_f1(true_pair, pred_pair)
    combined = precision_recall_f1(true_degree + true_field, pred_degree + pred_field)
    field_has_labels = has_field_col and field["label_count"] > 0

    write_failure_file(eval_dir / cfg["failure_file"], failure_rows)

    return {
        "dataset": key,
        "rows": len(rows),
        "sampled": max_rows is not None,
        "max_rows": max_rows or "",
        "failures": len(failure_rows),
        "degree_precision": round(degree["precision"], 4),
        "degree_recall": round(degree["recall"], 4),
        "degree_f1": round(degree["f1"], 4),
        "field_precision": round(field["precision"], 4) if field_has_labels else "N/A",
        "field_recall": round(field["recall"], 4) if field_has_labels else "N/A",
        "field_f1": round(field["f1"], 4) if field_has_labels else "N/A",
        "pair_precision": round(pair["precision"], 4),
        "pair_recall": round(pair["recall"], 4),
        "pair_f1": round(pair["f1"], 4),
        "micro_f1": round(combined["f1"], 4),
        "macro_f1": round((degree["macro_f1"] + field["macro_f1"]) / 2, 4)
        if field_has_labels
        else round(degree["macro_f1"], 4),
        "elapsed_ms": round(elapsed_ms, 1),
        "status_counts": dict(status_counts),
    }


def write_summary(path: Path, rows: list[dict[str, object]]) -> None:
    fieldnames = [
        "dataset",
        "rows",
        "sampled",
        "max_rows",
        "failures",
        "degree_precision",
        "degree_recall",
        "degree_f1",
        "field_precision",
        "field_recall",
        "field_f1",
        "pair_precision",
        "pair_recall",
        "pair_f1",
        "micro_f1",
        "macro_f1",
        "elapsed_ms",
        "status_counts",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_metrics_explanation(eval_dir: Path) -> None:
    text = """# F1 Metrics Explanation

This evaluation reports several scores instead of only one overall number.

| Metric | Meaning |
|---|---|
| Degree F1 | Checks whether the predicted canonical degree is correct. |
| Field F1 | Checks whether the predicted field or specialization is correct. |
| Pair F1 | Checks degree and field together. Both must match. |
| Micro F1 | Overall score across degree and field labels together. |
| Macro F1 | Average of degree macro F1 and field macro F1, so rare labels still matter. |

Missing field values are treated as blank values. They are not treated as the text `nan`.

Rows in `ambiguous_cases.csv` are excluded from the cleaned evaluation files until the team decides the correct business rule.

International datasets are degree-only. Their field metrics are reported as `N/A`.

Layer 3 is included in the complete evaluation summary, but it should be interpreted separately because it scores unstructured sentence extraction rather than direct alias lookup.
"""
    (eval_dir / "metrics_explanation.md").write_text(text, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run F1 evaluation for CV Manager datasets.")
    parser.add_argument("--dataset", choices=[*DATASETS.keys(), "all"], default="all")
    parser.add_argument("--eval-dir", type=Path, default=EVAL_DIR)
    parser.add_argument("--max-rows", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.dataset == "all":
        keys = list(DATASETS)
    else:
        keys = [args.dataset]
    results = [evaluate_dataset(key, args.eval_dir, args.max_rows) for key in keys]
    write_summary(args.eval_dir / "evaluation_summary.csv", results)
    write_metrics_explanation(args.eval_dir)

    print("F1 evaluation complete")
    for result in results:
        print(
            f"{result['dataset']}: rows={result['rows']}, "
            f"degree_f1={result['degree_f1']}, "
            f"field_f1={result['field_f1']}, "
            f"pair_f1={result['pair_f1']}"
        )
    print(f"Summary: {args.eval_dir / 'evaluation_summary.csv'}")


if __name__ == "__main__":
    main()
