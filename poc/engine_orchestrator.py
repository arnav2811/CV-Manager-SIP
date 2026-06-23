"""
CV Manager — Master Orchestrator Engine  (Full 3-Layer Pipeline)
================================================================
Combines all layers and sub-engines into one unified normalisation
pipeline.  Callers interact with a single class that:

  1. Loads and shares one alias dictionary (L1 data store)
  2. Routes inputs through the correct layer sequence
  3. Returns a rich, auditable result dict

Operating modes
---------------
  "fast"      L1 → L2 (RapidFuzz only)
               Lowest latency; best for high-throughput structured feeds.
               Thresholds: auto=88, review=70.

  "standard"  L1 → L2 (RapidFuzz + TF-IDF consensus)
               Best balance of speed and accuracy.  Recommended default.
               Embeddings engine skipped.

  "full"      L1 → L2 (all 3 engines, consensus) → L3 (heuristics)
               Highest recall; parses conversational text.
               Requires sentence-transformers + torch installed.

Result dict keys (all modes)
-----------------------------
  input             str    — original raw string
  canonical_degree  str|None
  canonical_field   str|None
  confidence        float  [0.0 – 1.0]
  status            str    resolved | fuzzy_matched | review_needed |
                           unresolved
  layer_used        str    L1 | L2 | L2_TFIDF | L2_Combined |
                           L3 | unresolved
  fuzzy_score       float  [0 – 100]  (100 for L1 hits)
  alternatives      list   [(canonical, score), …]
  engine            str    engine identifier string
  mode              str    operating mode used
  audit             dict   per-layer timing/decision trace

Run:  python engine_orchestrator.py
"""

from __future__ import annotations

import os
import sys
import time
from typing import Optional

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Sub-engine imports with graceful fallback
from normalizer_rapidfuzz import Normalizer       as _RF
from normalizer_tfidf      import NormalizerTFIDF as _TFIDF

try:
    from normalizer_embeddings import NormalizerEmbeddings as _EMB
    _EMB_AVAILABLE = True
except ImportError:
    _EMB_AVAILABLE = False

from engine_l3 import L3HeuristicEngine as _L3

ENGINE_ID = "Orchestrator_v3"
VERSION   = "3.0.0"


