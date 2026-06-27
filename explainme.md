# Pipeline Deployment Options — Growth Grids Decision Brief
# (Updated for v3.6.0 — 27 June 2026)

> **Purpose**: This document packages the CV Manager normalisation pipeline as **three distinct, named deployment versions** so that Growth Grids can evaluate and select the option that best fits their infrastructure, latency, and accuracy requirements.
>
> **v3.0.0 Update**: Layer 2 now offers a **Combined Engine (Engine C)** that runs all three sub-engines in consensus, and Layer 3 is now a **fully implemented heuristic engine** (no ML required) rather than a stub.
>
> **v3.5.0 Update**: A comprehensive suite of **internationally-scoped training datasets** (`data/`) has been added, engineered by Jai Gupta. These datasets cover India, USA, UK, and a curated world catalog — enabling future model evaluation, threshold calibration, and production testing at global scale. Additionally, the dictionary now includes **medical degrees** (MBBS, BDS, BPharm), and a RapidFuzz scoring bug causing all L2 matches to silently return `0.000` has been fixed.
>
> **v3.6.0 Update**: A reproducible **F1 scoring workflow** has been added for Layer 1, Layer 2, Layer 3, and the international degree-only datasets. The workflow was completed by Himanshi Kaushik, with help from Keshav Singhal, and now gives measurable precision/recall/F1 outputs for the existing CLI and normalizer behavior.

---

## Version A: Lookup Only (Layer 1)

### What It Does
Strictly performs **exact dictionary matching** against the expanded alias map (6,980+ pre-computed permutations). An input string is cleaned (lowercased, punctuation stripped, separators normalised) and checked against the dictionary. If a match is found, the canonical degree is returned instantly. If not, the input is marked `unresolved`.

### Layers Active
| Layer | Status |
|-------|--------|
| **L1 — Exact Lookup** | ✅ Active |
| L2 — Fuzzy Match | ❌ Disabled |
| L3 — NLP / Heuristics | ❌ Disabled |

### Technical Profile
| Metric | Value |
|--------|-------|
| **Latency** | ~0 ms (hash-map lookup) |
| **Determinism** | 100% — same input always produces same output |
| **Dependencies** | Python standard library only (`csv`, `json`, `re`) |
| **Infrastructure** | Minimal — runs anywhere, no ML runtime needed |
| **Accuracy** | High on structured data; **zero tolerance for typos** |

### When To Pick This
- Your candidate data is **mostly structured** (e.g., entered via dropdowns or constrained forms).
- You need the **absolute lowest latency** and simplest deployment.
- Unmapped entries can be safely **discarded or queued for manual review**.

### Limitations
- Any input not explicitly present in the alias dictionary will be rejected.
- Typos like `"Bacheler of Technology"` will fail unless pre-mapped.

---

## Version B: Lookup + Fuzzy (Layer 1 & Layer 2) — ⭐ Recommended

### What It Does
Performs exact dictionary matching first (Layer 1). If no match is found, the input **falls back to an algorithmic similarity engine** that scores the input against all 6,980+ known aliases and returns the closest match above a configurable confidence threshold.

Four interchangeable Layer 2 options are provided:

#### Engine Option B-1: RapidFuzz (Combined Levenshtein Scorer)
- **File**: `poc/normalizer_rapidfuzz.py`
- **How**: Uses a weighted combination of `token_set_ratio × 0.65 + token_sort_ratio × 0.35`. The combined scorer eliminates the "superset bias" of the old `token_set_ratio`-only approach (which caused long canonical names like "Bachelor of Business Administration" to absorb unrelated short inputs).
- **Speed**: ~1–5 ms per query.
- **Best at**: Catching typos (`"Btehc"` → `"BTech"`), word reorderings, abbreviation variants.
- **Dependencies**: `rapidfuzz` (lightweight pure-C extension).

#### Engine Option B-2: TF-IDF Character N-Gram Cosine Similarity
- **File**: `poc/normalizer_tfidf.py`
- **How**: Converts strings to sparse vectors using character 3-to-5-grams weighted by TF-IDF, then measures cosine distance.
- **Speed**: <1 ms per query (fastest L2 option).
- **Best at**: High-throughput batch processing; excellent typo tolerance since errors only corrupt a fraction of n-grams.
- **Dependencies**: `scikit-learn`, `numpy`.

#### Engine Option B-3: Sentence-Transformer Semantic Embeddings
- **File**: `poc/normalizer_embeddings.py`
- **How**: Passes input through `all-MiniLM-L6-v2` to produce a 384-dim dense vector; matches via dot product against pre-encoded canonical aliases.
- **Speed**: ~50–100 ms per query (CPU).
- **Best at**: Resolving conceptual abbreviations (`"B.S."`, `"B.Sc."`, `"Bachelor of Science"` all map correctly).
- **Dependencies**: `sentence-transformers`, `torch` (~500 MB).

