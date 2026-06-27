# Platform Audit: CV Normalization Engine

> **Version:** 3.6.0 — 27 June 2026
> **Project:** Growth Grids × University of Southampton Delhi
> **Contributors:** Arnav (pipeline & integration) · Jai Gupta (dataset engineering) · Himanshi Kaushik & Keshav Singhal (F1 scoring)

---

## Overview

This document serves as the living audit log for the CV Normalization Engine. It tracks the current status of all system components, datasets, known issues, and dependency health across versions.

---

## System Architecture

### Master Orchestrator (`engine_orchestrator.py`)
- **Status:** ✅ Active
- **Description:** Controls the full L1 → L2 → L3 pipeline via a unified interface.
- **Modes:** `fast` (RapidFuzz only, ~1–5 ms) · `standard` (RapidFuzz + TF-IDF, ~2–6 ms) · `full` (all engines + L3, ~50–120 ms)
- **Audit Trails:** Per-layer timing, confidence scores, engine votes, and decision rationale are captured in every result dict.

### Layer 3: Heuristic NLP Engine (`engine_l3.py`)
- **Status:** ✅ Active
- **Description:** Pure-Python, zero-ML engine for processing unstructured and conversational text.
- **Strategy Cascade (priority order):**
  1. **S2 Shortcode Expansion** — 50+ hard-coded abbreviations (BCA, PGDM, LLB, 12th…) → canonical (conf: 0.80)
  2. **S1 Sentence Extraction** — Regex patterns pull degree mentions from natural language (conf: 0.60–0.72)
  3. **S3 Level Keyword Detection** — Maps keywords (bachelor, master, phd…) to degree-level group (conf: 0.50)
  4. **S4 Field-Only Inference** — Detects field-of-study when no degree level is identifiable (conf: 0.35)
- **Note:** All L3 results are flagged `review_needed` — expected behaviour.

### Layer 2 Combined: Consensus Voting Engine (`engine_l2_combined.py`)
- **Status:** ✅ Active
- **Description:** Executes multiple sub-engines in parallel and fuses outputs via weighted voting.
- **Sub-engines & Weights:** RapidFuzz (0.35) · TF-IDF (0.30) · Dense Embeddings (0.35)
- **Consensus Bonus:** +0.05 confidence when ≥2 engines agree on the same canonical (capped at 1.0).
- **Degradation:** If `sentence-transformers` is absent, Embeddings is skipped and weights re-normalise automatically.
- **Bug Fixed (v3.5.0):** `_combined_score()` now accepts `**kwargs` — resolves `score_cutoff` crash that silently zeroed all L2 scores.

### Layer 2 Sub-Engines

| Engine | File | Latency | Dependencies |
|--------|------|---------|--------------|
| **B-1 RapidFuzz** | `normalizer_rapidfuzz.py` | ~1–5 ms | `rapidfuzz` |
| **B-2 TF-IDF** | `normalizer_tfidf.py` | <1 ms | `scikit-learn`, `numpy` |
| **B-3 Embeddings** | `normalizer_embeddings.py` | ~50–100 ms | `torch`, `sentence-transformers` |

### Layer 1: Exact Dictionary Lookup
- **Status:** ✅ Active
- **Dictionary Size:** 7,593 alias entries (as of v3.5.0, including medical degrees)
- **Coverage:** 22 canonical degrees × 68+ canonical fields, covering UG Engineering, UG Science, UG Medicine, PG Engineering, PG Other, Doctorate, Diploma, and School levels.

---

## Dataset Audit (v3.5.0)

### Existing Data — `data/`

| File | Status | Notes |
|------|--------|-------|
| `degree_aliases.csv` | ✅ Current | 7,593 entries — regenerated with medical degrees |
| `degree_dictionary.json` | ✅ Current | 22 canonical degrees including MBBS, BDS, BPHARM |
| `field_of_study_aliases.csv` | ✅ Current | 308 aliases, 68 canonical fields |
| `degree_field_map.csv` | ✅ Current | 186 UGC-compliant pairs |
| `education_seed.sql` | ✅ Current | 5-table schema + seeds |
| `education_seed.json` | ✅ Current | Regenerated v3.5.0 |

### New Datasets — `data/` (Jai Gupta)

| File | Rows | Layer | Status |
|------|-----:|-------|--------|
| `layer1_exact_lookup_training.csv` | 6,976 | L1 | ✅ Integrated |
| `layer2_fuzzy_training.csv` | 15,233 | L2 | ✅ Integrated |
| `layer3_unstructured_training.csv` | 1,124 | L3 | ✅ Integrated |
| `degree_only_canonical_catalog.csv` | 141 entries | Reference | ✅ Integrated |
| `indian_usa_degrees_training.csv` | 9,448 | Multi-national | ✅ Integrated |
| `indian_uk_degrees_training.csv` | 9,240 | Multi-national | ✅ Integrated |
| `indian_world_degrees_training.csv` | 17,913 | Multi-national | ✅ Integrated |
| `degree_only_manifest.json` | — | Manifest | ✅ Integrated |

### Expanded SQL Seeds — `education_reference_expanded_sql_files/` (Jai Gupta)

| Scope | Canonical Fields | Canonical Degrees | Degree-Field Combinations |
|-------|---:|---:|---:|
| USA | 218 | 84 | 18,312 |
| UK | 218 | 61 | 13,298 |
| WORLD | 348 | 179 | 62,292 |

**Sources:** NCES CIP 2020 · IPEDS/NCES · HESA HECoS · QAA/UCAS · UNESCO ISCED-F 2013

