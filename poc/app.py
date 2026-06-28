"""
CV Manager — Unified POC Application
=====================================
Single entry-point CLI that provides access to every engine in the
qualification-normalisation pipeline without requiring any server.

Engine roster
  [A]  Layer 1 only          — dictionary exact-match, zero latency
  [B1] RapidFuzz             — L1 + Levenshtein fuzzy (standalone)
  [B2] TF-IDF                — L1 + character n-gram cosine (standalone)
  [B3] Embeddings            — L1 + semantic vectors (needs torch)
  [C]  L2 Combined           — consensus vote across B1+B2+B3
  [D]  Full Orchestrator     — L1 + L2 Combined + L3 heuristic (max recall)

Menu structure
  Main menu → choose engine → sub-menu:
    1. Run standard test suite
    2. Normalise a custom input
    3. Batch process from file
    4. Compare all engines on one input
    5. Back to main menu

Run:  python app.py
"""

from __future__ import annotations

import csv
import os
import sys
import time
from typing import Optional

# ── path bootstrap ─────────────────────────────────────────────────────────
_HERE     = os.path.dirname(os.path.abspath(__file__))
_ROOT     = os.path.dirname(_HERE)
_DATA_DIR = os.path.join(_ROOT, "data")
sys.path.insert(0, _HERE)
sys.path.insert(0, _ROOT)

# ── version ────────────────────────────────────────────────────────────────
APP_VERSION = "3.6.5"

# ── shared test suite ─────────────────────────────────────────────────────
STANDARD_TESTS: list[str] = [
    # Clean abbreviations
    "B.Tech",
    "BTech",
    "MBA",
    "BBA",
    "BSc",
    "12th",
    # Typo-laced
    "Bacheler of Technology",
    "Bachellor of Technolgy",
    "Bachelar of Sci",
    # With field separators
    "B. Tech in CSE",
    "M.Tech (Computer Science)",
    "B.Tech - Mechanical Engineering",
    "BE, Electronics",
    # Long canonical names
    "Bachelor of Technology",
    "Bachelor of Business Administration",
    # Abbreviated long name (the "BBA bug" case)
    "Bachelor of Business Admin",
    # Hons / variant markers
    "BE Hons",
    "B.Pharma",
    # Unrecognised
    "Kuchh bhi degree",
    # Conversational (L3 territory)
    "I completed my Masters in Data Science from IIT Delhi",
    "She holds a diploma in Electrical Engineering",
]


# ══════════════════════════════════════════════════════════════════════════
# Display helpers
# ══════════════════════════════════════════════════════════════════════════

def _banner() -> None:
    width = 68
    print()
    print("╔" + "═" * width + "╗")
    print("║" + " CV MANAGER  —  Qualification Normalisation PoC ".center(width) + "║")
    print("║" + f" Version {APP_VERSION}  ·  Growth Grids × University of Southampton ".center(width) + "║")
    print("║" + " Contributor: Arnav Mishra ".center(width) + "║")
    print("╚" + "═" * width + "╝")


def _section(title: str) -> None:
    width = len(title) + 6
    print(f"\n  ┌{'─' * width}┐")
    print(f"  │   {title}   │")
    print(f"  └{'─' * width}┘")