#### Engine Option C: L2 Combined (Weighted Consensus Voting) ⭐ New in v3
- **File**: `poc/engine_l2_combined.py`
- **How**: Runs B-1 + B-2 + B-3 in parallel. Each engine votes for its top canonical match weighted by `engine_base_weight × confidence`. The canonical with the highest total vote weight wins. A **consensus bonus** (+0.05) is applied when ≥2 engines agree.
- **Speed**: Combined latency of all active engines (~2–110 ms depending on Embeddings availability).
- **Best at**: Maximum L2 accuracy — individual engine weaknesses are cancelled out by cross-engine consensus.
- **Dependencies**: All of the above. Degrades gracefully if Embeddings is absent.

### Layers Active
| Layer | Status |
|-------|--------|
| **L1 — Exact Lookup** | ✅ Active |
| **L2 — Fuzzy Match** | ✅ Active (choose one engine above) |
| L3 — NLP / Heuristics | ❌ Disabled |

### When To Pick This
- Your data contains **natural human variation** — spelling mistakes, abbreviation differences, minor formatting inconsistencies.
- You are processing **historical free-text input fields** or **OCR outputs** where data is somewhat clean but not perfectly structured.
- **Recommended as the default starting point** for most production use cases.

### Limitations
- Cannot parse complex unstructured sentences (e.g., `"I completed my B.S. in Computer Science in 2022"`).
- Confidence thresholds (`auto-accept ≥ 88`, `review ≥ 70` for B-1) may need tuning for your specific data distribution.

---

## Version C: Full 3-Layer Pipeline (Lookup + Fuzzy + NLP/Heuristics)

### What It Does
The **complete stack**. Inputs flow through all three layers sequentially via `engine_orchestrator.py`:
1. **Layer 1** — Exact dictionary lookup (instant resolution for known aliases).
2. **Layer 2** — Combined consensus fuzzy matching (B-1 + B-2 + optional B-3).
3. **Layer 3** — Pure-Python heuristic extraction for fully unstructured conversational text.

### Layer 3 Detail (Fully Implemented in v3.0.0)
Layer 3 is no longer a stub. `engine_l3.py` implements a **four-strategy heuristic cascade** with zero ML dependencies:

| Strategy | Description | Confidence |
|----------|-------------|------------|
| **S2 Shortcode Expansion** | Hard-coded map of 50+ abbreviations (BCA, PGDM, LLB…) → canonical. Runs first (highest precision). | 0.80 |
| **S1 Sentence Extraction** | Regex patterns extract degree mentions from conversational sentences. | 0.60–0.72 |
| **S3 Level Keyword Detection** | Maps level keywords (bachelor, master, phd, diploma…) to a degree-level group. | 0.50 |
| **S4 Field-Only Inference** | Detects field-of-study mention when no degree level is identifiable. | 0.35 |

### Orchestrator Operating Modes
`engine_orchestrator.py` exposes three modes so you can tune the speed/accuracy tradeoff:

| Mode | L2 Engines | L3 | Typical Latency |
|------|-----------|-----|----------------|
| `fast` | RapidFuzz only | No | 1–5 ms |
| `standard` | RapidFuzz + TF-IDF | No | 2–6 ms |
| `full` | RapidFuzz + TF-IDF + Embeddings | Yes | 50–120 ms |

### Layers Active
| Layer | Status |
|-------|--------|
| **L1 — Exact Lookup** | ✅ Active |
| **L2 — Fuzzy Match** | ✅ Active (Combined) |
| **L3 — NLP / Heuristics** | ✅ Active (pure-Python cascade) |

### When To Pick This
- You need to process **entirely raw, unstructured resume blocks** or free-text candidate summaries.
- Your input data includes **conversational sentences** like *"I completed my B.S. in Computer Science from MIT in 2022"*.
- You want **maximum extraction rate** at minimal infrastructure overhead (L3 needs no ML runtime).

### Limitations
- L3 confidence is inherently lower (0.35–0.80) — all L3 results are flagged as `review_needed`.
- Regex patterns may require domain-specific tuning for non-standard Indian institution formats.

---

## Decision Matrix — Side-by-Side Comparison

