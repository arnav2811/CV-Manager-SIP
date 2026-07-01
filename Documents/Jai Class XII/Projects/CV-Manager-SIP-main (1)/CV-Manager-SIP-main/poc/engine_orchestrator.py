"""
CV Manager - Master Orchestrator Engine
=======================================
Runs the qualification-normalisation pipeline as:

  1. L1 exact lookup
  2. L2_Unified advanced resolution

L2_Unified contains the old Layer 2 fuzzy consensus engines and the old Layer 3
heuristic extraction logic. Callers now receive one auditable post-L1 layer
instead of two separate advanced routing steps.

Operating modes
---------------
  "fast"      L1 -> L2_Unified (RapidFuzz fuzzy only)
  "standard"  L1 -> L2_Unified (RapidFuzz + TF-IDF fuzzy consensus)
  "full"      L1 -> L2_Unified (fuzzy consensus + heuristic extraction)

Result dict keys include input, canonical_degree, canonical_field, confidence,
status, layer_used, fuzzy_score, alternatives, engine, mode, resolution_strategy,
and audit.

Run:  python engine_orchestrator.py
"""

from __future__ import annotations

import os
import sys
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from normalizer_rapidfuzz import Normalizer       as _RF
from engine_l2_l3_unified import UnifiedAdvancedLayer as _Unified

ENGINE_ID = "Orchestrator_v3"
VERSION   = "3.6.5"