def _print_result_table(results: list[dict], label: str = "") -> None:
    total = len(results)
    W = {"inp": 36, "canon": 32, "layer": 14, "conf": 6}
    div = "  " + "─" * (W["inp"] + W["canon"] + W["layer"] + W["conf"] + 4 * 2 + 6)
    if label:
        print(f"\n  {label}  ({total} inputs)")
    print()
    print(f"  {'INPUT':<{W['inp']}}  {'CANONICAL':<{W['canon']}}  "
          f"{'LAYER':<{W['layer']}}  {'CONF':<{W['conf']}}  STATUS")
    print(div)
    stats: dict[str, int] = {}
    for r in results:
        inp    = (str(r.get("input") or ""))[:W["inp"] - 1]
        canon  = (str(r.get("canonical_degree") or "—"))[:W["canon"] - 1]
        layer  = str(r.get("layer_used") or "—")[:W["layer"] - 1]
        conf   = f"{r.get('confidence', 0):.2f}"
        status = str(r.get("status") or "—")
        print(f"  {inp:<{W['inp']}}  {canon:<{W['canon']}}  "
              f"{layer:<{W['layer']}}  {conf:<{W['conf']}}  {status}")
        if r.get("canonical_field"):
            print(f"  {'':>{W['inp']}}  ↳ field: {r['canonical_field']}")
        stats[status] = stats.get(status, 0) + 1
    print(div)
    print(f"\n  {'STATUS':<18}  {'N':>4}  {'%':>5}")
    print(f"  {'─'*18}  {'─'*4}  {'─'*5}")
    for s, c in sorted(stats.items()):
        print(f"  {s:<18}  {c:>4}  {c / total * 100:>4.0f}%")


def _print_single_result(r: dict) -> None:
    W = 24
    width = 66
    div = "  " + "─" * width
    print(f"\n{div}")
    print("  NORMALISATION RESULT")
    print(div)
    print(f"  {'Input':<{W}}: {r.get('input','')}")
    canon = r.get("canonical_degree") or "—"
    field = r.get("canonical_field") or "—"
    print(f"  {'Canonical Degree':<{W}}: {canon}")
    print(f"  {'Canonical Field':<{W}}: {field}")
    print(f"  {'Layer Used':<{W}}: {r.get('layer_used','—')}")
    conf  = r.get("confidence", 0)
    score = r.get("fuzzy_score", 0)
    bar_fill = int(conf * 20)
    bar = "█" * bar_fill + "░" * (20 - bar_fill)
    print(f"  {'Confidence':<{W}}: {conf:.4f}  [{bar}]")
    print(f"  {'Fuzzy Score':<{W}}: {score}")
    print(f"  {'Status':<{W}}: {r.get('status','—')}")
    if r.get("alternatives"):
        print(f"\n  {'Alternatives':<{W}}:")
        for alt, sc in r["alternatives"]:
            print(f"  {'':{W}}  • {alt:<40}  score: {sc:.1f}")
    if r.get("audit"):
        print(f"\n  Audit Trail:")
        for lyr, info in r["audit"].items():
            if isinstance(info, dict):
                print(f"    [{lyr}]  hit={info.get('hit', '—')}  "
                      f"latency={info.get('latency_ms', info.get('ms', '—'))}ms")
                if "engines" in info:
                    for ed in info["engines"]:
                        print(f"      ↳ {ed.get('engine','?'):<12}  "
                              f"{(ed.get('result') or '—'):<28}  "
                              f"conf={ed.get('conf',0):.3f}  {ed.get('ms',0):.1f}ms")
    if r.get("l3_strategy"):
        print(f"\n  {'L3 Strategy':<{W}}: {r['l3_strategy']}")
        print(f"  {'Extracted Text':<{W}}: {r.get('extracted_mention') or '—'}")
    print(div)

def _compare_all_engines(raw: str, engine_map: dict) -> None:
    W = {"eng": 20, "canon": 34, "conf": 6, "layer": 14}
    div = "  " + "─" * (W["eng"] + W["canon"] + W["conf"] + W["layer"] + 4 * 2 + 6)
    print(f"\n  ENGINE COMPARISON  —  \"{raw}\"\n")
    print(f"  {'ENGINE':<{W['eng']}}  {'CANONICAL':<{W['canon']}}  "
          f"{'CONF':<{W['conf']}}  {'LAYER':<{W['layer']}}  STATUS")
    print(div)
    for label, eng in engine_map.items():
        if eng is None:
            print(f"  {label:<{W['eng']}}  (not loaded — missing dependency)")
            continue
        try:
            t0 = time.perf_counter()
            r  = eng.normalize(raw)
            ms = (time.perf_counter() - t0) * 1000
            canon  = (str(r.get("canonical_degree") or "—"))[:W["canon"] - 1]
            conf   = f"{r.get('confidence', 0):.3f}"
            layer  = str(r.get("layer_used") or "—")[:W["layer"] - 1]
            status = str(r.get("status") or "—")
            lbl    = str(label)[:W["eng"] - 1]
            print(f"  {lbl:<{W['eng']}}  {canon:<{W['canon']}}  "
                  f"{conf:<{W['conf']}}  {layer:<{W['layer']}}  {status}  ({ms:.1f}ms)")
        except Exception as exc:
            print(f"  {label:<{W['eng']}}  ERROR: {exc}")
    print(div)



