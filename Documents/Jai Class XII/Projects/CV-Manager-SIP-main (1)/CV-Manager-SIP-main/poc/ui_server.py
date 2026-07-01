"""
CV Manager - Local Web UI
=========================
Dependency-light dashboard for the complete qualification normalisation system.

Run:
    python poc/ui_server.py

Then open:
    http://127.0.0.1:8765
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import sys
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA_DIR = os.path.join(ROOT, "data")

sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)


ENGINE_SPECS: dict[str, dict[str, str]] = {
    "orchestrator": {
        "label": "Full Orchestrator",
        "type": "Full system",
        "detail": "L1 exact lookup plus L2_Unified advanced resolution.",
    },
    "unified": {
        "label": "L2+L3 Unified",
        "type": "Advanced layer",
        "detail": "Fuzzy consensus with heuristic extraction in one layer.",
    },
    "l1": {
        "label": "L1 Exact",
        "type": "Lookup",
        "detail": "Dictionary exact match only.",
    },
    "rapidfuzz": {
        "label": "RapidFuzz",
        "type": "Fuzzy",
        "detail": "Levenshtein/token fuzzy matching.",
    },
    "tfidf": {
        "label": "TF-IDF",
        "type": "Fuzzy",
        "detail": "Character n-gram cosine similarity.",
    },
    "embeddings": {
        "label": "Embeddings",
        "type": "Semantic",
        "detail": "Sentence-transformer semantic similarity.",
    },
    "l3": {
        "label": "L3 Heuristic",
        "type": "Heuristic",
        "detail": "Pure-Python conversational text extraction.",
    },
}


DATASET_SPECS: list[dict[str, str]] = [
    {
        "key": "layer1",
        "label": "Layer 1 exact lookup",
        "kind": "Training",
        "path": os.path.join(DATA_DIR, "layer1_exact_lookup_training.csv"),
    },
    {
        "key": "layer2",
        "label": "Layer 2 fuzzy inputs",
        "kind": "Training",
        "path": os.path.join(DATA_DIR, "layer2_fuzzy_training.csv"),
    },
    {
        "key": "layer3",
        "label": "Layer 3 unstructured text",
        "kind": "Training",
        "path": os.path.join(DATA_DIR, "layer3_unstructured_training.csv"),
    },
    {
        "key": "india_usa",
        "label": "India + USA degrees",
        "kind": "Degree only",
        "path": os.path.join(DATA_DIR, "indian_usa_degrees_training.csv"),
    },
    {
        "key": "india_uk",
        "label": "India + UK degrees",
        "kind": "Degree only",
        "path": os.path.join(DATA_DIR, "indian_uk_degrees_training.csv"),
    },
    {
        "key": "india_world",
        "label": "India + world degrees",
        "kind": "Degree only",
        "path": os.path.join(DATA_DIR, "indian_world_degrees_training.csv"),
    },
    {
        "key": "catalog",
        "label": "Canonical degree catalog",
        "kind": "Reference",
        "path": os.path.join(DATA_DIR, "degree_only_canonical_catalog.csv"),
    },
]


class L1OnlyAdapter:
    def __init__(self, data_dir: str):
        from normalizer_rapidfuzz import Normalizer as RapidFuzz

        self._rf = RapidFuzz(data_dir)

    def normalize(self, raw_string: str) -> dict[str, Any]:
        cleaned, extracted_field = self._rf.clean(raw_string)
        canonical_field = self._rf._normalize_field(extracted_field)
        t0 = time.perf_counter()
        hit = self._rf.layer1_lookup(cleaned)
        elapsed = (time.perf_counter() - t0) * 1000
        if hit:
            return {
                **hit,
                "input": raw_string,
                "canonical_field": canonical_field,
                "engine": "L1_Only",
                "mode": "exact",
                "resolution_strategy": "exact_lookup",
                "audit": {
                    "L1": {
                        "cleaned": cleaned,
                        "hit": True,
                        "latency_ms": round(elapsed, 3),
                    }
                },
            }
        return {
            "input": raw_string,
            "canonical_degree": None,
            "canonical_field": canonical_field,
            "confidence": 0.0,
            "status": "unresolved",
            "layer_used": "unresolved",
            "fuzzy_score": 0,
            "alternatives": [],
            "engine": "L1_Only",
            "mode": "exact",
            "resolution_strategy": "unresolved",
            "audit": {
                "L1": {
                    "cleaned": cleaned,
                    "hit": False,
                    "latency_ms": round(elapsed, 3),
                }
            },
        }

    def batch_normalize(self, inputs: list[str]) -> list[dict[str, Any]]:
        return [self.normalize(item) for item in inputs]


_ENGINE_CACHE: dict[str, Any] = {}
_ENGINE_ERRORS: dict[str, str] = {}


def _dependency_snapshot() -> dict[str, bool]:
    return {
        "rapidfuzz": importlib.util.find_spec("rapidfuzz") is not None,
        "sklearn": importlib.util.find_spec("sklearn") is not None,
        "numpy": importlib.util.find_spec("numpy") is not None,
        "sentence_transformers": importlib.util.find_spec("sentence_transformers") is not None,
        "torch": importlib.util.find_spec("torch") is not None,
    }


def _engine_dependency_hint(key: str, deps: dict[str, bool]) -> str | None:
    missing: list[str] = []
    if key in {"orchestrator", "unified", "l1", "rapidfuzz"}:
        if not deps["rapidfuzz"]:
            missing.append("rapidfuzz")
    if key == "tfidf":
        if not deps["sklearn"]:
            missing.append("scikit-learn")
        if not deps["numpy"]:
            missing.append("numpy")
    if key == "embeddings":
        if not deps["numpy"]:
            missing.append("numpy")
        if not deps["sentence_transformers"]:
            missing.append("sentence-transformers")
        if not deps["torch"]:
            missing.append("torch")
    if missing:
        return "Missing: " + ", ".join(missing)
    return None


def _build_engine(key: str) -> Any:
    if key == "orchestrator":
        from engine_orchestrator import CVNormalizationOrchestrator

        return CVNormalizationOrchestrator(DATA_DIR, mode="full")
    if key == "unified":
        from engine_l2_l3_unified import UnifiedAdvancedLayer

        return UnifiedAdvancedLayer(DATA_DIR, mode="full")
    if key == "l1":
        return L1OnlyAdapter(DATA_DIR)
    if key == "rapidfuzz":
        from normalizer_rapidfuzz import Normalizer

        return Normalizer(DATA_DIR)
    if key == "tfidf":
        from normalizer_tfidf import NormalizerTFIDF

        return NormalizerTFIDF(DATA_DIR)
    if key == "embeddings":
        from normalizer_embeddings import NormalizerEmbeddings

        return NormalizerEmbeddings(DATA_DIR)
    if key == "l3":
        from engine_l3 import L3HeuristicEngine

        return L3HeuristicEngine()
    raise KeyError(f"Unknown engine: {key}")


def _get_engine(key: str) -> Any:
    if key in _ENGINE_CACHE:
        return _ENGINE_CACHE[key]
    if key in _ENGINE_ERRORS:
        raise RuntimeError(_ENGINE_ERRORS[key])
    try:
        engine = _build_engine(key)
    except Exception as exc:
        _ENGINE_ERRORS[key] = str(exc)
        raise
    _ENGINE_CACHE[key] = engine
    return engine


def _safe_result(result: dict[str, Any], elapsed_ms: float) -> dict[str, Any]:
    cleaned = dict(result)
    cleaned["latency_ms"] = round(elapsed_ms, 2)
    return cleaned


def normalize_with_engine(engine_key: str, raw: str) -> dict[str, Any]:
    raw = (raw or "").strip()
    if not raw:
        raise ValueError("Input text is required.")
    engine = _get_engine(engine_key)
    t0 = time.perf_counter()
    result = engine.normalize(raw)
    elapsed = (time.perf_counter() - t0) * 1000
    return _safe_result(result, elapsed)


def compare_engines(raw: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, spec in ENGINE_SPECS.items():
        try:
            result = normalize_with_engine(key, raw)
            rows.append({"key": key, "label": spec["label"], "ok": True, "result": result})
        except Exception as exc:
            rows.append({"key": key, "label": spec["label"], "ok": False, "error": str(exc)})
    return rows


def _row_preview(row: dict[str, str]) -> dict[str, str]:
    preferred = [
        "sample_id",
        "raw_input",
        "raw_text",
        "canonical_degree",
        "canonical_name",
        "canonical_field",
        "degree_level",
        "noise_type",
        "difficulty",
        "scope",
    ]
    preview: dict[str, str] = {}
    for key in preferred:
        if key in row and row[key]:
            preview[key] = row[key]
    if preview:
        return preview
    for key, value in list(row.items())[:6]:
        preview[key] = value
    return preview


def dataset_overview() -> list[dict[str, Any]]:
    overviews: list[dict[str, Any]] = []
    for spec in DATASET_SPECS:
        path = spec["path"]
        item: dict[str, Any] = {
            "key": spec["key"],
            "label": spec["label"],
            "kind": spec["kind"],
            "file": os.path.relpath(path, ROOT),
            "exists": os.path.exists(path),
            "rows": 0,
            "columns": [],
            "samples": [],
        }
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8", newline="") as handle:
                    reader = csv.DictReader(handle)
                    item["columns"] = reader.fieldnames or []
                    for index, row in enumerate(reader):
                        if index < 4:
                            item["samples"].append(_row_preview(row))
                        item["rows"] += 1
            except Exception as exc:
                item["error"] = str(exc)
        overviews.append(item)
    return overviews


def engine_status() -> list[dict[str, Any]]:
    deps = _dependency_snapshot()
    statuses: list[dict[str, Any]] = []
    for key, spec in ENGINE_SPECS.items():
        hint = _engine_dependency_hint(key, deps)
        error = _ENGINE_ERRORS.get(key)
        loaded = key in _ENGINE_CACHE
        available = hint is None and error is None
        statuses.append(
            {
                "key": key,
                "label": spec["label"],
                "type": spec["type"],
                "detail": spec["detail"],
                "loaded": loaded,
                "available": available,
                "message": error or hint or ("Loaded" if loaded else "Ready"),
            }
        )
    return statuses


HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>CV Manager Qualification UI</title>
  <style>
    :root {
      --bg: #f6f7f4;
      --panel: #ffffff;
      --ink: #222522;
      --muted: #667069;
      --line: #d8ddd7;
      --green: #0f7b62;
      --green-dark: #09533f;
      --amber: #a66d05;
      --red: #b23a37;
      --blue: #2f5d8c;
      --soft-green: #e8f3ef;
      --soft-amber: #fff4dc;
      --soft-red: #fae6e5;
      --soft-blue: #e7eef6;
      --shadow: 0 16px 36px rgba(31, 38, 35, 0.08);
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      color: var(--ink);
      background: var(--bg);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }
    button, input, select, textarea {
      font: inherit;
      letter-spacing: 0;
    }
    .shell {
      min-height: 100vh;
      display: grid;
      grid-template-columns: 260px minmax(0, 1fr);
    }
    aside {
      border-right: 1px solid var(--line);
      background: #fbfcfa;
      padding: 22px 18px;
      position: sticky;
      top: 0;
      height: 100vh;
      overflow: auto;
    }
    main {
      padding: 24px;
      min-width: 0;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 22px;
    }
    .mark {
      width: 36px;
      height: 36px;
      display: grid;
      place-items: center;
      border-radius: 8px;
      background: var(--green);
      color: #fff;
      font-weight: 800;
    }
    h1 {
      font-size: 18px;
      line-height: 1.2;
      margin: 0;
    }
    .sub {
      color: var(--muted);
      font-size: 12px;
      margin-top: 3px;
    }
    .engine-list {
      display: grid;
      gap: 8px;
    }
    .engine-btn {
      width: 100%;
      min-height: 54px;
      border: 1px solid var(--line);
      background: #fff;
      color: var(--ink);
      border-radius: 8px;
      padding: 9px 10px;
      text-align: left;
      cursor: pointer;
    }
    .engine-btn.active {
      border-color: var(--green);
      background: var(--soft-green);
      box-shadow: inset 3px 0 0 var(--green);
    }
    .engine-btn.unavailable {
      opacity: 0.72;
    }
    .engine-title {
      display: flex;
      justify-content: space-between;
      gap: 8px;
      font-weight: 700;
      font-size: 13px;
    }
    .engine-meta {
      color: var(--muted);
      margin-top: 4px;
      font-size: 11px;
      line-height: 1.25;
    }
    .dot {
      display: inline-block;
      width: 9px;
      height: 9px;
      border-radius: 99px;
      background: var(--green);
      flex: 0 0 auto;
      margin-top: 4px;
    }
    .dot.warn { background: var(--amber); }
    .topbar {
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 18px;
    }
    .topbar h2 {
      font-size: 24px;
      margin: 0 0 4px;
    }
    .toolbar {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }
    .tabs {
      display: flex;
      gap: 6px;
      padding: 5px;
      background: #e9ede7;
      border-radius: 8px;
    }
    .tab-btn {
      border: 0;
      background: transparent;
      border-radius: 6px;
      min-height: 34px;
      padding: 0 12px;
      cursor: pointer;
      color: #3e4641;
    }
    .tab-btn.active {
      background: #fff;
      color: var(--ink);
      box-shadow: 0 1px 2px rgba(0,0,0,0.08);
    }
    .grid {
      display: grid;
      grid-template-columns: minmax(320px, 0.95fr) minmax(360px, 1.05fr);
      gap: 18px;
      align-items: start;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: var(--shadow);
      padding: 18px;
      min-width: 0;
    }
    .panel h3 {
      font-size: 15px;
      margin: 0 0 14px;
    }
    .field {
      display: grid;
      gap: 7px;
      margin-bottom: 12px;
    }
    label {
      font-size: 12px;
      font-weight: 700;
      color: #3e4641;
    }
    textarea, input, select {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      color: var(--ink);
      padding: 11px 12px;
      outline: none;
    }
    textarea {
      min-height: 132px;
      resize: vertical;
      line-height: 1.45;
    }
    textarea:focus, input:focus, select:focus {
      border-color: var(--green);
      box-shadow: 0 0 0 3px rgba(15, 123, 98, 0.12);
    }
    .actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
    }
    .btn {
      min-height: 38px;
      border: 1px solid transparent;
      border-radius: 8px;
      padding: 0 14px;
      cursor: pointer;
      font-weight: 700;
      background: var(--green);
      color: #fff;
    }
    .btn:hover { background: var(--green-dark); }
    .btn.secondary {
      background: #fff;
      color: var(--ink);
      border-color: var(--line);
    }
    .btn.secondary:hover { background: #f2f5f1; }
    .result-head {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 12px;
      align-items: start;
      margin-bottom: 12px;
    }
    .canonical {
      font-size: 23px;
      font-weight: 800;
      line-height: 1.15;
      overflow-wrap: anywhere;
    }
    .status {
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      border-radius: 999px;
      padding: 0 10px;
      font-size: 12px;
      font-weight: 800;
      background: var(--soft-blue);
      color: var(--blue);
      white-space: nowrap;
    }
    .status.resolved, .status.fuzzy_matched { background: var(--soft-green); color: var(--green-dark); }
    .status.review_needed { background: var(--soft-amber); color: var(--amber); }
    .status.unresolved, .status.error { background: var(--soft-red); color: var(--red); }
    .metric-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
      margin-top: 12px;
    }
    .metric {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      min-height: 64px;
      background: #fbfcfa;
    }
    .metric b {
      display: block;
      font-size: 11px;
      color: var(--muted);
      text-transform: uppercase;
      margin-bottom: 4px;
    }
    .metric span {
      display: block;
      font-weight: 750;
      overflow-wrap: anywhere;
    }
    .confidence {
      height: 8px;
      width: 100%;
      background: #e4e8e2;
      border-radius: 99px;
      overflow: hidden;
      margin-top: 10px;
    }
    .confidence > div {
      height: 100%;
      background: var(--green);
      width: 0%;
    }
    details {
      margin-top: 12px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px;
      background: #fbfcfa;
    }
    summary {
      cursor: pointer;
      font-weight: 700;
      font-size: 13px;
    }
    pre {
      overflow: auto;
      max-height: 280px;
      margin: 10px 0 0;
      font-size: 12px;
      line-height: 1.45;
      white-space: pre-wrap;
    }
    .table-wrap {
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 760px;
    }
    th, td {
      border-bottom: 1px solid var(--line);
      padding: 10px;
      text-align: left;
      vertical-align: top;
      font-size: 13px;
    }
    th {
      font-size: 11px;
      text-transform: uppercase;
      color: var(--muted);
      background: #f6f8f5;
    }
    tr:last-child td { border-bottom: 0; }
    .dataset-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
    }
    .dataset-card {
      border: 1px solid var(--line);
      background: #fff;
      border-radius: 8px;
      padding: 14px;
      min-height: 164px;
    }
    .dataset-card h4 {
      margin: 0 0 8px;
      font-size: 14px;
    }
    .pill-row {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 10px;
    }
    .pill {
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 4px 8px;
      font-size: 11px;
      color: var(--muted);
      background: #fbfcfa;
      white-space: nowrap;
    }
    .notice {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fff;
      padding: 12px;
      color: var(--muted);
      font-size: 13px;
    }
    .hidden { display: none !important; }
    .muted { color: var(--muted); }
    .error-text { color: var(--red); font-weight: 700; }
    @media (max-width: 980px) {
      .shell { grid-template-columns: 1fr; }
      aside { position: static; height: auto; }
      .grid { grid-template-columns: 1fr; }
      .dataset-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    @media (max-width: 640px) {
      main { padding: 16px; }
      aside { padding: 16px; }
      .topbar { align-items: stretch; flex-direction: column; }
      .tabs { overflow-x: auto; }
      .metric-grid, .dataset-grid { grid-template-columns: 1fr; }
      .result-head { grid-template-columns: 1fr; }
      .canonical { font-size: 20px; }
    }
  </style>
</head>
<body>
  <div class="shell">
    <aside>
      <div class="brand">
        <div class="mark">CV</div>
        <div>
          <h1>Qualification UI</h1>
          <div class="sub">v3.6.5 local system</div>
        </div>
      </div>
      <div class="engine-list" id="engineList"></div>
    </aside>

    <main>
      <div class="topbar">
        <div>
          <h2 id="activeTitle">Full Orchestrator</h2>
          <div class="sub" id="activeDetail">L1 exact lookup plus L2_Unified advanced resolution.</div>
        </div>
        <div class="tabs" role="tablist">
          <button class="tab-btn active" data-tab="single">Single</button>
          <button class="tab-btn" data-tab="batch">Batch</button>
          <button class="tab-btn" data-tab="compare">Compare</button>
          <button class="tab-btn" data-tab="data">Data</button>
        </div>
      </div>

      <section class="tab-panel" id="tab-single">
        <div class="grid">
          <div class="panel">
            <h3>Normalize one input</h3>
            <div class="field">
              <label for="singleInput">Education text</label>
              <textarea id="singleInput">B.Tech in Computer Science from IIT Delhi</textarea>
            </div>
            <div class="actions">
              <button class="btn" id="runSingle">Normalize</button>
              <button class="btn secondary" id="sampleSingle">Use sample</button>
              <span class="muted" id="singleLatency"></span>
            </div>
          </div>
          <div class="panel">
            <h3>Result</h3>
            <div id="singleResult" class="notice">Run a normalization request.</div>
          </div>
        </div>
      </section>

      <section class="tab-panel hidden" id="tab-batch">
        <div class="panel">
          <h3>Batch normalize</h3>
          <div class="field">
            <label for="batchInput">One input per line</label>
            <textarea id="batchInput">B.Tech
Bachelor of Business Admin
I completed my Masters in Data Science from IIT Delhi
Some random text</textarea>
          </div>
          <div class="actions">
            <button class="btn" id="runBatch">Run batch</button>
            <span class="muted" id="batchLatency"></span>
          </div>
        </div>
        <div class="panel" style="margin-top: 18px;">
          <h3>Batch results</h3>
          <div id="batchResult" class="notice">Batch output will appear here.</div>
        </div>
      </section>

      <section class="tab-panel hidden" id="tab-compare">
        <div class="panel">
          <h3>Compare every engine type</h3>
          <div class="field">
            <label for="compareInput">Education text</label>
            <textarea id="compareInput">Bachellor of Technolgy in CSE</textarea>
          </div>
          <div class="actions">
            <button class="btn" id="runCompare">Compare</button>
            <span class="muted" id="compareLatency"></span>
          </div>
        </div>
        <div class="panel" style="margin-top: 18px;">
          <h3>Engine comparison</h3>
          <div id="compareResult" class="notice">Comparison output will appear here.</div>
        </div>
      </section>

      <section class="tab-panel hidden" id="tab-data">
        <div class="panel">
          <h3>Dataset overview by type</h3>
          <div id="datasetResult" class="notice">Loading datasets...</div>
        </div>
      </section>
    </main>
  </div>

  <script>
    const state = {
      activeEngine: "orchestrator",
      engines: [],
      samples: [
        "B.Tech",
        "Bachellor of Technolgy in CSE",
        "Bachelor of Business Admin",
        "I completed my Masters in Data Science from IIT Delhi",
        "Have a diploma in Mechanical Engineering from a polytechnic",
        "Some random text"
      ],
      sampleIndex: 0
    };

    const $ = (id) => document.getElementById(id);

    function escapeHtml(value) {
      return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
      }[ch]));
    }

    function statusClass(status) {
      return "status " + String(status || "unresolved").replace(/\s+/g, "_");
    }

    async function api(path, options = {}) {
      const response = await fetch(path, {
        headers: { "Content-Type": "application/json" },
        ...options
      });
      const data = await response.json();
      if (!response.ok || data.ok === false) {
        throw new Error(data.error || response.statusText);
      }
      return data;
    }

    function renderEngines() {
      const list = $("engineList");
      list.innerHTML = state.engines.map((engine) => {
        const active = engine.key === state.activeEngine ? " active" : "";
        const unavailable = engine.available ? "" : " unavailable";
        const dot = engine.available ? "dot" : "dot warn";
        return `
          <button class="engine-btn${active}${unavailable}" data-engine="${escapeHtml(engine.key)}">
            <div class="engine-title">
              <span>${escapeHtml(engine.label)}</span>
              <span class="${dot}"></span>
            </div>
            <div class="engine-meta">${escapeHtml(engine.type)} - ${escapeHtml(engine.message)}</div>
          </button>
        `;
      }).join("");
      list.querySelectorAll("button").forEach((btn) => {
        btn.addEventListener("click", () => {
          const key = btn.dataset.engine;
          state.activeEngine = key;
          const selected = state.engines.find((item) => item.key === key);
          $("activeTitle").textContent = selected?.label || key;
          $("activeDetail").textContent = selected?.detail || "";
          renderEngines();
        });
      });
    }

    function renderResult(result) {
      const confidence = Number(result.confidence || 0);
      const pct = Math.max(0, Math.min(100, confidence * 100));
      const canonical = result.canonical_degree || "No canonical degree";
      const field = result.canonical_field || "-";
      const strategy = result.resolution_strategy || result.l3_strategy || "-";
      return `
        <div class="result-head">
          <div class="canonical">${escapeHtml(canonical)}</div>
          <span class="${statusClass(result.status)}">${escapeHtml(result.status || "unresolved")}</span>
        </div>
        <div class="confidence"><div style="width:${pct}%"></div></div>
        <div class="metric-grid">
          <div class="metric"><b>Field</b><span>${escapeHtml(field)}</span></div>
          <div class="metric"><b>Confidence</b><span>${confidence.toFixed(4)}</span></div>
          <div class="metric"><b>Layer</b><span>${escapeHtml(result.layer_used || "-")}</span></div>
          <div class="metric"><b>Strategy</b><span>${escapeHtml(strategy)}</span></div>
          <div class="metric"><b>Engine</b><span>${escapeHtml(result.engine || "-")}</span></div>
          <div class="metric"><b>Latency</b><span>${escapeHtml(result.latency_ms ?? "-")} ms</span></div>
        </div>
        <details>
          <summary>Full result</summary>
          <pre>${escapeHtml(JSON.stringify(result, null, 2))}</pre>
        </details>
      `;
    }

    function renderRows(rows) {
      if (!rows.length) return '<div class="notice">No rows to show.</div>';
      return `
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Input</th>
                <th>Canonical</th>
                <th>Field</th>
                <th>Status</th>
                <th>Layer</th>
                <th>Confidence</th>
                <th>Strategy</th>
              </tr>
            </thead>
            <tbody>
              ${rows.map((result) => `
                <tr>
                  <td>${escapeHtml(result.input)}</td>
                  <td>${escapeHtml(result.canonical_degree || "-")}</td>
                  <td>${escapeHtml(result.canonical_field || "-")}</td>
                  <td><span class="${statusClass(result.status)}">${escapeHtml(result.status || "-")}</span></td>
                  <td>${escapeHtml(result.layer_used || "-")}</td>
                  <td>${Number(result.confidence || 0).toFixed(3)}</td>
                  <td>${escapeHtml(result.resolution_strategy || result.l3_strategy || "-")}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>
        </div>
      `;
    }

    function renderCompare(rows) {
      return `
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Engine</th>
                <th>Canonical</th>
                <th>Field</th>
                <th>Status</th>
                <th>Layer</th>
                <th>Confidence</th>
                <th>Message</th>
              </tr>
            </thead>
            <tbody>
              ${rows.map((row) => {
                if (!row.ok) {
                  return `
                    <tr>
                      <td>${escapeHtml(row.label)}</td>
                      <td colspan="5">-</td>
                      <td class="error-text">${escapeHtml(row.error)}</td>
                    </tr>
                  `;
                }
                const result = row.result;
                return `
                  <tr>
                    <td>${escapeHtml(row.label)}</td>
                    <td>${escapeHtml(result.canonical_degree || "-")}</td>
                    <td>${escapeHtml(result.canonical_field || "-")}</td>
                    <td><span class="${statusClass(result.status)}">${escapeHtml(result.status || "-")}</span></td>
                    <td>${escapeHtml(result.layer_used || "-")}</td>
                    <td>${Number(result.confidence || 0).toFixed(3)}</td>
                    <td>${escapeHtml(result.resolution_strategy || result.l3_strategy || `${result.latency_ms} ms`)}</td>
                  </tr>
                `;
              }).join("")}
            </tbody>
          </table>
        </div>
      `;
    }

    function renderDatasets(datasets) {
      return `
        <div class="dataset-grid">
          ${datasets.map((dataset) => `
            <div class="dataset-card">
              <h4>${escapeHtml(dataset.label)}</h4>
              <div class="muted">${escapeHtml(dataset.kind)} - ${escapeHtml(dataset.file)}</div>
              <div class="metric-grid" style="grid-template-columns: 1fr 1fr; margin-top: 10px;">
                <div class="metric"><b>Rows</b><span>${dataset.rows.toLocaleString()}</span></div>
                <div class="metric"><b>Columns</b><span>${dataset.columns.length}</span></div>
              </div>
              <div class="pill-row">
                ${dataset.columns.slice(0, 6).map((column) => `<span class="pill">${escapeHtml(column)}</span>`).join("")}
              </div>
            </div>
          `).join("")}
        </div>
      `;
    }

    async function loadHealth() {
      const data = await api("/api/health");
      state.engines = data.engines;
      renderEngines();
      const selected = state.engines.find((item) => item.key === state.activeEngine);
      $("activeTitle").textContent = selected?.label || "Full Orchestrator";
      $("activeDetail").textContent = selected?.detail || "";
    }

    async function loadDatasets() {
      try {
        const data = await api("/api/datasets");
        $("datasetResult").innerHTML = renderDatasets(data.datasets);
      } catch (error) {
        $("datasetResult").innerHTML = `<span class="error-text">${escapeHtml(error.message)}</span>`;
      }
    }

    document.querySelectorAll(".tab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".tab-btn").forEach((item) => item.classList.remove("active"));
        document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.add("hidden"));
        btn.classList.add("active");
        $("tab-" + btn.dataset.tab).classList.remove("hidden");
        if (btn.dataset.tab === "data") loadDatasets();
      });
    });

    $("runSingle").addEventListener("click", async () => {
      $("singleResult").innerHTML = '<div class="notice">Running...</div>';
      try {
        const t0 = performance.now();
        const data = await api("/api/normalize", {
          method: "POST",
          body: JSON.stringify({ engine: state.activeEngine, text: $("singleInput").value })
        });
        $("singleLatency").textContent = `${(performance.now() - t0).toFixed(0)} ms round trip`;
        $("singleResult").innerHTML = renderResult(data.result);
        await loadHealth();
      } catch (error) {
        $("singleResult").innerHTML = `<span class="error-text">${escapeHtml(error.message)}</span>`;
      }
    });

    $("sampleSingle").addEventListener("click", () => {
      state.sampleIndex = (state.sampleIndex + 1) % state.samples.length;
      $("singleInput").value = state.samples[state.sampleIndex];
    });

    $("runBatch").addEventListener("click", async () => {
      $("batchResult").innerHTML = '<div class="notice">Running...</div>';
      try {
        const t0 = performance.now();
        const texts = $("batchInput").value.split(/\n+/).map((line) => line.trim()).filter(Boolean);
        const data = await api("/api/batch", {
          method: "POST",
          body: JSON.stringify({ engine: state.activeEngine, texts })
        });
        $("batchLatency").textContent = `${(performance.now() - t0).toFixed(0)} ms round trip`;
        $("batchResult").innerHTML = renderRows(data.results);
        await loadHealth();
      } catch (error) {
        $("batchResult").innerHTML = `<span class="error-text">${escapeHtml(error.message)}</span>`;
      }
    });

    $("runCompare").addEventListener("click", async () => {
      $("compareResult").innerHTML = '<div class="notice">Running...</div>';
      try {
        const t0 = performance.now();
        const data = await api("/api/compare", {
          method: "POST",
          body: JSON.stringify({ text: $("compareInput").value })
        });
        $("compareLatency").textContent = `${(performance.now() - t0).toFixed(0)} ms round trip`;
        $("compareResult").innerHTML = renderCompare(data.results);
        await loadHealth();
      } catch (error) {
        $("compareResult").innerHTML = `<span class="error-text">${escapeHtml(error.message)}</span>`;
      }
    });

    loadHealth()
      .then(loadDatasets)
      .catch((error) => {
        $("engineList").innerHTML = `<span class="error-text">${escapeHtml(error.message)}</span>`;
      });
  </script>
</body>
</html>
"""


