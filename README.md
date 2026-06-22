# CV Manager — Qualification Standardization (SIP)

> **Project:** Growth Grids × University of Southampton Delhi
> **Deadline:** 3 July 2026
> **Current Version:** 3.0.0 (22 June 2026)

This repository contains the deliverables for the Growth Grids Summer Internship Project regarding standardisation of candidate qualification strings in CV Manager.

---

## Architecture Overview

The normalisation pipeline is a **three-layer, multi-engine system** that processes raw education strings from structured abbreviations all the way to conversational sentences.

```
Raw Input String
       │
  ┌────▼──────────────────────────────────────────────────────────┐
  │  LAYER 1 — Exact Dictionary Lookup                            │
  │  6,980+ pre-computed alias permutations (JSON + CSV)          │
  │  Latency: ~0 ms  ·  Accuracy: 100% on known aliases           │
  └────┬──────────────────────────────────────────────────────────┘
       │ miss
  ┌────▼──────────────────────────────────────────────────────────┐
  │  LAYER 2 — Algorithmic Fuzzy Matching (choose one or all)     │
  │                                                               │
  │  Engine B-1 · RapidFuzz  — token_set × sort combined scorer  │
  │  Engine B-2 · TF-IDF     — character 3–5-gram cosine sim.    │
  │  Engine B-3 · Embeddings — all-MiniLM-L6-v2 semantic cosine  │
  │  Engine C   · Combined   — weighted consensus of B1+B2+B3     │
  └────┬──────────────────────────────────────────────────────────┘
       │ miss / low confidence
  ┌────▼──────────────────────────────────────────────────────────┐
  │  LAYER 3 — NLP / Heuristic Extraction                         │
  │  Pure-Python, no ML dependencies.  Four-strategy cascade:     │
  │  S1 Sentence extraction  S2 Shortcode expansion               │
  │  S3 Level keyword detect S4 Field-only inference              │
  └────┬──────────────────────────────────────────────────────────┘
       │
  ┌────▼──────────────────────────────────────────────────────────┐
  │  RESULT  {canonical_degree, canonical_field, confidence,      │
  │           status, layer_used, alternatives, audit_trail}      │
  └───────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
cv_manager_sip/
├── data/
│   ├── degree_aliases.csv            # ~7,000 alias → canonical mappings
│   ├── degree_dictionary.json        # Canonical degree dict with levels & codes
│   ├── field_of_study_aliases.csv    # 308 field aliases across 68 fields
│   ├── degree_field_map.csv          # 186 UGC-compliant degree-field pairs
│   ├── full_education_reference.csv  # Combined degree × field reference table
│   ├── education_reference_seed.sql  # SQL schema + seed for field aliases
│   ├── education_seed.sql            # Full 5-table relational schema + inserts
│   ├── education_seed.json           # JSON export of aliases + sample candidates
│   └── education_schema_seed.csv     # Sample candidate data (CSV)
│
├── poc/
│   ├── app.py                        # ★ Unified POC CLI — entry point for all engines
│   │
│   ├── normalizer_rapidfuzz.py       # Standalone · Engine B-1 (RapidFuzz)
│   ├── normalizer_tfidf.py           # Standalone · Engine B-2 (TF-IDF)
│   ├── normalizer_embeddings.py      # Standalone · Engine B-3 (Embeddings)
│   │
│   ├── engine_l2_combined.py         # ★ NEW · Layer 2 consensus voting engine
│   ├── engine_l3.py                  # ★ NEW · Layer 3 NLP/heuristic engine
│   └── engine_orchestrator.py        # ★ NEW · Master 3-layer orchestrator
│
├── auxilary_sources/
│   └── field_of_study.py             # Generator script for field aliases
│
├── reports/                          # Supporting documents & research
├── requirements.txt                  # Python dependency manifest
├── README.md                         # This file
├── CHANGELOG.md                      # Full version history
└── explainme.md                      # Growth Grids deployment decision brief
```

---

## Quick Start

### 1. Install dependencies

```bash
# Minimum (RapidFuzz engine only — no ML, fastest):
pip install rapidfuzz

# Standard (recommended — all lightweight engines):
pip install rapidfuzz scikit-learn numpy

# Full (all engines including semantic embeddings — ~500 MB extra):
pip install -r requirements.txt
```

### 2. Run the unified POC application

Navigate to the `poc/` directory and launch the interactive CLI:

```bash
cd poc
python app.py
```

The application loads all available engines and presents a menu:

```
═══════════════════════════════════════════════════════════════════════
  MAIN MENU — Select an engine
═══════════════════════════════════════════════════════════════════════
    1.  [A+B1] RapidFuzz (L1+L2)                  ✓
    2.  [B2]   TF-IDF (L1+L2)                     ✓
    3.  [B3]   Embeddings (L1+L2)                  ✓ / ✗
    4.  [C]    L2 Combined (voting)                ✓
    5.  [D]    Orchestrator (full)                 ✓
    6.  Compare all engines on custom input
    7.  Exit
```

Each engine sub-menu provides:
- Run the standard 20-input test suite
- Normalise a custom input (with full result breakdown)
- Batch process from a CSV or TXT file (with optional output save)
- Cross-engine comparison for a single input

### 3. Run individual standalone engines

Each engine is also directly runnable as a standalone CLI:

```bash
cd poc

python normalizer_rapidfuzz.py    # Engine B-1
python normalizer_tfidf.py        # Engine B-2
python normalizer_embeddings.py   # Engine B-3 (needs torch)
python engine_l2_combined.py      # Layer 2 consensus voting
python engine_l3.py               # Layer 3 heuristics (conversational text)
python engine_orchestrator.py     # Full 3-layer master orchestrator
```

---

## Engine Reference

| ID | File | Mechanism | Latency | Dependencies |
|----|------|-----------|---------|--------------|
| **B-1** | `normalizer_rapidfuzz.py` | Levenshtein combined score | ~1–5 ms | `rapidfuzz` |
| **B-2** | `normalizer_tfidf.py` | Char 3–5-gram cosine sim | <1 ms | `scikit-learn` |
| **B-3** | `normalizer_embeddings.py` | Semantic dense vectors | ~50–100 ms | `torch`, `sentence-transformers` |
| **C** | `engine_l2_combined.py` | Weighted consensus of B1+B2+B3 | ~2–110 ms | same as above |
| **D** | `engine_orchestrator.py` | L1 → L2-Combined → L3 full pipeline | variable | all |
| **L3** | `engine_l3.py` | 4-strategy regex/heuristic cascade | <1 ms | stdlib only |

---

## Deployment Options

The pipeline is packaged as **three named deployment versions** for Growth Grids to select based on infrastructure constraints.

> **📄 Full Decision Brief**: [`explainme.md`](explainme.md) — per-version technical profiles, engine sub-options, and recommendation rationale.

| Criterion | **Version A** — Lookup Only | **Version B** — Lookup + Fuzzy ⭐ | **Version C** — Full 3-Layer |
|-----------|-----------|-------------|-----------| 
| **Layers** | L1 only | L1 + L2 | L1 + L2 + L3 |
| **Latency** | ~0 ms | 1–100 ms | Variable |
| **Typo Handling** | ❌ | ✅ High | ✅ High |
| **Synonym Resolution** | ❌ | ⚠️ Engine-dependent | ✅ Yes |
| **Unstructured Text** | ❌ | ❌ | ✅ Yes |
| **Dependencies** | stdlib only | +1–2 packages | Full ML stack |
| **Infra Cost** | Lowest | Low–Medium | High |
| **Best For** | Dropdown data | Mixed text fields | Raw resumes |

> **Recommendation**: Start with **Version B** (RapidFuzz engine) for production. Upgrade to Version C when unstructured resume parsing becomes a requirement.

---

## Data Extensibility

Reference data is provided in **JSON**, **CSV**, and **SQL** formats for easy ingestion across different systems:

- `degree_dictionary.json` — import directly as a canonical degree reference
- `degree_aliases.csv` — bulk-load alias mappings
- `education_seed.sql` — seed a relational DB (MySQL/PostgreSQL compatible)
- `education_seed.json` — MongoDB / NoSQL ready

---

## Key Bug Fixes in v3.0.0

| Issue | Root Cause | Fix |
|-------|-----------|-----|
| `"Bachelor of Business Admin"` misclassified | `token_set_ratio` superset bias | Combined scorer: `token_set_ratio×0.65 + token_sort_ratio×0.35` |
| False field-splits on "Admin", "Engineering" | `\bin\b` matched inside word boundaries | Replaced with `\s+in\s+` (requires surrounding spaces) |
| FastAPI server instability | External HTTP server overhead | Removed; replaced with rich interactive CLI |
| L3 stub returned `None` canonical crashing display | No null guard | L3 now returns structured dict; caller always gets displayable output |

---

*See [`CHANGELOG.md`](CHANGELOG.md) for full version history.*