# ══════════════════════════════════════════════════════════════════════════
# Engine loading
# ══════════════════════════════════════════════════════════════════════════

def _load_engines(data_dir: str) -> dict:
    """Load all engines. Returns dict; unavailable engines map to None."""
    engines: dict[str, object | None] = {}

    print("\n  Loading engines (this may take a moment on first run) …\n")

    from normalizer_rapidfuzz import Normalizer as RF
    from normalizer_tfidf      import NormalizerTFIDF as TFIDF

    engines["[A] L1-Only / RapidFuzz"] = RF(data_dir)
    engines["[B1] RapidFuzz"]          = engines["[A] L1-Only / RapidFuzz"]

    try:
        engines["[B2] TF-IDF"] = TFIDF(data_dir)
    except Exception as exc:
        print(f"  [B2] TF-IDF unavailable: {exc}")
        engines["[B2] TF-IDF"] = None

    try:
        from normalizer_embeddings import NormalizerEmbeddings as EMB
        emb = EMB(data_dir)
        engines["[B3] Embeddings"] = emb if emb.model else None
        if not emb.model:
            print("  [B3] Embeddings: model not loaded (install sentence-transformers torch)")
    except Exception as exc:
        print(f"  [B3] Embeddings unavailable: {exc}")
        engines["[B3] Embeddings"] = None

    try:
        from engine_l2_combined import L2CombinedEngine
        engines["[C] L2-Combined"] = L2CombinedEngine(data_dir)
    except Exception as exc:
        print(f"  [C] L2-Combined unavailable: {exc}")
        engines["[C] L2-Combined"] = None

    try:
        from engine_orchestrator import CVNormalizationOrchestrator
        mode = "full" if engines.get("[B3] Embeddings") else "standard"
        engines["[D] Orchestrator"] = CVNormalizationOrchestrator(data_dir, mode=mode)
    except Exception as exc:
        print(f"  [D] Orchestrator unavailable: {exc}")
        engines["[D] Orchestrator"] = None

    available = [k for k, v in engines.items() if v is not None]
    print(f"\n  Loaded: {len(available)}/{len(engines)} engines")
    return engines


# ══════════════════════════════════════════════════════════════════════════
# Sub-menus
# ══════════════════════════════════════════════════════════════════════════

