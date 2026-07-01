# CV Manager — Qualification Standardization (SIP)

> **Project:** Growth Grids × University of Southampton Delhi
> **Deadline:** 3 July 2026
> **Current Version:** 3.7.0 (1 July 2026)
> **Contributors:** Arnav Mishra (pipeline & integration) · Jai Gupta (dataset engineering) · Himanshi Kaushik & Keshav Singhal (F1 scoring)

This repository contains the deliverables for the Growth Grids Summer Internship Project regarding standardisation of candidate qualification strings in CV Manager.

---

## Architecture Overview

The normalisation pipeline is a **three-layer, multi-engine system** with a two-stage runtime flow: Layer 1 exact lookup first, then `L2_Unified`, which combines the old Layer 2 fuzzy consensus and Layer 3 heuristic extraction in one advanced layer.

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
  │  L2_UNIFIED — Fuzzy + Heuristic Advanced Resolution           │
  │                                                               │
  │  Engine B-1 · RapidFuzz  — token_set × sort combined scorer  │
  │  Engine B-2 · TF-IDF     — character 3–5-gram cosine sim.    │
  │  Engine B-3 · Embeddings — all-MiniLM-L6-v2 semantic cosine  │
  │  Engine C   · Unified    — fuzzy consensus + L3 heuristics    │
  └────┬──────────────────────────────────────────────────────────┘
       │ miss / low confidence
  ┌────▼──────────────────────────────────────────────────────────┐
  │  LAYER 3 LOGIC — Embedded inside L2_Unified                   │
  │  Pure-Python fallback when fuzzy confidence is low/absent.    │
  │  S1 Sentence extraction  S2 Shortcode expansion               │
  │  S3 Level keyword detect S4 Field-only inference              │
  └────┬──────────────────────────────────────────────────────────┘
       │
  ┌────▼──────────────────────────────────────────────────────────┐
  │  RESULT  {canonical_degree, canonical_field, confidence,      │
  │           status, layer_used, resolution_strategy, audit}     │
  └───────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