---

## Evaluation Audit (v3.6.0)

### F1 Scoring Workflow

| File | Status | Notes |
|------|--------|-------|
| `poc/prepare_f1_datasets.py` | ✅ Active | Builds cleaned evaluation datasets from the training CSVs |
| `poc/evaluate_f1.py` | ✅ Active | Calculates precision, recall, and F1 for degree, field, and degree-field pair outputs |
| `poc/smoke_test_cli.py` | ✅ Active | Runs quick CLI checks; current result is `3/3 smoke checks passed` |
| `evaluation/evaluation_summary.csv` | ✅ Current | Stores the latest F1 summary |
| `evaluation/*_failures.csv` | ✅ Current | Stores incorrect predictions for debugging |

### Current F1 Summary

| Dataset | Degree F1 | Field F1 | Degree+Field Pair F1 |
|---------|----------:|---------:|---------------------:|
| `layer1` | 0.7618 | 0.9134 | 0.6353 |
| `layer2` | 0.7863 | 0.8312 | 0.5323 |
| `layer3` | 0.3975 | 0.5153 | 0.1604 |
| `indian_usa` | 0.5393 | N/A | 0.4400 |
| `indian_uk` | 0.5533 | N/A | 0.4509 |
| `indian_world` | 0.3479 | N/A | 0.2572 |

**Note:** International datasets are degree-only, so field F1 is not applicable.

---

## User Interfaces

### Interactive CLI Proof of Concept (`app.py`)
- **Status:** ✅ Active
- **Engines Exposed:** [A+B1] RapidFuzz · [B2] TF-IDF · [B3] Embeddings · [C] L2 Combined · [D] Orchestrator
- **Features:** Test suite · Custom input · Batch CSV · Cross-engine comparison

---

## Bug History

| Bug | Affected Version | Status | Fix Applied |
|-----|-----------------|--------|-------------|
| `token_set_ratio` superset bias (long canonicals absorbing short inputs) | ≤v2.3.0 | ✅ Fixed | v3.0.0 — combined scorer |
| `\bin\b` false field-splits on 'Admin', 'Engineering' | ≤v2.3.0 | ✅ Fixed | v3.0.0 — `\s+in\s+` |
| FastAPI server instability | v2.x | ✅ Resolved | v3.0.0 — removed; replaced with CLI |
| L3 stub `None` canonical crash | v3.0.0-beta | ✅ Fixed | v3.0.0 — structured dict return |
| `_combined_score()` missing `**kwargs` — all L2 scores zeroed | v3.0.0 | ✅ Fixed | v3.5.0 — added `**kwargs` |
| Medical degrees (MBBS, BDS, BPharm) absent from dictionary | ≤v3.0.0 | ✅ Fixed | v3.5.0 — `UG MEDICINE` category added |
| Compact CS/IT field inputs not inferred | v3.5.0 | ✅ Fixed | v3.6.0 — compact CS/IT inference added |

---

## Known Issues & Action Items

- [ ] **Threshold Calibration:** Use `layer2_fuzzy_training.csv` to fine-tune `auto_accept` (currently 88.0) and `flag_review` (currently 70.0) thresholds per noise type and difficulty level.
- [ ] **L3 Regex Tuning:** Use `evaluation/layer3_failures.csv` and `layer3_unstructured_training.csv` to improve sentence extraction and degree-field pair matching.
- [ ] **International Integration:** Determine which SQL scope (USA / UK / WORLD) to adopt for the Growth Grids production database seed.
- [ ] **HuggingFace Token:** Set `HF_TOKEN` environment variable to resolve unauthenticated download warning from Sentence-Transformers.
- [x] **Evaluation Runner:** Added formal F1 scoring through `poc/evaluate_f1.py`, with summary and failure outputs under `evaluation/`.

---

## Security & Dependencies

| Dependency | Purpose | Install Tier |
|------------|---------|-------------|
| `rapidfuzz` | Engine B-1 (Levenshtein) | Minimum |
| `scikit-learn`, `numpy` | Engine B-2 (TF-IDF) | Standard |
| `sentence-transformers`, `torch` | Engine B-3 (Embeddings) | Full (~500 MB) |

- All REST server dependencies (FastAPI, Uvicorn, Pydantic) removed in v3.0.0 — attack surface reduced.
- No network calls at runtime; all model weights are cached locally after first download.
- `.gitignore` enforces exclusion of `__pycache__/` and compiled `.pyc` files.

---

## Contribution Log

| Version | Contributor | Contribution |
|---------|-------------|--------------|
| v1.0.0 | Arnav | Initial 3-layer engine, exact-match dictionary, SQL/CSV seed |
| v2.0.0 | Arnav | Layer 1/2 overhaul, permutation engine, 7k alias expansion |
| v2.1.0–v2.3.0 | Arnav | REST API, TF-IDF/Embeddings engines, SQL rewrite, documentation |
| v3.0.0 | Arnav | L3 engine, L2 combined, orchestrator, CLI, superset bias fix |
| v3.5.0 | **Jai Gupta** | Dataset engineering — all `data/` files |
| v3.5.0 | Arnav | Integration, RapidFuzz `**kwargs` fix, medical degrees, docs |
| v3.6.0 | **Himanshi Kaushik** | F1 scoring workflow, evaluation outputs, GitHub PR integration, and documentation sync |
| v3.6.0 | **Keshav Singhal** | Helped with F1 scoring work, validation, and review |

---

*Last updated: 27 June 2026 — v3.6.0*