class CVNormalizationOrchestrator:
    """
    Full-stack normalisation orchestrator.

    Instantiate once per process; the alias dictionary and embedding
    index are shared across all engines loaded at startup.
    """

    VALID_MODES = ("fast", "standard", "full")

    def __init__(self, data_dir: str = "../data", mode: str = "full"):
        if mode not in self.VALID_MODES:
            raise ValueError(f"mode must be one of {self.VALID_MODES}")

        self.data_dir = data_dir
        self.mode     = mode
        self._engines: dict[str, object] = {}
        self._advanced_layer: _Unified | None = None

        self._init(mode)

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init(self, mode: str) -> None:
        print(f"\n[Orchestrator] Initialising — mode={mode!r}")

        # Always load RapidFuzz (used for L1 + fast L2)
        try:
            self._engines["rf"] = _RF(self.data_dir)
            print("[Orchestrator] OK RapidFuzz engine ready")
        except Exception as exc:
            raise RuntimeError(f"RapidFuzz engine failed to load: {exc}") from exc

        try:
            self._advanced_layer = _Unified(
                self.data_dir,
                mode=mode,
                existing_rf=self._rf_engine(),
            )
            print("[Orchestrator] OK unified advanced layer ready")
        except Exception as exc:
            raise RuntimeError(f"Unified advanced layer failed to load: {exc}") from exc

        active = list(self._engines.keys())
        print(f"[Orchestrator] Active engines: {active}  unified_layer=yes")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _rf_engine(self) -> _RF:
        return self._engines["rf"]  # type: ignore[return-value]

    @staticmethod
    def _make_base_result(raw_string: str, mode: str) -> dict:
        return {
            "input":            raw_string,
            "canonical_degree": None,
            "canonical_field":  None,
            "confidence":       0.0,
            "status":           "unresolved",
            "layer_used":       "unresolved",
            "fuzzy_score":      0,
            "alternatives":     [],
            "engine":           ENGINE_ID,
            "mode":             mode,
            "resolution_strategy": "unresolved",
            "audit":            {},
        }

    def _l1_pass(self, raw_string: str, result: dict) -> bool:
        """
        Run L1 exact-match via RapidFuzz engine (dict is identical for all).
        Returns True and mutates *result* if resolved.
        """
        rf      = self._rf_engine()
        cleaned, extracted_field = rf.clean(raw_string)
        canonical_field = rf._normalize_field(extracted_field)
        result["canonical_field"] = canonical_field

        t0 = time.perf_counter()
        l1 = rf.layer1_lookup(cleaned)
        elapsed = (time.perf_counter() - t0) * 1000

        result["audit"]["L1"] = {
            "cleaned":   cleaned,
            "hit":       l1 is not None,
            "latency_ms": round(elapsed, 3),
        }

        if l1:
            result.update({
                "canonical_degree": l1["canonical_degree"],
                "confidence":       1.0,
                "status":           "resolved",
                "layer_used":       "L1",
                "fuzzy_score":      100,
                "alternatives":     [],
                "resolution_strategy": "exact_lookup",
            })
            return True
        return False

    def _advanced_pass(self, raw_string: str, result: dict) -> bool:
        """
        Run the unified advanced layer after L1 misses.

        The unified layer contains the old Layer 2 fuzzy consensus and Layer 3
        heuristic extraction, so callers see one post-L1 layer: L2_Unified.
        """
        if self._advanced_layer is None:
            return False

        t0 = time.perf_counter()
        advanced = self._advanced_layer.resolve_after_l1(
            raw_string,
            canonical_field=result.get("canonical_field"),
        )
        elapsed = (time.perf_counter() - t0) * 1000

        advanced_audit = advanced.pop("audit", {})
        advanced_audit["latency_ms"] = round(elapsed, 3)
        result["audit"]["L2_Unified"] = advanced_audit

        if advanced.get("status") == "unresolved":
            result.update({
                "canonical_degree": advanced.get("canonical_degree"),
                "canonical_field": advanced.get("canonical_field") or result.get("canonical_field"),
                "confidence": advanced.get("confidence", 0.0),
                "status": advanced.get("status", "unresolved"),
                "layer_used": advanced.get("layer_used", "unresolved"),
                "fuzzy_score": advanced.get("fuzzy_score", 0),
                "alternatives": advanced.get("alternatives", []),
                "resolution_strategy": advanced.get("resolution_strategy", "unresolved"),
            })
            return False

        result.update(advanced)
        result["engine"] = ENGINE_ID
        result["mode"] = self.mode
        return True

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def normalize(self, raw_string: str) -> dict:
        """
        Normalise a single raw education string.  Always returns a dict;
        never raises.
        """
        result = self._make_base_result(raw_string, self.mode)

        # ── Layer 1 ────────────────────────────────────────────────────
        if self._l1_pass(raw_string, result):
            return result

        # Unified advanced layer: fuzzy consensus + heuristic extraction.
        self._advanced_pass(raw_string, result)
        return result

    def batch_normalize(self, inputs: list[str]) -> list[dict]:
        return [self.normalize(s) for s in inputs]

    def compare_all_engines(self, raw_string: str) -> dict:
        """
        Run *raw_string* through every sub-engine independently and return
        a structured comparison report.  Useful for benchmarking and tuning.
        """
        report: dict[str, dict] = {}
        for key, eng in self._engines.items():
            try:
                report[key] = eng.normalize(raw_string)
            except Exception as exc:
                report[key] = {"error": str(exc)}

        if self._advanced_layer:
            report["advanced"] = self._advanced_layer.normalize(raw_string)

        report["orchestrated"] = self.normalize(raw_string)
        return report


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys as _sys
    if hasattr(_sys.stdout, "reconfigure") and _sys.stdout.encoding.lower() != "utf-8":
        _sys.stdout.reconfigure(encoding="utf-8")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "..", "data")

    TEST_CASES = [
        "B.Tech",
        "BTech",
        "Bachelor of Technology",
        "Bacheler of Technology",
        "B. Tech in CSE",
        "M.Tech (Computer Science)",
        "MBA",
        "Bachellor of Technolgy in CSE",
        "BE Hons",
        "12th",
        "B.Pharma",
        "Bachelor of Business Administration",
        "Bachelor of Business Admin",
        "BBA",
        "Kuchh bhi degree",
        "I completed my Masters in Data Science from IIT Delhi",
        "Have a diploma in Mechanical from a polytechnic",
    ]

    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " CV MANAGER · Orchestrator v3.6.5 ".center(68) + "║")
    print("║" + " Growth Grids × University of Southampton ".center(68) + "║")
    print("╚" + "═" * 68 + "╝")
    print("\n  Select operating mode:")
    print("    1  fast      — L1 + RapidFuzz only          (lowest latency)")
    print("    2  standard  — L1 + RapidFuzz + TF-IDF      (recommended)")
    print("    3  full      - L1 + L2_Unified fuzzy+heuristic (max recall)")

    mode_choice = input("\n  Mode [1/2/3, default=2]: ").strip() or "2"
    mode_map    = {"1": "fast", "2": "standard", "3": "full"}
    mode        = mode_map.get(mode_choice, "standard")

    orch = CVNormalizationOrchestrator(data_dir, mode=mode)

    while True:
        print(f"\n\n{'='*70}")
        print(f"  Orchestrator  [mode={mode}]")
        print("=" * 70)
        print("  1. Run default test suite")
        print("  2. Enter custom degree string")
        print("  3. Compare all engines on one input")
        print("  4. Exit")

        choice = input("\n  Choice [1/2/3/4]: ").strip()

        if choice == "1":
            t_start  = time.perf_counter()
            results  = orch.batch_normalize(TEST_CASES)
            t_total  = (time.perf_counter() - t_start) * 1000
            W = {"inp": 36, "canon": 32, "layer": 13, "conf": 6}
            div = "  " + "─" * (W["inp"] + W["canon"] + W["layer"] + W["conf"] + 4 * 2 + 6)
            print(f"\n  {len(TEST_CASES)} inputs · mode={mode}")
            print()
            print(f"  {'INPUT':<{W['inp']}}  {'CANONICAL':<{W['canon']}}  "
                  f"{'LAYER':<{W['layer']}}  {'CONF':<{W['conf']}}  STATUS")
            print(div)
            stats = {"resolved": 0, "fuzzy_matched": 0, "review_needed": 0, "unresolved": 0}
            for r in results:
                inp    = (r["input"] or "")[:W["inp"] - 1]
                canon  = (r["canonical_degree"] or "—")[:W["canon"] - 1]
                layer  = r["layer_used"][:W["layer"] - 1]
                conf   = f"{r['confidence']:.2f}"
                status = r["status"]
                print(f"  {inp:<{W['inp']}}  {canon:<{W['canon']}}  "
                      f"{layer:<{W['layer']}}  {conf:<{W['conf']}}  {status}")
                if r.get("canonical_field"):
                    print(f"  {'':>{W['inp']}}  ↳ field: {r['canonical_field']}")
                stats[status] = stats.get(status, 0) + 1
            print(div)
            total = len(TEST_CASES)
            print(f"\n  Total time: {t_total:.1f} ms   avg: {t_total/total:.1f} ms/input")
            print(f"\n  {'STATUS':<18}  {'N':>4}  {'%':>5}")
            print(f"  {'─'*18}  {'─'*4}  {'─'*5}")
            for k, v in stats.items():
                if v:
                    print(f"  {k:<18}  {v:>4}  {v/total*100:>4.0f}%")


        elif choice == "2":
            raw = input("\n  Enter degree string: ").strip()
            if not raw:
                continue
            r = orch.normalize(raw)
            print("\n  " + "─" * 60)
            print("  ORCHESTRATOR RESULT")
            print("  " + "─" * 60)
            print(f"  Input            : {r['input']}")
            print(f"  Canonical Degree : {r['canonical_degree'] or 'None'}")
            print(f"  Canonical Field  : {r['canonical_field']  or 'None'}")
            print(f"  Layer Used       : {r['layer_used']}")
            print(f"  Confidence       : {r['confidence']:.4f}")
            print(f"  Fuzzy Score      : {r['fuzzy_score']}")
            print(f"  Status           : {r['status']}")
            if r.get("resolution_strategy"):
                print(f"  Resolution       : {r['resolution_strategy']}")
            print(f"  Mode             : {r['mode']}")
            if r.get("alternatives"):
                print("\n  Alternatives:")
                for alt, sc in r["alternatives"]:
                    print(f"    • {alt:<35}  {sc:.4f}")
            if r.get("audit"):
                print("\n  Audit Trail:")
                for layer, info in r["audit"].items():
                    print(f"    [{layer}]")
                    if isinstance(info, dict):
                        for k, v in info.items():
                            if k != "engines":
                                print(f"       {k}: {v}")
                        if "engines" in info:
                            for ed in info["engines"]:
                                print(f"       ↳ {ed['engine']:<12}  {ed.get('result','—'):<28}  "
                                      f"conf={ed.get('conf',0):.3f}  {ed.get('ms',0):.1f}ms")
            print("  " + "─" * 60)

        elif choice == "3":
            raw = input("\n  Enter degree string for engine comparison: ").strip()
            if not raw:
                continue
            report = orch.compare_all_engines(raw)
            print(f"\n  ENGINE COMPARISON  —  input: {raw!r}\n")
            print(f"  {'ENGINE':<16} {'CANONICAL':<32} {'CONF':<6} {'LAYER':<14} STATUS")
            print("  " + "-" * 85)
            for eng_key, res in report.items():
                if "error" in res:
                    print(f"  {eng_key:<16}  ERROR: {res['error']}")
                    continue
                eng   = eng_key
                canon = (res.get("canonical_degree") or "-")[:30]
                conf  = f"{res.get('confidence', 0):.3f}"
                layer = res.get("layer_used", "-")
                stat  = res.get("status", "-")
                print(f"  {eng:<16} {canon:<32} {conf:<6} {layer:<14} {stat}")
                if res.get("canonical_field"):
                    print(f"  {'':>16} ↳ field: {res['canonical_field']}")
            print("  " + "-" * 85)

        elif choice == "4":
            print("  Exiting.")
            _sys.exit(0)
        else:
            print("  Invalid choice.")