cv_manager_sip/
├── data/                              # All reference data & training datasets
│   │
│   │  ── Core dictionary & alias files ──
│   ├── degree_aliases.csv            # 7,593 alias → canonical mappings (inc. medical)
│   ├── degree_dictionary.json        # Canonical degree dict with levels & codes
│   ├── field_of_study_aliases.csv    # 308 field aliases across 68 fields
│   ├── degree_field_map.csv          # 186 UGC-compliant degree-field pairs
│   ├── full_education_reference.csv  # Combined degree × field reference table
│   ├── education_reference_seed.sql  # SQL schema + seed for field aliases
│   ├── education_seed.sql            # Full 5-table relational schema + inserts
│   ├── education_seed.json           # JSON export of aliases + sample candidates
│   ├── education_schema_seed.csv     # Sample candidate data (CSV)
│   │
│   │  ── ★ NEW (v3.5.0) Training datasets — Jai Gupta ──
│   ├── layer1_exact_lookup_training.csv   # 6,976 gold-standard L1 validation samples
│   ├── layer2_fuzzy_training.csv          # 15,233 noisy alias samples for L2 tuning
│   ├── layer3_unstructured_training.csv   # 1,124 conversational text samples for L3
│   ├── degree_only_canonical_catalog.csv  # 141-entry multi-country canonical catalog
│   ├── indian_usa_degrees_training.csv    # 9,448 India + USA alias permutations
│   ├── indian_uk_degrees_training.csv     # 9,240 India + UK alias permutations
│   ├── indian_world_degrees_training.csv  # 17,913 India + world alias permutations
│   ├── degree_only_manifest.json          # Dataset manifest & permutation scope
│   └── education_reference_expanded_sql_files/   # ★ Expanded SQL seeds (v3.5.0)
│       ├── education_reference_expanded_usa.sql    # 218 fields × 84 degrees (USA)
│       ├── education_reference_expanded_uk.sql     # 218 fields × 61 degrees (UK)
│       ├── education_reference_expanded_world.sql  # 348 fields × 179 degrees (world)
│       ├── education_reference_expanded_summary.json
│       └── README.md
│
├── evaluation/                       # ★ NEW (v3.6.0) — F1 scoring outputs
│   ├── cleaned_eval_layer1.csv       # Cleaned L1 evaluation dataset
│   ├── cleaned_eval_layer2.csv       # Cleaned L2 evaluation dataset
│   ├── cleaned_eval_layer3.csv       # Cleaned L3 evaluation dataset
│   ├── cleaned_eval_indian_usa.csv   # Degree-only India + USA evaluation dataset
│   ├── cleaned_eval_indian_uk.csv    # Degree-only India + UK evaluation dataset
│   ├── cleaned_eval_indian_world.csv # Degree-only India + world evaluation dataset
│   ├── evaluation_summary.csv        # F1, accuracy, TP/FP/FN, latency summary
│   ├── layer*_failures.csv           # Failure outputs for debugging
│   ├── indian_*_failures.csv         # International failure outputs
│   ├── *_confusion.csv               # Degree, field, and pair confusion matrices
│   └── *.md                          # Metrics, mapping, ambiguity, and scope notes
│
├── poc/
│   ├── app.py                        # ★ Unified POC CLI — entry point for all engines
│   ├── ui_server.py                  # ★ NEW (v3.7.0) — local browser UI for all system types
│   │
│   ├── normalizer_rapidfuzz.py       # Standalone · Engine B-1 (RapidFuzz)
│   ├── normalizer_tfidf.py           # Standalone · Engine B-2 (TF-IDF)
│   ├── normalizer_embeddings.py      # Standalone · Engine B-3 (Embeddings)
│   │
│   ├── engine_l2_combined.py         # Legacy Layer 2 consensus voting engine
│   ├── engine_l2_l3_unified.py       # ★ NEW (v3.7.0) — unified fuzzy + heuristic layer
│   ├── engine_l3.py                  # ★ Layer 3 NLP/heuristic engine
│   ├── engine_orchestrator.py        # ★ Master orchestrator: L1 → L2_Unified
│   ├── evaluate_datasets.py          # ★ NEW (v3.5.0) — Training dataset evaluation runner
│   ├── prepare_f1_datasets.py        # ★ NEW (v3.6.0) — Builds cleaned F1 datasets
│   ├── evaluate_f1.py                # ★ NEW (v3.6.0) — Precision/recall/F1 scorer
│   └── smoke_test_cli.py             # ★ NEW (v3.6.0) — CLI smoke checks
│
├── auxilary_sources/
│   └── field_of_study.py             # Generator script for field aliases
│
├── reports/                          # Supporting documents & research
├── requirements.txt                  # Python dependency manifest
├── README.md                         # This file
├── CHANGELOG.md                      # Full version history
├── platform_audit.md                 # Platform & dataset audit log
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

### 2. Run the local web UI

Launch the dependency-light browser UI from the project root:

```bash
python poc/ui_server.py
```

Then open:

```text
http://127.0.0.1:8765
```

The UI provides single input normalization, batch normalization, all-engine comparison, dataset overview, and engine availability for every system type.

### 3. Run the unified POC CLI application

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
    4.  [C]    L2+L3 Unified                       ✓
    5.  [D]    Orchestrator (full)                 ✓
    6.  Compare all engines on custom input
    7.  Exit
```

Each engine sub-menu provides:
- Run the standard 20-input test suite
- Normalise a custom input (with full result breakdown)
- Batch process from a CSV or TXT file (with optional output save)
- Cross-engine comparison for a single input

### 4. Run individual standalone engines

Each engine is also directly runnable as a standalone CLI:

```bash
cd poc

