"""
CV Manager — Dataset Evaluation Runner  (v3.5.0)
=================================================
Evaluates the normalisation pipeline against the purpose-built training
datasets that now live in  data/  (previously datasets_updated/).

Datasets used
-------------
  L1  layer1_exact_lookup_training.csv  — gold-standard L1 regression
  L2  layer2_fuzzy_training.csv         — noisy alias samples for L2
  L3  layer3_unstructured_training.csv  — conversational text for L3

International permutation sets (evaluated against all engines):
  indian_usa_degrees_training.csv
  indian_uk_degrees_training.csv
  indian_world_degrees_training.csv

Expected CSV columns
--------------------
  layer1 / layer2 / international:
    raw_text        — input string
    canonical_name  — expected canonical degree (ground truth)
    [optional: noise_type, difficulty, scope]

  layer3:
    raw_text        — input sentence
    canonical_name  — expected canonical degree (may be empty = field-only)
    [optional: span_start, span_end, strategy_hint]

Run
---
  cd poc
  python evaluate_datasets.py

  # Evaluate only L1:
  python evaluate_datasets.py --dataset l1

  # Evaluate with a row limit (fast smoke-test):
  python evaluate_datasets.py --limit 500

Output
------
  Per-dataset precision / recall table printed to stdout.
  Optional CSV report saved to  reports/eval_<dataset>_<timestamp>.csv
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from datetime import datetime
from typing import Optional

# ── path bootstrap ─────────────────────────────────────────────────────────
_HERE     = os.path.dirname(os.path.abspath(__file__))
_ROOT     = os.path.dirname(_HERE)
_DATA_DIR = os.path.join(_ROOT, "data")
_RPT_DIR  = os.path.join(_ROOT, "reports")
sys.path.insert(0, _HERE)

# ── dataset registry ───────────────────────────────────────────────────────
DATASETS = {
    "l1": {
        "file":        "layer1_exact_lookup_training.csv",
        "label":       "L1 Exact Lookup",
        "engine_key":  "l1",
        "col_input":   "raw_input",
        "col_expect":  "canonical_degree",
    },
    "l2": {
        "file":        "layer2_fuzzy_training.csv",
        "label":       "L2 Fuzzy",
        "engine_key":  "l2",
        "col_input":   "raw_input",
        "col_expect":  "canonical_degree",
    },
    "l3": {
        "file":        "layer3_unstructured_training.csv",
        "label":       "L3 Unstructured",
        "engine_key":  "l3",
        "col_input":   "raw_text",
        "col_expect":  "canonical_degree",
    },
    "usa": {
        "file":        "indian_usa_degrees_training.csv",
        "label":       "International — India + USA",
        "engine_key":  "full",
        "col_input":   "raw_input",
        "col_expect":  "canonical_degree",
    },
    "uk": {
        "file":        "indian_uk_degrees_training.csv",
        "label":       "International — India + UK",
        "engine_key":  "full",
        "col_input":   "raw_input",
        "col_expect":  "canonical_degree",
    },
    "world": {
        "file":        "indian_world_degrees_training.csv",
        "label":       "International — India + World",
        "engine_key":  "full",
        "col_input":   "raw_input",
        "col_expect":  "canonical_degree",
    },
}

# ── display constants ──────────────────────────────────────────────────────
COL_W = {"input": 36, "expect": 30, "got": 30, "layer": 13, "conf": 6, "ok": 4}
DIVIDER = "  " + "-" * (sum(COL_W.values()) + 5 * 2 + 4)


# ===========================================================================
# Engine loader
# ===========================================================================

def _load_engine(key: str, data_dir: str):
    """Return the appropriate engine for the evaluation task."""
    from normalizer_rapidfuzz import Normalizer as RF
    from engine_orchestrator   import CVNormalizationOrchestrator as Orch

    if key == "l1":
        return RF(data_dir)          # L1 exact-match only tested via full normalize()
    elif key == "l2":
        return RF(data_dir)          # RapidFuzz standalone for L2 evaluation
    elif key == "l3":
        from engine_l3 import L3HeuristicEngine as L3
        return L3()
    else:                            # full / usa / uk / world
        return Orch(data_dir, mode="standard")


# ===========================================================================
# CSV reader
# ===========================================================================

def _read_dataset(path: str, col_input: str, col_expect: str,
                  limit: Optional[int] = None) -> list[tuple[str, str]]:
    """Read (raw_text, expected_canonical) pairs from a CSV file."""
    rows: list[tuple[str, str]] = []
    with open(path, "r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            print(f"  [WARN] Empty or headerless file: {path}")
            return rows
        # Detect column names gracefully
        fields = [f.strip().lower() for f in reader.fieldnames]
        in_col  = next((f for f in reader.fieldnames
                        if f.strip().lower() == col_input.lower()), None)
        ex_col  = next((f for f in reader.fieldnames
                        if f.strip().lower() == col_expect.lower()), None)
        if not in_col:
            in_col = reader.fieldnames[0]
        if not ex_col and len(reader.fieldnames) > 1:
            ex_col = reader.fieldnames[1]

        for i, row in enumerate(reader):
            if limit and i >= limit:
                break
            inp = (row.get(in_col) or "").strip()
            exp = (row.get(ex_col) or "").strip() if ex_col else ""
            if inp:
                rows.append((inp, exp))
    return rows


# ===========================================================================
# Evaluation core
# ===========================================================================

def _normalize(engine, raw: str, engine_key: str) -> dict:
    """Run normalisation, handling L3 standalone vs orchestrator API."""
    try:
        return engine.normalize(raw)
    except Exception as exc:
        return {
            "input": raw, "canonical_degree": None, "canonical_field": None,
            "confidence": 0.0, "status": "error", "layer_used": "error",
            "fuzzy_score": 0, "_error": str(exc),
        }


def _evaluate(dataset_key: str, data_dir: str, limit: Optional[int],
              save_csv: bool) -> dict:
    cfg   = DATASETS[dataset_key]
    fpath = os.path.join(data_dir, cfg["file"])

    print(f"\n{'=' * 74}")
    print(f"  EVALUATING: {cfg['label']}")
    print(f"  Dataset   : {cfg['file']}")
    print(f"{'=' * 74}")

    if not os.path.exists(fpath):
        print(f"  [ERROR] Dataset file not found: {fpath}")
        return {}

    # Load rows
    rows = _read_dataset(fpath, cfg["col_input"], cfg["col_expect"], limit)
    if not rows:
        print("  [WARN] No rows loaded.")
        return {}
    print(f"  Rows loaded: {len(rows):,}" + (f"  (limited to {limit})" if limit else ""))

    # Load engine
    try:
        engine = _load_engine(cfg["engine_key"], data_dir)
    except Exception as exc:
        print(f"  [ERROR] Engine load failed: {exc}")
        return {}

    # Run evaluation
    stats = {"resolved": 0, "fuzzy_matched": 0, "review_needed": 0,
             "unresolved": 0, "error": 0, "pass": 0, "fail": 0}
    report_rows: list[dict] = []

    t_start = time.perf_counter()
    for raw, expected in rows:
        r = _normalize(engine, raw, cfg["engine_key"])
        got    = (r.get("canonical_degree") or "").strip()
        status = r.get("status", "unresolved")
        layer  = r.get("layer_used", "—")
        conf   = r.get("confidence", 0.0)

        correct = (got.lower() == expected.lower()) if expected else None
        if correct is True:
            stats["pass"] += 1
        elif correct is False:
            stats["fail"] += 1
        stats[status] = stats.get(status, 0) + 1

        report_rows.append({
            "input":     raw,
            "expected":  expected,
            "got":       got,
            "layer":     layer,
            "conf":      round(conf, 4),
            "status":    status,
            "correct":   "v" if correct else ("x" if correct is False else "-"),
        })

    elapsed = (time.perf_counter() - t_start) * 1000
    total   = len(rows)
    labeled = stats["pass"] + stats["fail"]

    # ── tidy result table (first 50 rows) ─────────────────────────────
    print(f"\n  {'INPUT':<{COL_W['input']}}  {'EXPECTED':<{COL_W['expect']}}  "
          f"{'GOT':<{COL_W['got']}}  {'LAYER':<{COL_W['layer']}}  "
          f"{'CONF':<{COL_W['conf']}}  OK")
    print(DIVIDER)
    for rr in report_rows[:50]:
        inp = rr["input"][:COL_W["input"]-1]
        exp = rr["expected"][:COL_W["expect"]-1]
        got = rr["got"][:COL_W["got"]-1]
        lyr = rr["layer"][:COL_W["layer"]-1]
        cnf = f"{rr['conf']:.2f}"
        ok  = rr["correct"]
        print(f"  {inp:<{COL_W['input']}}  {exp:<{COL_W['expect']}}  "
              f"{got:<{COL_W['got']}}  {lyr:<{COL_W['layer']}}  "
              f"{cnf:<{COL_W['conf']}}  {ok}")
    if total > 50:
        print(f"  … {total - 50:,} more rows not shown …")

    # ── summary metrics ────────────────────────────────────────────────
    print(f"\n{DIVIDER}")
    print(f"  {'METRIC':<22}  VALUE")
    print(f"  {'-'*22}  {'-'*20}")
    print(f"  {'Total rows':<22}  {total:,}")
    print(f"  {'Total time':<22}  {elapsed:.0f} ms  ({elapsed/total:.2f} ms/row)")
    if labeled:
        prec = stats["pass"] / labeled * 100
        print(f"  {'Labeled rows':<22}  {labeled:,}")
        print(f"  {'Pass (exact match)':<22}  {stats['pass']:,}  ({prec:.1f}%)")
        print(f"  {'Fail':<22}  {stats['fail']:,}  ({100-prec:.1f}%)")
    print(f"  {'-'*22}  {'-'*20}")
    for s in ("resolved", "fuzzy_matched", "review_needed", "unresolved", "error"):
        v = stats.get(s, 0)
        if v:
            print(f"  {s:<22}  {v:,}  ({v/total*100:.1f}%)")
    print(f"{DIVIDER}\n")

    # ── optional CSV report ────────────────────────────────────────────
    if save_csv:
        os.makedirs(_RPT_DIR, exist_ok=True)
        ts      = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_csv = os.path.join(_RPT_DIR, f"eval_{dataset_key}_{ts}.csv")
        with open(out_csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(report_rows[0].keys()))
            w.writeheader()
            w.writerows(report_rows)
        print(f"  Report saved → {out_csv}\n")

    return {
        "dataset":  dataset_key,
        "total":    total,
        "pass":     stats.get("pass", 0),
        "fail":     stats.get("fail", 0),
        "labeled":  labeled,
        "elapsed_ms": elapsed,
    }


# ===========================================================================
# CLI
# ===========================================================================

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="CV Manager — Dataset Evaluation Runner (v3.5.0)"
    )
    p.add_argument(
        "--dataset", "-d",
        choices=list(DATASETS.keys()) + ["all"],
        default="all",
        help="Dataset to evaluate (default: all)",
    )
    p.add_argument(
        "--limit", "-n",
        type=int, default=None,
        help="Max rows per dataset (default: all rows)",
    )
    p.add_argument(
        "--save", "-s",
        action="store_true",
        help="Save per-dataset CSV reports to reports/",
    )
    return p.parse_args()


def main() -> None:
    args = _parse_args()

    print("\n" + "+" + "=" * 72 + "+")
    print("|" + "  CV MANAGER * Dataset Evaluation Runner  (v3.5.0)".center(72) + "|")
    print("|" + f"  Data dir: {_DATA_DIR}".ljust(72) + "|")
    print("+" + "=" * 72 + "+")

    keys = list(DATASETS.keys()) if args.dataset == "all" else [args.dataset]
    summaries: list[dict] = []

    for k in keys:
        result = _evaluate(k, _DATA_DIR, args.limit, args.save)
        if result:
            summaries.append(result)

    # ── overall summary ────────────────────────────────────────────────
    if len(summaries) > 1:
        print("\n" + "=" * 74)
        print("  OVERALL SUMMARY")
        print("=" * 74)
        print(f"  {'DATASET':<30}  {'ROWS':>8}  {'PASS':>7}  {'FAIL':>7}  {'PREC%':>7}")
        print("  " + "-" * 62)
        for s in summaries:
            prec = f"{s['pass']/s['labeled']*100:.1f}%" if s.get("labeled") else "-"
            print(f"  {DATASETS[s['dataset']]['label']:<30}  "
                  f"{s['total']:>8,}  {s['pass']:>7,}  {s['fail']:>7,}  {prec:>7}")
        print("  " + "-" * 62 + "\n")


if __name__ == "__main__":
    main()