class CVNormalizationOrchestrator:
    """
    Full-stack normalisation orchestrator.

    Instantiate once per process; the alias dictionary and embedding
    index are shared across all engines loaded at startup.
    """

    VALID_MODES = ("fast", "standard", "full")

    def __init__(self, data_dir: str = "../data", mode: str = "standard"):
        if mode not in self.VALID_MODES:
            raise ValueError(f"mode must be one of {self.VALID_MODES}")

        self.data_dir = data_dir
        self.mode     = mode
        self._engines: dict[str, object] = {}
        self._l3: Optional[_L3] = None

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

        if mode in ("standard", "full"):
            try:
                self._engines["tfidf"] = _TFIDF(self.data_dir)
                print("[Orchestrator] OK TF-IDF engine ready")
            except Exception as exc:
                print(f"[Orchestrator] X TF-IDF unavailable: {exc}")

        if mode == "full" and _EMB_AVAILABLE:
            try:
                emb = _EMB(self.data_dir)
                if emb.model is not None:
                    self._engines["emb"] = emb
                    print("[Orchestrator] OK Embeddings engine ready")
                else:
                    print("[Orchestrator] X Embeddings: model not loaded")
            except Exception as exc:
                print(f"[Orchestrator] X Embeddings unavailable: {exc}")

        if mode == "full":
            self._l3 = _L3()
            print("[Orchestrator] OK L3 Heuristic engine ready")

        active = list(self._engines.keys())
        print(f"[Orchestrator] Active engines: {active}  L3={'yes' if self._l3 else 'no'}")

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
            })
            return True
        return False

    def _l2_pass(self, raw_string: str, result: dict) -> bool:
        """
        Run L2 on all available engines and fuse via weighted voting.
        Returns True and mutates *result* if a usable match is found.
        """
        rf      = self._rf_engine()
        cleaned, _ = rf.clean(raw_string)

        votes: dict[str, float] = {}
        vote_count: dict[str, int] = {}
        engine_debug: list[dict]   = []

        # --- RapidFuzz ---
        t0   = time.perf_counter()
        rf_r = rf.layer2_fuzzy(cleaned)
        rf_ms = (time.perf_counter() - t0) * 1000
        if rf_r:
            c = rf_r["canonical_degree"]
            votes[c]      = votes.get(c, 0.0) + 0.45 * rf_r["confidence"]
            vote_count[c] = vote_count.get(c, 0) + 1
        engine_debug.append({
            "engine":   "RapidFuzz",
            "result":   rf_r["canonical_degree"] if rf_r else None,
            "conf":     round(rf_r["confidence"], 4) if rf_r else 0,
            "ms":       round(rf_ms, 2),
        })

        # --- TF-IDF (standard / full) ---
        if "tfidf" in self._engines:
            tf  = self._engines["tfidf"]
            t0  = time.perf_counter()
            tf_r = tf.layer2_fuzzy(cleaned)
            tf_ms = (time.perf_counter() - t0) * 1000
            if tf_r:
                c = tf_r["canonical_degree"]
                votes[c]      = votes.get(c, 0.0) + 0.30 * tf_r["confidence"]
                vote_count[c] = vote_count.get(c, 0) + 1
            engine_debug.append({
                "engine": "TF-IDF",
                "result": tf_r["canonical_degree"] if tf_r else None,
                "conf":   round(tf_r["confidence"], 4) if tf_r else 0,
                "ms":     round(tf_ms, 2),
            })

        # --- Embeddings (full mode only) ---
        if "emb" in self._engines:
            emb  = self._engines["emb"]
            t0   = time.perf_counter()
            emb_r = emb.layer2_fuzzy(cleaned)
            emb_ms = (time.perf_counter() - t0) * 1000
            if emb_r:
                c = emb_r["canonical_degree"]
                votes[c]      = votes.get(c, 0.0) + 0.25 * emb_r["confidence"]
                vote_count[c] = vote_count.get(c, 0) + 1
            engine_debug.append({
                "engine": "Embeddings",
                "result": emb_r["canonical_degree"] if emb_r else None,
                "conf":   round(emb_r["confidence"], 4) if emb_r else 0,
                "ms":     round(emb_ms, 2),
            })

        result["audit"]["L2"] = {
            "engines": engine_debug,
            "votes":   {k: round(v, 4) for k, v in votes.items()},
        }

        if not votes:
            return False

        winner    = max(votes, key=votes.get)
        raw_conf  = votes[winner]
        n_agree   = vote_count.get(winner, 0)
        n_engines = len(engine_debug)

        # Consensus bonus
        if n_engines > 1 and n_agree >= 2:
            raw_conf = min(1.0, raw_conf + 0.05)

        alt_list = [
            (can, round(sc, 4))
            for can, sc in sorted(votes.items(), key=lambda x: -x[1])
            if can != winner
        ][:3]

        # Fast mode: use raw RapidFuzz score for threshold check
        if self.mode == "fast" and rf_r:
            raw_conf = rf_r["confidence"]

        if raw_conf >= 0.82:
            status    = "fuzzy_matched"
            layer_tag = "L2" if self.mode == "fast" else "L2_Combined"
        elif raw_conf >= 0.60:
            status    = "review_needed"
            layer_tag = "L2" if self.mode == "fast" else "L2_Combined"
        else:
            return False

        result.update({
            "canonical_degree": winner,
            "confidence":       round(raw_conf, 4),
            "status":           status,
            "layer_used":       layer_tag,
            "fuzzy_score":      round(raw_conf * 100, 1),
            "alternatives":     alt_list,
        })
        return True

    def _l3_pass(self, raw_string: str, result: dict) -> bool:
        """
        Run L3 heuristic engine. Returns True if any signal found.
        """
        if self._l3 is None:
            return False

        t0   = time.perf_counter()
        l3_r = self._l3.analyze(raw_string)
        ms   = (time.perf_counter() - t0) * 1000

        result["audit"]["L3"] = {
            "fired":      l3_r is not None,
            "strategy":   l3_r.get("strategy") if l3_r else None,
            "latency_ms": round(ms, 3),
        }

        if not l3_r:
            return False

        result.update({
            "canonical_degree": l3_r.get("canonical_degree"),
            "canonical_field":  l3_r.get("field_mention") or result.get("canonical_field"),
            "confidence":       l3_r.get("confidence", 0.0),
            "status":           "review_needed",
            "layer_used":       "L3",
            "fuzzy_score":      round(l3_r.get("confidence", 0.0) * 100, 1),
        })
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

        # ── Layer 2 ────────────────────────────────────────────────────
        l2_hit = self._l2_pass(raw_string, result)
        if l2_hit and result["status"] == "fuzzy_matched":
            return result

        # ── Layer 3 (full mode only) ───────────────────────────────────
        if not l2_hit or result["status"] == "review_needed":
            if self._l3:
                self._l3_pass(raw_string, result)

        return result

    def batch_normalize(self, inputs: list[str]) -> list[dict]:
        return [self.normalize(s) for s in inputs]

    def compare_all_engines(self, raw_string: str) -> dict:
        """
        Run *raw_string* through every sub-engine independently and return
        a structured comparison report.  Useful for benchmarking and tuning.
        """
        report: dict[str, dict] = {}
        rf = self._rf_engine()

        for key, eng in self._engines.items():
            try:
                report[key] = eng.normalize(raw_string)
            except Exception as exc:
                report[key] = {"error": str(exc)}

        if self._l3:
            report["l3"] = self._l3.normalize(raw_string)

        report["orchestrated"] = self.normalize(raw_string)
        return report


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys as _sys

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

    print("\n" + "=" * 70)
    print("  CV MANAGER · Orchestrator v3.0.0")
    print("=" * 70)
    print("\n  Select operating mode:")
    print("    1  fast      — L1 + RapidFuzz only          (lowest latency)")
    print("    2  standard  — L1 + RapidFuzz + TF-IDF      (recommended)")
    print("    3  full      — L1 + L2 Combined + L3         (max recall, needs torch)")

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