def _sub_menu(label: str, engine: object, all_engines: dict) -> None:
    while True:
        print(f"\n  ── {label} ──")
        print("    1. Run standard test suite")
        print("    2. Normalise a custom input")
        print("    3. Batch process from CSV file")
        print("    4. Compare all engines on one input")
        print("    5. ← Back to main menu")

        sub = input("\n    Sub-choice [1-5]: ").strip()

        if sub == "1":
            t0      = time.perf_counter()
            results = engine.batch_normalize(STANDARD_TESTS)  # type: ignore[attr-defined]
            elapsed = (time.perf_counter() - t0) * 1000
            _print_result_table(
                results,
                f"{label}  ·  {elapsed:.1f}ms total  ·  {elapsed/len(results):.1f}ms avg",
            )

        elif sub == "2":
            raw = input("\n    Degree string: ").strip()
            if raw:
                r = engine.normalize(raw)  # type: ignore[attr-defined]
                _print_single_result(r)

        elif sub == "3":
            path = input("\n    CSV/TXT file path (one string per line, or column 'raw_text'): ").strip()
            if not os.path.isfile(path):
                print("    File not found.")
                continue
            inputs: list[str] = []
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    if path.endswith(".csv"):
                        reader = csv.DictReader(fh)
                        col    = "raw_text" if "raw_text" in (reader.fieldnames or []) else None
                        for row in reader:
                            val = row.get(col, "") if col else next(iter(row.values()), "")
                            if val.strip():
                                inputs.append(val.strip())
                    else:
                        inputs = [ln.strip() for ln in fh if ln.strip()]
            except Exception as exc:
                print(f"    Error reading file: {exc}")
                continue

            if not inputs:
                print("    No inputs found in file.")
                continue

            t0      = time.perf_counter()
            results = engine.batch_normalize(inputs)  # type: ignore[attr-defined]
            elapsed = (time.perf_counter() - t0) * 1000
            _print_result_table(results, f"Batch from {os.path.basename(path)}")

            save = input("\n    Save results to CSV? [y/N]: ").strip().lower()
            if save == "y":
                out_path = path.replace(".csv", "_normalized.csv").replace(".txt", "_normalized.csv")
                if not out_path.endswith("_normalized.csv"):
                    out_path += "_normalized.csv"
                with open(out_path, "w", newline="", encoding="utf-8") as fh:
                    fieldnames = ["input", "canonical_degree", "canonical_field",
                                  "confidence", "status", "layer_used", "fuzzy_score"]
                    w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
                    w.writeheader()
                    w.writerows(results)
                print(f"    Saved → {out_path}")

        elif sub == "4":
            raw = input("\n    Degree string to compare across all engines: ").strip()
            if raw:
                _compare_all_engines(raw, all_engines)

        elif sub == "5":
            break
        else:
            print("    Invalid choice.")


# ══════════════════════════════════════════════════════════════════════════
# Main menu
# ══════════════════════════════════════════════════════════════════════════

def main() -> None:
    _banner()

    engines = _load_engines(_DATA_DIR)

    # Quick-select labels in menu order
    menu_order = [
        "[A] L1-Only / RapidFuzz",
        "[B1] RapidFuzz",
        "[B2] TF-IDF",
        "[B3] Embeddings",
        "[C] L2-Combined",
        "[D] Orchestrator",
    ]
    # Deduplicate [A] and [B1] in display (they share the same object)
    display_labels = [
        ("[A+B1] RapidFuzz (L1+L2)",   "[B1] RapidFuzz"),
        ("[B2]   TF-IDF (L1+L2)",      "[B2] TF-IDF"),
        ("[B3]   Embeddings (L1+L2)",   "[B3] Embeddings"),
        ("[C]    L2 Combined (voting)", "[C] L2-Combined"),
        ("[D]    Orchestrator (full)",  "[D] Orchestrator"),
    ]

    while True:
        print("\n\n" + "═" * 70)
        print("  MAIN MENU — Select an engine")
        print("═" * 70)
        for idx, (display, key) in enumerate(display_labels, 1):
            avail  = engines.get(key) is not None
            icon   = "✅" if avail else "❌"
            suffix = "" if avail else "  (unavailable — missing dependency)"
            print(f"    {idx}.  {display:<36}  {icon}{suffix}")
        print(f"    {len(display_labels)+1}.  Compare all engines on custom input")
        print(f"    {len(display_labels)+2}.  Exit")
        print("─" * 70)

        choice = input(f"\n  Choice [1-{len(display_labels)+2}]: ").strip()

        if choice.isdigit():
            c = int(choice)
            if 1 <= c <= len(display_labels):
                display, key = display_labels[c - 1]
                eng = engines.get(key)
                if eng is None:
                    print(f"\n  {display} is not available. Install missing dependencies.")
                else:
                    _sub_menu(display, eng, engines)

            elif c == len(display_labels) + 1:
                raw = input("\n  Degree string to compare across all engines: ").strip()
                if raw:
                    _compare_all_engines(raw, {k: v for k, v in engines.items()
                                               if k not in ("[A] L1-Only / RapidFuzz",)})

            elif c == len(display_labels) + 2:
                print("\n  Goodbye.\n")
                sys.exit(0)
            else:
                print("  Invalid choice.")
        else:
            print("  Please enter a number.")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
    main()
