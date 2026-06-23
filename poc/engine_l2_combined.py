"""
CV Manager — Layer 2 Combined Engine  (Consensus Voting)
=========================================================
Runs all three Layer 2 sub-engines in parallel and fuses their outputs
using a weighted confidence-vote strategy.

Voting strategy
---------------
Each available engine casts a vote for its top canonical match weighted
by its normalised confidence score:

    vote_weight = engine_base_weight × confidence_score

Canonical names are accumulated across all engines; the one with the
highest total weight wins.  Consensus bonus: if ≥ 2 engines agree, the
winning confidence is boosted by +0.05 (capped at 1.0).

Engine base weights (tuned empirically):
    RapidFuzz   0.35  — typo-resilient, fast, lightweight
    TF-IDF      0.30  — character n-gram, sub-millisecond
    Embeddings  0.35  — semantic synonyms (only when available)

If sentence-transformers is not installed, Embeddings is skipped and
weights are re-normalised over the two remaining engines automatically.

Run:  python engine_l2_combined.py
"""

from __future__ import annotations

import os
import sys
from collections import defaultdict
from typing import Optional

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from normalizer_rapidfuzz import Normalizer          as _RF
from normalizer_tfidf      import NormalizerTFIDF    as _TFIDF
from normalizer_embeddings import NormalizerEmbeddings as _EMB

ENGINE_ID = "L2_Combined"

# -----------------------------------------------------------------------
# Internal engine weights
# -----------------------------------------------------------------------
_WEIGHTS: dict[str, float] = {
    "rapidfuzz":  0.35,
    "tfidf":      0.30,
    "embeddings": 0.35,
}