python normalizer_rapidfuzz.py    # Engine B-1
python normalizer_tfidf.py        # Engine B-2
python normalizer_embeddings.py   # Engine B-3 (needs torch)
python engine_l2_l3_unified.py    # Unified Layer 2 fuzzy + Layer 3 heuristic
python engine_l3.py               # Layer 3 heuristics (conversational text)
python engine_orchestrator.py     # Full orchestrator: L1 → L2_Unified
```

### 5. Run F1 scoring

The F1 scoring workflow prepares cleaned evaluation datasets, runs precision/recall/F1 across the layer and international datasets, and writes updated outputs under `evaluation/`. It also records accuracy, TP/FP/FN counts, resolution rate, average latency, and confusion matrix CSVs.

```bash
python poc/prepare_f1_datasets.py
python poc/evaluate_f1.py --dataset all
python poc/smoke_test_cli.py
```

The F1 scoring work was completed by **Himanshi Kaushik**, with help from **Keshav Singhal**.

---

## Engine Reference

| ID | File | Mechanism | Latency | Dependencies |
|----|------|-----------|---------|--------------|
| **B-1** | `normalizer_rapidfuzz.py` | Levenshtein combined score | ~1–5 ms | `rapidfuzz` |
| **B-2** | `normalizer_tfidf.py` | Char 3–5-gram cosine sim | <1 ms | `scikit-learn` |
| **B-3** | `normalizer_embeddings.py` | Semantic dense vectors | ~50–100 ms | `torch`, `sentence-transformers` |
| **C** | `engine_l2_l3_unified.py` | Fuzzy consensus + heuristic extraction | ~2–110 ms | `rapidfuzz`; optional `scikit-learn`, `torch` |
| **D** | `engine_orchestrator.py` | L1 → L2_Unified full pipeline | variable | same as above |
| **L3** | `engine_l3.py` | 4-strategy regex/heuristic cascade | <1 ms | stdlib only |
| **UI** | `ui_server.py` | Local browser dashboard for all engine types | local | stdlib server + installed engines |

---

## Deployment Options

The pipeline is packaged as **three named deployment versions** for Growth Grids to select based on infrastructure constraints.

> **📄 Full Decision Brief**: [`explainme.md`](explainme.md) — per-version technical profiles, engine sub-options, and recommendation rationale.

| Criterion | **Version A** — Lookup Only | **Version B** — Lookup + Fuzzy ⭐ | **Version C** — Full Unified |
|-----------|-----------|-------------|-----------| 
| **Layers** | L1 only | L1 + L2 | L1 + L2_Unified (L2 + L3 logic) |
| **Latency** | ~0 ms | 1–100 ms | Variable |
| **Typo Handling** | ❌ | ✅ High | ✅ High |
| **Synonym Resolution** | ❌ | ⚠️ Engine-dependent | ✅ Yes |
| **Unstructured Text** | ❌ | ❌ | ✅ Yes |
| **Dependencies** | stdlib only | +1–2 packages | Full ML stack |
| **Infra Cost** | Lowest | Low–Medium | High |
| **Best For** | Dropdown data | Mixed text fields | Raw resumes |

> **Recommendation**: Start with **Version B** (RapidFuzz engine) for production. Upgrade to Version C when unstructured resume parsing becomes a requirement or when the unified fuzzy + heuristic layer should run as one auditable post-L1 step.

---

## Data Extensibility

Reference data is provided in **JSON**, **CSV**, and **SQL** formats for easy ingestion across different systems:

- `degree_dictionary.json` — import directly as a canonical degree reference
- `degree_aliases.csv` — bulk-load alias mappings (7,593 entries including medical degrees)
- `education_seed.sql` — seed a relational DB (MySQL/PostgreSQL compatible)
- `education_seed.json` — MongoDB / NoSQL ready

### Training Datasets (v3.5.0 — `data/`)

A full suite of layer-specific training and evaluation datasets contributed by **Jai Gupta**:

| Dataset | Rows | Scope |
|---------|-----:|-------|
| `layer1_exact_lookup_training.csv` | 6,976 | L1 gold-standard regression samples |
| `layer2_fuzzy_training.csv` | 15,233 | L2 noisy inputs with noise-type & difficulty labels |
| `layer3_unstructured_training.csv` | 1,124 | L3 conversational sentences with span annotations |
| `indian_usa_degrees_training.csv` | 9,448 | India + USA international alias permutations |
| `indian_uk_degrees_training.csv` | 9,240 | India + UK international alias permutations |
| `indian_world_degrees_training.csv` | 17,913 | India + USA + UK + world alias permutations |
| `degree_only_canonical_catalog.csv` | 141 | Multi-country canonical degree catalog |

Expanded SQL seeds for USA (18,312 combinations), UK (13,298), and WORLD (62,292) degree-field pairs are provided in `data/education_reference_expanded_sql_files/`.

### F1 Evaluation Outputs (v3.6.5 — `evaluation/`)

The current F1 scoring suite covers Layer 1, Layer 2, Layer 3, and degree-only international datasets. International datasets are degree-only, so field F1 is marked `N/A`. The summary also includes accuracy, TP/FP/FN counts, resolution rate, average latency, and per-dataset confusion CSVs.

| Dataset | Degree F1 | Field F1 | Degree+Field Pair F1 | vs v3.6.0 |
|---------|----------:|---------:|---------------------:|:---------:|
| `layer1` | 0.7614 | 0.9129 | 0.6353 | ≈ same |
| `layer2` | 0.7753 | 0.8288 | 0.5334 | ≈ same |
| `layer3` | **0.7985** | **0.7343** | **0.4901** | ⬆️ +101% / +42% / +206% |
| `indian_usa` | **0.5730** | N/A | **0.5315** | ⬆️ +3.4% |
| `indian_uk` | **0.5926** | N/A | **0.5506** | ⬆️ +3.9% |
| `indian_world` | **0.3610** | N/A | **0.3184** | ⬆️ +1.3% |

---

## Key Bug Fixes in v3.0.0 – v3.7.0

| Issue | Root Cause | Fix | Version |
|-------|-----------|-----|--------|
| `"Bachelor of Business Admin"` misclassified | `token_set_ratio` superset bias | Combined scorer: `token_set_ratio×0.65 + token_sort_ratio×0.35` | v3.0.0 |
| False field-splits on "Admin", "Engineering" | `\bin\b` matched inside word boundaries | Replaced with `\s+in\s+` (requires surrounding spaces) | v3.0.0 |
| FastAPI server instability | External HTTP server overhead | Removed; replaced with rich interactive CLI | v3.0.0 |
| L3 stub returned `None` canonical crashing display | No null guard | L3 now returns structured dict; caller always gets displayable output | v3.0.0 |
| `MBBS` and all L2 matches returning `0.000` | `_combined_score()` missing `**kwargs`; `score_cutoff` crash silently swallowed | Added `**kwargs` to scorer signature and forwarded to sub-scorers | v3.5.0 |
| Medical degrees (MBBS, BDS, BPharm) not resolvable | Missing from training dictionary entirely | Added `UG MEDICINE` category to `generate_data.py`; dictionary regenerated | v3.5.0 |
| Compact CS/IT inputs missed field inference | Inputs like `BTech CSE` and `BTech IT` kept the degree but dropped the field | Added compact CS/IT field inference after degree alias removal | v3.6.0 |
| L3 shortcode map incomplete | Missing BEng, slash-forms, PhD variants, EMBA, MBBS | Expanded to 80+ shortcodes; PhD normalization; field acronym map added | v3.6.5 |
| L3 stub in `normalizer_rapidfuzz.py` bypassed the real engine | `layer3_stub` used primitive regex instead of delegating to `engine_l3.py` | Renamed to `layer3_heuristic`; now delegates to `L3HeuristicEngine` | v3.6.5 |
| Institution names leaking as field predictions | Field regex captured `Jadavpur`, `Pune`, `Amity` etc. | Extended `_FIELD_STOPWORDS` + `_normalize_field()` validation in L3 path | v3.6.5 |
| Separate L2 and L3 routing duplicated advanced logic | Orchestrator ran fuzzy consensus and heuristic extraction as separate post-L1 branches | Added `L2_Unified` layer with fuzzy consensus + heuristic extraction in one auditable step | v3.7.0 |
| Plain non-education text triggered L3 review results | Permissive sentence-start regex accepted any short text beginning with letters | Added explicit degree-signal and degree-prefix guards before heuristic extraction returns a mention | v3.7.0 |
| No simple browser UI for full-system testing | Only CLI/evaluation scripts were available | Added `poc/ui_server.py` local dashboard for single, batch, compare, and dataset overview workflows | v3.7.0 |

---

*See [`CHANGELOG.md`](CHANGELOG.md) for full version history.*
