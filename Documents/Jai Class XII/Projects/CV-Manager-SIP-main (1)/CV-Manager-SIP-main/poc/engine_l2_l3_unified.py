"""
CV Manager - Unified Advanced Resolution Layer
==============================================
Combines the old Layer 2 fuzzy engines and Layer 3 heuristic extraction behind
one public layer. The orchestrator can now route:

    L1 exact lookup -> L2_Unified advanced resolution

The unified layer first attempts fuzzy consensus. If fuzzy confidence is low or
absent, it runs heuristic extraction in the same layer and chooses the strongest
usable result while preserving a detailed audit trail.
"""

from __future__ import annotations

import os
import sys
import time
from collections import defaultdict
from typing import Optional

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from normalizer_rapidfuzz import Normalizer as _RF
from engine_l3 import L3HeuristicEngine as _L3


ENGINE_ID = "L2_L3_Unified"

_WEIGHTS: dict[str, float] = {
    "rapidfuzz": 0.35,
    "tfidf": 0.30,
    "embeddings": 0.35,
}


class UnifiedAdvancedLayer:
    """
    Single advanced resolution layer combining fuzzy matching and heuristics.

    Modes:
      fast      RapidFuzz fuzzy only
      standard  RapidFuzz + TF-IDF fuzzy consensus
      full      RapidFuzz + TF-IDF + optional embeddings + L3 heuristics
    """

    VALID_MODES = ("fast", "standard", "full")

    def __init__(
        self,
        data_dir: str = "../data",
        mode: str = "full",
        existing_rf: Optional[_RF] = None,
        enable_heuristic: Optional[bool] = None,
    ):
        if mode not in self.VALID_MODES:
            raise ValueError(f"mode must be one of {self.VALID_MODES}")

        self.data_dir = data_dir
        self.mode = mode
        self._rf: Optional[_RF] = existing_rf
        self._tf = None
        self._emb = None
        self._l3: Optional[_L3] = None
        self._available: list[str] = []

        self._init_engines(enable_heuristic)

    def _init_engines(self, enable_heuristic: Optional[bool]) -> None:
        if self._rf is None:
            self._rf = _RF(self.data_dir)
        self._available.append("rapidfuzz")

        if self.mode in ("standard", "full"):
            try:
                from normalizer_tfidf import NormalizerTFIDF as _TFIDF

                self._tf = _TFIDF(self.data_dir)
                self._available.append("tfidf")
            except Exception as exc:
                print(f"[UnifiedLayer] TF-IDF unavailable: {exc}")

        if self.mode == "full":
            try:
                from normalizer_embeddings import NormalizerEmbeddings as _EMB

                emb = _EMB(self.data_dir)
                if emb.model is not None:
                    self._emb = emb
                    self._available.append("embeddings")
                else:
                    print("[UnifiedLayer] Embeddings unavailable: model not loaded")
            except Exception as exc:
                print(f"[UnifiedLayer] Embeddings unavailable: {exc}")

        use_heuristic = self.mode == "full" if enable_heuristic is None else enable_heuristic
        if use_heuristic:
            self._l3 = _L3()

        active = ", ".join(self._available) or "none"
        print(
            f"[UnifiedLayer] Active fuzzy engines: {active}; "
            f"heuristic={'yes' if self._l3 else 'no'}"
        )

    def _rf_engine(self) -> _RF:
        if self._rf is None:
            raise RuntimeError("RapidFuzz engine is not available")
        return self._rf

    def _run_fuzzy(self, raw_string: str) -> dict:
        rf = self._rf_engine()
        cleaned, extracted_field = rf.clean(raw_string)
        canonical_field = rf._normalize_field(extracted_field)

        engine_results: dict[str, Optional[dict]] = {}
        engine_detail: list[dict] = []

        def poll(name: str, engine: object) -> None:
            t0 = time.perf_counter()
            try:
                result = engine.layer2_fuzzy(cleaned)  # type: ignore[attr-defined]
            except Exception as exc:
                result = None
                engine_detail.append(
                    {
                        "engine": name,
                        "result": None,
                        "confidence": 0.0,
                        "status": "error",
                        "error": str(exc),
                        "ms": round((time.perf_counter() - t0) * 1000, 2),
                    }
                )
                engine_results[name] = result
                return

            ms = (time.perf_counter() - t0) * 1000
            engine_results[name] = result
            engine_detail.append(
                {
                    "engine": name,
                    "result": result.get("canonical_degree") if result else None,
                    "confidence": round(result.get("confidence", 0.0), 4) if result else 0.0,
                    "status": result.get("status", "unresolved") if result else "unresolved",
                    "layer": result.get("layer_used", "-") if result else "-",
                    "ms": round(ms, 2),
                }
            )

        poll("rapidfuzz", rf)
        if self._tf is not None:
            poll("tfidf", self._tf)
        if self._emb is not None:
            poll("embeddings", self._emb)

        active_weights = {k: _WEIGHTS[k] for k in self._available}
        total_weight = sum(active_weights.values()) or 1.0
        norm_weights = {k: v / total_weight for k, v in active_weights.items()}

        votes: dict[str, float] = defaultdict(float)
        vote_count: dict[str, int] = defaultdict(int)
        for engine_name, result in engine_results.items():
            if not result:
                continue
            canonical = result.get("canonical_degree")
            status = result.get("status")
            confidence = result.get("confidence", 0.0)
            if canonical and status != "unresolved":
                votes[canonical] += norm_weights.get(engine_name, 0.0) * confidence
                vote_count[canonical] += 1

        audit = {
            "cleaned": cleaned,
            "engines": engine_detail,
            "votes": {k: round(v, 4) for k, v in votes.items()},
            "active_weights": {k: round(v, 4) for k, v in norm_weights.items()},
        }

        if not votes:
            return {
                "hit": False,
                "result": None,
                "canonical_field": canonical_field,
                "audit": audit,
            }

        winner = max(votes, key=votes.get)
        confidence = votes[winner]
        agree_count = vote_count[winner]
        engines_polled = len(engine_results)
        if engines_polled > 1 and agree_count >= 2:
            confidence = min(1.0, confidence + 0.05)

        if confidence >= 0.82:
            status = "fuzzy_matched"
        elif confidence >= 0.60:
            status = "review_needed"
        else:
            status = "unresolved"

        alternatives = [
            (canonical, round(score, 4))
            for canonical, score in sorted(votes.items(), key=lambda item: -item[1])
            if canonical != winner
        ][:3]

        result = {
            "input": raw_string,
            "layer_used": "L2_Unified",
            "canonical_degree": winner if status != "unresolved" else None,
            "canonical_field": canonical_field,
            "confidence": round(confidence, 4),
            "status": status,
            "fuzzy_score": round(confidence * 100, 1),
            "alternatives": alternatives,
            "engine": ENGINE_ID,
            "mode": self.mode,
            "resolution_strategy": "fuzzy_consensus",
            "consensus_votes": agree_count,
            "engines_polled": engines_polled,
        }

        return {
            "hit": status != "unresolved",
            "result": result,
            "canonical_field": canonical_field,
            "audit": audit,
        }

    def _run_heuristic(self, raw_string: str, fallback_field: str | None) -> dict:
        if self._l3 is None:
            return {
                "hit": False,
                "result": None,
                "audit": {"enabled": False, "fired": False},
            }

        t0 = time.perf_counter()
        analyzed = self._l3.analyze(raw_string)
        ms = (time.perf_counter() - t0) * 1000

        audit = {
            "enabled": True,
            "fired": analyzed is not None,
            "strategy": analyzed.get("strategy") if analyzed else None,
            "latency_ms": round(ms, 3),
        }

        if not analyzed:
            return {"hit": False, "result": None, "audit": audit}

        result = {
            "input": raw_string,
            "layer_used": "L2_Unified",
            "canonical_degree": analyzed.get("canonical_degree"),
            "canonical_field": analyzed.get("field_mention") or fallback_field,
            "confidence": analyzed.get("confidence", 0.0),
            "status": "review_needed",
            "fuzzy_score": round(analyzed.get("confidence", 0.0) * 100, 1),
            "alternatives": [],
            "engine": ENGINE_ID,
            "mode": self.mode,
            "resolution_strategy": "heuristic_extraction",
            "l3_strategy": analyzed.get("strategy"),
            "extracted_mention": analyzed.get("extracted_mention"),
        }
        return {"hit": True, "result": result, "audit": audit}

    @staticmethod
    def _choose_result(fuzzy: dict, heuristic: dict) -> tuple[dict | None, str]:
        fuzzy_result = fuzzy.get("result")
        heuristic_result = heuristic.get("result")

        if fuzzy_result and fuzzy_result.get("status") == "fuzzy_matched":
            return fuzzy_result, "fuzzy_auto_accept"
        if fuzzy_result and not heuristic_result:
            return fuzzy_result, "fuzzy_only"
        if heuristic_result and not fuzzy_result:
            return heuristic_result, "heuristic_only"
        if fuzzy_result and heuristic_result:
            fuzzy_conf = fuzzy_result.get("confidence", 0.0)
            heuristic_conf = heuristic_result.get("confidence", 0.0)
            if heuristic_conf > fuzzy_conf or not fuzzy_result.get("canonical_degree"):
                return heuristic_result, "heuristic_higher_confidence"
            return fuzzy_result, "fuzzy_higher_confidence"
        return None, "unresolved"

    def resolve_after_l1(self, raw_string: str, canonical_field: str | None = None) -> dict:
        fuzzy = self._run_fuzzy(raw_string)
        fallback_field = canonical_field or fuzzy.get("canonical_field")

        should_run_heuristic = (
            not fuzzy.get("hit")
            or (fuzzy.get("result") or {}).get("status") == "review_needed"
        )
        heuristic = (
            self._run_heuristic(raw_string, fallback_field)
            if should_run_heuristic
            else {"hit": False, "result": None, "audit": {"enabled": self._l3 is not None, "skipped": True}}
        )

        chosen, decision = self._choose_result(fuzzy, heuristic)
        audit = {
            "fuzzy": fuzzy.get("audit", {}),
            "heuristic": heuristic.get("audit", {}),
            "decision": decision,
        }

        if chosen is None:
            return {
                "input": raw_string,
                "layer_used": "unresolved",
                "canonical_degree": None,
                "canonical_field": fallback_field,
                "confidence": 0.0,
                "status": "unresolved",
                "fuzzy_score": 0,
                "alternatives": [],
                "engine": ENGINE_ID,
                "mode": self.mode,
                "resolution_strategy": "unresolved",
                "audit": audit,
            }

        chosen = dict(chosen)
        chosen["canonical_field"] = chosen.get("canonical_field") or fallback_field
        chosen["mode"] = self.mode
        chosen["audit"] = audit
        return chosen

    def normalize(self, raw_string: str) -> dict:
        rf = self._rf_engine()
        cleaned, extracted_field = rf.clean(raw_string)
        canonical_field = rf._normalize_field(extracted_field)
        l1 = rf.layer1_lookup(cleaned)
        if l1:
            return {
                **l1,
                "input": raw_string,
                "canonical_field": canonical_field,
                "engine": ENGINE_ID,
                "mode": self.mode,
                "resolution_strategy": "exact_lookup",
            }
        return self.resolve_after_l1(raw_string, canonical_field)

    def batch_normalize(self, inputs: list[str]) -> list[dict]:
        return [self.normalize(item) for item in inputs]