class L2CombinedEngine:
    """
    Unified Layer-2 engine that aggregates RapidFuzz, TF-IDF, and
    (optionally) Embeddings via weighted consensus voting.
    """

    def __init__(self, data_dir: str = "../data"):
        self.data_dir = data_dir
        self._rf:  Optional[_RF]   = None
        self._tf:  Optional[_TFIDF] = None
        self._emb: Optional[_EMB]  = None
        self._available: list[str] = []

        self._init_engines()

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def _init_engines(self) -> None:
        print("[L2-Combined] Initialising sub-engines …")

        try:
            self._rf = _RF(self.data_dir)
            self._available.append("rapidfuzz")
        except Exception as exc:
            print(f"[L2-Combined] RapidFuzz unavailable: {exc}")

        try:
            self._tf = _TFIDF(self.data_dir)
            self._available.append("tfidf")
        except Exception as exc:
            print(f"[L2-Combined] TF-IDF unavailable: {exc}")

        try:
            self._emb = _EMB(self.data_dir)
            if self._emb.model is not None:          # only if model loaded OK
                self._available.append("embeddings")
            else:
                self._emb = None
        except Exception as exc:
            print(f"[L2-Combined] Embeddings unavailable: {exc}")
            self._emb = None

        print(f"[L2-Combined] Active sub-engines: {', '.join(self._available) or 'NONE'}")

    # ------------------------------------------------------------------
    # Voting core
    # ------------------------------------------------------------------

    def _vote(self, raw_string: str) -> dict:
        """
        Run all available engines, collect votes, pick winner.
        Returns a fully populated result dict.
        """
        # ── collect individual engine results ──────────────────────────
        engine_results: dict[str, Optional[dict]] = {}

        if self._rf:
            engine_results["rapidfuzz"] = self._rf.normalize(raw_string)
        if self._tf:
            engine_results["tfidf"]     = self._tf.normalize(raw_string)
        if self._emb:
            engine_results["embeddings"] = self._emb.normalize(raw_string)

        # Use RapidFuzz result for field extraction (any engine works —
        # field is extracted at the clean() stage which is identical)
        ref_result = (
            engine_results.get("rapidfuzz")
            or engine_results.get("tfidf")
            or {}
        )
        canonical_field = ref_result.get("canonical_field")

        # ── re-normalise weights to available engines ──────────────────
        active_weights = {k: _WEIGHTS[k] for k in self._available}
        total_w = sum(active_weights.values())
        norm_w  = {k: v / total_w for k, v in active_weights.items()}

        # ── tally votes ────────────────────────────────────────────────
        vote_tally: dict[str, float] = defaultdict(float)
        vote_count: dict[str, int]   = defaultdict(int)
        engine_detail: list[dict]    = []

        for eng_name, res in engine_results.items():
            if res is None:
                continue
            canon  = res.get("canonical_degree")
            status = res.get("status", "unresolved")
            conf   = res.get("confidence", 0.0)

            if canon and status not in ("unresolved",):
                weight = norm_w.get(eng_name, 0.0)
                vote_tally[canon] += weight * conf
                vote_count[canon] += 1

            engine_detail.append({
                "engine":     eng_name,
                "canonical":  canon,
                "confidence": round(conf, 4),
                "status":     status,
                "layer":      res.get("layer_used", "-"),
            })

        # ── determine winner ───────────────────────────────────────────
        if not vote_tally:
            return {
                "input":            raw_string,
                "layer_used":       "unresolved",
                "canonical_degree": None,
                "canonical_field":  canonical_field,
                "confidence":       0.0,
                "status":           "unresolved",
                "fuzzy_score":      0,
                "alternatives":     [],
                "engine":           ENGINE_ID,
                "engine_detail":    engine_detail,
            }

        winner       = max(vote_tally, key=vote_tally.get)
        raw_conf     = vote_tally[winner]
        agree_count  = vote_count[winner]
        n_engines    = len(engine_results)

        # Consensus bonus
        if n_engines > 1 and agree_count >= 2:
            raw_conf = min(1.0, raw_conf + 0.05)

        # Determine status thresholds
        if raw_conf >= 0.82:
            status = "fuzzy_matched"
        elif raw_conf >= 0.60:
            status = "review_needed"
        else:
            status = "unresolved"

        # Build alternatives (other candidates with votes, sorted by tally)
        alt_list = [
            (can, round(sc, 4))
            for can, sc in sorted(vote_tally.items(), key=lambda x: -x[1])
            if can != winner
        ][:3]

        return {
            "input":            raw_string,
            "layer_used":       "L2_Combined",
            "canonical_degree": winner  if status != "unresolved" else None,
            "canonical_field":  canonical_field,
            "confidence":       round(raw_conf, 4),
            "status":           status,
            "fuzzy_score":      round(raw_conf * 100, 1),
            "alternatives":     alt_list,
            "engine":           ENGINE_ID,
            "engine_detail":    engine_detail,
            "consensus_votes":  agree_count,
            "engines_polled":   n_engines,
        }

    # ------------------------------------------------------------------
    # Public interface — mirrors the standalone normalizer API
    # ------------------------------------------------------------------

    def normalize(self, raw_string: str) -> dict:
        """Full L1 → L2 (combined) pipeline."""
        # Try L1 via RapidFuzz (all engines share the same dict)
        if self._rf:
            cleaned, _ = self._rf.clean(raw_string)
            l1 = self._rf.layer1_lookup(cleaned)
            if l1:
                l1["input"]         = raw_string
                l1["canonical_field"] = self._rf._normalize_field(
                    self._rf.clean(raw_string)[1]
                )
                l1["engine"]        = ENGINE_ID
                l1["engine_detail"] = [{"engine": "L1_dict", "layer": "L1"}]
                return l1

        # L2 combined voting
        return self._vote(raw_string)

    def batch_normalize(self, inputs: list[str]) -> list[dict]:
        return [self.normalize(s) for s in inputs]


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys as _sys

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "..", "data")
    engine   = L2CombinedEngine(data_dir)

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
        "I completed my Masters in Data Science from IIT",
    ]

    while True:
        print("\n" + "=" * 65)
        print("  CV MANAGER · L2 Combined Engine   [consensus voting CLI]")
        print("=" * 65)
        print("  1. Run default test suite")
        print("  2. Enter custom degree string  (with per-engine breakdown)")
        print("  3. Exit")

        choice = input("\n  Choice [1/2/3]: ").strip()

        if choice == "1":
            results = engine.batch_normalize(TEST_CASES)
            W = {"inp": 33, "canon": 32, "conf": 6, "votes": 7}
            div = "  " + "─" * (W["inp"] + W["canon"] + W["conf"] + W["votes"] + 4 * 2 + 6)
            print(f"\n  {len(TEST_CASES)} inputs · L2 Combined consensus engine")
            print()
            print(f"  {'INPUT':<{W['inp']}}  {'CANONICAL':<{W['canon']}}  "
                  f"{'CONF':<{W['conf']}}  {'VOTES':<{W['votes']}}  STATUS")
            print(div)
            stats = {"L1": 0, "L2": 0, "review": 0, "unresolved": 0}
            for r in results:
                inp    = (r["input"] or "")[:W["inp"] - 1]
                canon  = (r["canonical_degree"] or "—")[:W["canon"] - 1]
                conf   = f"{r['confidence']:.2f}"
                votes  = f"{r.get('consensus_votes', '—')}/{r.get('engines_polled', '—')}"
                status = r["status"]
                print(f"  {inp:<{W['inp']}}  {canon:<{W['canon']}}  "
                      f"{conf:<{W['conf']}}  {votes:<{W['votes']}}  {status}")
                if r.get("canonical_field"):
                    print(f"  {'':>{W['inp']}}  ↳ field: {r['canonical_field']}")
                layer = r["layer_used"]
                if   layer.startswith("L1"):   stats["L1"]         += 1
                elif "L2" in layer:            stats["L2"]         += 1
                elif status == "review_needed": stats["review"]    += 1
                else:                           stats["unresolved"] += 1
            print(div)
            total = len(TEST_CASES)
            print(f"\n  {'LAYER/STATUS':<14}  {'N':>4}  {'%':>5}")
            print(f"  {'─'*14}  {'─'*4}  {'─'*5}")
            for k, v in stats.items():
                if v:
                    print(f"  {k:<14}  {v:>4}  {v/total*100:>4.0f}%")


        elif choice == "2":
            raw = input("\n  Enter degree string: ").strip()
            if not raw:
                continue
            r = engine.normalize(raw)
            print("\n  " + "─" * 55)
            print("  COMBINED ENGINE RESULT")
            print("  " + "─" * 55)
            print(f"  Input            : {r['input']}")
            print(f"  Canonical Degree : {r['canonical_degree'] or 'None'}")
            print(f"  Canonical Field  : {r['canonical_field']  or 'None'}")
            print(f"  Layer Used       : {r['layer_used']}")
            print(f"  Confidence       : {r['confidence']:.4f}")
            print(f"  Status           : {r['status']}")
            print(f"  Consensus        : {r.get('consensus_votes','-')}/{r.get('engines_polled','-')} engines agreed")
            if r["alternatives"]:
                print("\n  Alternatives (by vote weight):")
                for alt, sc in r["alternatives"]:
                    print(f"    • {alt:<35}  weight={sc:.4f}")
            if r.get("engine_detail"):
                print("\n  Per-engine breakdown:")
                for d in r["engine_detail"]:
                    print(f"    [{d['engine']:<12}]  {d.get('canonical','—'):<30}  "
                          f"conf={d.get('confidence',0):.3f}  {d.get('status','-')}")
            print("  " + "─" * 55)

        elif choice == "3":
            _sys.exit(0)
        else:
            print("  Invalid choice.")