| Criterion | Version A | Version B ⭐ | Version C |
|-----------|-----------|-------------|-----------|
| **Layers** | L1 only | L1 + L2 | L1 + L2 + L3 |
| **Latency** | ~0 ms | 1–110 ms | Variable |
| **Typo Handling** | ❌ None | ✅ High | ✅ High |
| **Synonym Resolution** | ❌ None | ⚠️ Engine-dependent | ✅ Yes |
| **Unstructured Text** | ❌ No | ❌ No | ✅ Yes |
| **Dependencies** | stdlib only | +1–2 packages | Full ML stack (optional) |
| **Infra Cost** | Lowest | Low–Medium | Medium (L3 is pure-Python) |
| **Maintenance** | Near zero | Threshold tuning | Regex pattern updates |
| **Risk** | Lowest | Low | Low–Moderate |
| **Recommended For** | Structured / dropdown data | Mixed-quality text fields | Raw resumes / free-text |

---

## Recommendation

> **Start with Version B** using **Engine C (L2 Combined)** for immediate production deployment. It provides the strongest balance of accuracy, speed, and resilience by leveraging cross-engine consensus. Use `standard` mode in the orchestrator (RapidFuzz + TF-IDF, no heavy GPU/CPU model required).
>
> **Upgrade to Version C (full mode)** when unstructured resume parsing becomes a business requirement. Because Layer 3 is now a pure-Python heuristic cascade, there is no additional ML infrastructure cost — only the Embeddings engine (B-3) requires PyTorch.

---

## Appendix: Layer 2 Engine Strategic Comparison

| Feature | B-1 RapidFuzz | B-2 TF-IDF | B-3 Embeddings | C Combined |
|---------|--------------|------------|----------------|------------|
| **Mechanism** | Token overlap + edit distance (combined) | Sub-string vector overlaps | Neural semantic vectors | Weighted vote of B1+B2+B3 |
| **Speed** | ~1–5 ms | <1 ms | ~50–100 ms | 2–110 ms |
| **Typo Resilience** | High | High | Moderate | High |
| **Synonym Matching** | Low | Low | Excellent | Good |
| **Infrastructure** | Light | Light | Heavy | Light (without B-3) |
| **Single Engine Failure Tolerance** | — | — | — | ✅ Degrades gracefully |

---

## Training & Evaluation Datasets (v3.5.0)

A purpose-built suite of **internationally-scoped** training datasets now accompanies the pipeline, enabling rigorous engine evaluation and future model development. Contributed by **Jai Gupta**, integrated by **Arnav**.

| Dataset | Rows | Designed For |
|---------|-----:|---------------|
| `layer1_exact_lookup_training.csv` | 6,976 | L1 regression & dictionary validation |
| `layer2_fuzzy_training.csv` | 15,233 | L2 threshold calibration (noise-typed, difficulty-rated) |
| `layer3_unstructured_training.csv` | 1,124 | L3 regex/NER evaluation (character-span annotated) |
| `indian_usa_degrees_training.csv` | 9,448 | International alias permutations — India + USA |
| `indian_uk_degrees_training.csv` | 9,240 | International alias permutations — India + UK |
| `indian_world_degrees_training.csv` | 17,913 | International alias permutations — India + world |
| `degree_only_canonical_catalog.csv` | 141 | Multi-country canonical degree catalog |

Expanded SQL seeds (USA: 18,312 · UK: 13,298 · WORLD: 62,292 degree-field combinations) are in `education_reference_expanded_sql_files/`, sourced from NCES CIP 2020, HESA HECoS, QAA/UCAS, and UNESCO ISCED-F 2013.

---

## F1 Scoring Workflow (v3.6.0)

The project now includes an evaluation workflow that measures how well the existing CLI/normalizer pipeline performs against the prepared datasets.

### How To Run

```bash
python poc/prepare_f1_datasets.py
python poc/evaluate_f1.py --dataset all
python poc/smoke_test_cli.py
```

### Current Results

| Dataset | Degree F1 | Field F1 | Degree+Field Pair F1 |
|---------|----------:|---------:|---------------------:|
| `layer1` | 0.7618 | 0.9134 | 0.6353 |
| `layer2` | 0.7863 | 0.8312 | 0.5323 |
| `layer3` | 0.3975 | 0.5153 | 0.1604 |
| `indian_usa` | 0.5393 | N/A | 0.4400 |
| `indian_uk` | 0.5533 | N/A | 0.4509 |
| `indian_world` | 0.3479 | N/A | 0.2572 |

### What This Means

- Layer 1 and Layer 2 are the strongest current paths for structured and semi-structured qualification strings.
- Layer 3 works, but the lower pair F1 shows that unstructured sentence extraction still needs more tuning.
- The international datasets are degree-only, so they mainly measure degree recognition rather than full degree-field matching.
- The failure CSVs in `evaluation/` should be used to decide the next fixes and threshold changes.

---

*This document is part of the SIP deliverables. See [README.md](README.md) for project overview and [CHANGELOG.md](CHANGELOG.md) for version history.*