class UIHandler(BaseHTTPRequestHandler):
    server_version = "CVManagerUI/1.0"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("[ui] " + fmt % args + "\n")

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or "0")
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        return json.loads(raw)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            self._send(HTTPStatus.OK, HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if parsed.path == "/api/health":
            self._json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "dependencies": _dependency_snapshot(),
                    "engines": engine_status(),
                    "data_dir": DATA_DIR,
                },
            )
            return
        if parsed.path == "/api/datasets":
            self._json(HTTPStatus.OK, {"ok": True, "datasets": dataset_overview()})
            return
        if parsed.path == "/api/sample":
            query = parse_qs(parsed.query)
            text = query.get("text", ["B.Tech in Computer Science"])[0]
            self._json(HTTPStatus.OK, {"ok": True, "text": text})
            return
        self._json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Route not found."})

    def do_POST(self) -> None:
        try:
            payload = self._read_json()
            parsed = urlparse(self.path)
            if parsed.path == "/api/normalize":
                engine_key = str(payload.get("engine") or "orchestrator")
                text = str(payload.get("text") or "")
                result = normalize_with_engine(engine_key, text)
                self._json(HTTPStatus.OK, {"ok": True, "result": result})
                return
            if parsed.path == "/api/batch":
                engine_key = str(payload.get("engine") or "orchestrator")
                texts = payload.get("texts") or []
                if not isinstance(texts, list):
                    raise ValueError("texts must be a list.")
                if len(texts) > 250:
                    raise ValueError("Batch limit is 250 lines.")
                results = [normalize_with_engine(engine_key, str(text)) for text in texts if str(text).strip()]
                self._json(HTTPStatus.OK, {"ok": True, "results": results})
                return
            if parsed.path == "/api/compare":
                text = str(payload.get("text") or "")
                if not text.strip():
                    raise ValueError("Input text is required.")
                self._json(HTTPStatus.OK, {"ok": True, "results": compare_engines(text)})
                return
            self._json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Route not found."})
        except Exception as exc:
            self._json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": str(exc)})


def main() -> None:
    parser = argparse.ArgumentParser(description="CV Manager local web UI")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8765, type=int)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), UIHandler)
    url = f"http://{args.host}:{args.port}"
    print(f"CV Manager UI running at {url}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
