# CHANGELOG — CV Manager Qualification Normalizer

> **Project:** CV Manager — Qualification Standardization (SIP)  
> **Organisation:** Growth Grids × University of Southampton Delhi  
> **Deadline:** 3 July 2026

---

## Version 3.6.5 — 28 June 2026

### What's New

**Layer 3 improvement release** — significantly enhanced the L3 heuristic engine to improve degree F1 from the v3.6.0 baseline. The `normalizer_rapidfuzz.py` Layer 3 stub now delegates to the full `engine_l3.py` engine instead of using a primitive keyword regex. CLI output across all engines has been polished. Documentation enriched with a metrics interpretation guide and cross-validation assessment. Work completed by **Arnav Mishra**.

---

### 1. L3 Engine Overhaul (`engine_l3.py`)

- **Expanded shortcode map**: from 50+ to 80+ entries — added `BEng`, `B.Eng`, `M.Eng`, slash-combined forms (`b.tech/be`, `be/btech`), `EMBA`, `B.B.A`, `M.B.A`, `B.C.A`, `M.C.A`, `B.Ed`, `M.Ed`, `B.Arch`, `MBBS`, `BDS`, and more.
- **PhD variant normalization**: Any extracted mention containing `phd`, `ph.d`, `dphil`, `doctorate`, `doctoral` is now canonicalized to `Doctor of Philosophy`.
- **S1 post-canonicalization**: Sentence-extracted text (e.g. `"B.Tech"`, `"BSc degree"`) is now passed through the shortcode map + PhD normalizer before being returned — eliminates raw verbatim text in results.
- **Field acronym map**: New `_FIELD_ACRONYM_MAP` with 40+ compact field abbreviations (CSE → Computer Science and Engineering, ECE → Electronics and Communication Engineering, IT → Information Technology, AI → Artificial Intelligence, DS → Data Science, etc.).
- **Relaxed field extraction**: Minimum field length lowered from `> 2` to `> 1` with a stopword blocklist to filter noise — catches `"IT"`, `"CS"` etc. that were previously dropped.

---

### 2. L3 Stub Delegation (`normalizer_rapidfuzz.py`)

- **Root cause**: `evaluate_f1.py` always routed through `normalizer_rapidfuzz.py`, which had its own primitive `layer3_stub` that returned raw extracted text (e.g. `"B  Tech degree"`) without canonicalization. The proper `engine_l3.py` was never invoked during evaluation.
- **Fix**: `layer3_stub` renamed to `layer3_heuristic`, now imports and delegates to `L3HeuristicEngine` from `engine_l3.py`. Falls back to a minimal keyword detector only if `engine_l3.py` is unavailable. Old name `layer3_stub` kept as an alias for backward compatibility.

---

### 3. CLI Polish (`app.py`, `engine_l3.py`)

- `app.py` version bumped from `3.0.0` → `3.6.5`.
- Updated banner to include contributor name.
- Main menu now uses ✅/❌ icons for engine availability status.
- `_print_single_result` enhanced with a visual confidence bar `[████████████░░░░░░░░]`.
- `engine_l3.py` CLI standalone output polished with Unicode box-drawing characters and aligned columns.

---

### 4. Documentation Enrichment

- **`explainme.md`**: Added two new sections:
  - **Metrics Interpretation Guide** — explains F1/precision/recall, TP/FP/FN definitions in the context of qualification normalization, how to read the confusion matrix CSVs, and what each `evaluation_summary.csv` column means.
  - **Cross-Validation & Stratification Assessment** — explains why k-fold CV is not needed now (no learnable parameters, natural stratification already exists), when it would be needed (ML model or threshold optimizer), and recommends stratified holdout as the future approach.
- **`CHANGELOG.md`**: This entry.
- **`platform_audit.md`**: Updated L3 description, added three new bug fix entries, marked L3 Regex Tuning action item as done, added v3.6.5 contribution log entry.
- **`README.md`**: Version bumped to 3.6.5, contributor name updated to full name.

---

### Attribution

| Contributor | Contribution |
|---|---|
| **Arnav Mishra** | L3 engine overhaul, L3 stub delegation fix, CLI polish, metrics documentation, cross-validation assessment |

---

### Files Changed in v3.6.5

| File | Change |
|---|---|
| `poc/engine_l3.py` | **Rewritten** — expanded shortcode map, PhD normalization, field acronym map, S1 canonicalization, relaxed field extraction |
| `poc/normalizer_rapidfuzz.py` | Updated — `layer3_stub` → `layer3_heuristic` delegate to full L3 engine |
| `poc/app.py` | Updated — version bump to 3.6.5, CLI polish (banner, icons, confidence bar) |
| `explainme.md` | Updated — metrics interpretation guide + cross-validation assessment |
| `platform_audit.md` | Updated — v3.6.5 status, bug fixes, contribution log |
| `README.md` | Updated — version bump, contributor name |
| `CHANGELOG.md` | Added v3.6.5 entry |

---

## Version 3.6.0 — 27 June 2026

### What's New

**F1 scoring release** — added a reproducible F1 evaluation workflow for the qualification normalizer. The workflow prepares cleaned evaluation datasets, scores predictions with precision/recall/F1, writes summary and failure CSVs under `evaluation/`, records accuracy, TP/FP/FN counts, resolution rate, latency, and confusion CSVs, and includes smoke checks for the CLI pipeline. The F1 scoring work was completed by **Himanshi Kaushik**, with help from **Keshav Singhal**.

---

### 1. F1 Evaluation Framework (`evaluation/` + `poc/evaluate_f1.py`)

- Added cleaned evaluation datasets for Layer 1, Layer 2, Layer 3, and international degree-only datasets.
- Added `poc/prepare_f1_datasets.py` to convert the training CSVs into consistent evaluation inputs.
- Added `poc/evaluate_f1.py` to calculate precision, recall, F1, accuracy, TP/FP/FN counts, resolution rate, average latency, and incorrect prediction outputs.
- Added `evaluation/evaluation_summary.csv` as the main summary output.
- Added failure CSVs to make debugging easier after each scoring run.
- Added confusion matrix CSV outputs for degree, field, and degree-field pair labels.

---

### 2. Complete Evaluation Coverage

The F1 scorer now covers all current evaluation datasets:

| Dataset | Degree F1 | Field F1 | Degree+Field Pair F1 |
|---|---:|---:|---:|
| `layer1` | 0.7618 | 0.9134 | 0.6353 |
| `layer2` | 0.7863 | 0.8312 | 0.5323 |
| `layer3` | 0.3975 | 0.5153 | 0.1604 | ← **improved in v3.6.5** |
| `indian_usa` | 0.5393 | N/A | 0.4400 | ← improved in v3.6.5 |
| `indian_uk` | 0.5533 | N/A | 0.4509 | ← improved in v3.6.5 |
| `indian_world` | 0.3479 | N/A | 0.2572 | ← improved in v3.6.5 |

International datasets are degree-only, so field F1 is marked `N/A`.

> See **v3.6.5** entry for the improved metrics after the L3 engine overhaul.

---

### 3. CS/IT Field Inference Improvement (`normalizer_rapidfuzz.py`)

- Improved handling for compact CS/IT inputs such as `BTech CSE`, `B.Tech IT`, and similar variants.
- The normalizer now keeps the degree result and also infers the expected Computer Science / Information Technology field when the field is present in compact form.
- Updated F1 output files after this fix so the metrics reflect the latest behavior.

---

### 4. CLI Smoke Checks (`poc/smoke_test_cli.py`)

- Added a lightweight smoke test file for the existing CLI flow.
- Current smoke check result: `3/3 smoke checks passed`.

---

### Attribution

| Contributor | Contribution |
|---|---|
| **Himanshi Kaushik** | F1 scoring workflow, evaluation outputs, GitHub PR integration, and documentation sync |
| **Keshav Singhal** | Helped with the F1 scoring work, validation, and review |

---

### Files Changed in v3.6.0

| File | Change |
|---|---|
| `evaluation/` | **New / Updated** — cleaned evaluation datasets, F1 summary, failure files, confusion CSVs, and notes |
| `poc/prepare_f1_datasets.py` | **New** — prepares cleaned datasets for F1 scoring |
| `poc/evaluate_f1.py` | **New** — runs precision, recall, F1, accuracy, TP/FP/FN, latency, and confusion scoring |
| `poc/smoke_test_cli.py` | **New** — verifies the CLI path with quick smoke checks |
| `poc/normalizer_rapidfuzz.py` | Updated — compact CS/IT field inference |
| `README.md` | Updated — F1 scoring commands, outputs, and contributor note |
| `CHANGELOG.md` | Added v3.6.0 entry |
| `explainme.md` | Updated — F1 evaluation context and current score table |
| `platform_audit.md` | Updated — evaluation audit, action items, and contribution log |

---

## Version 3.5.0 — 23 June 2026

### What's New

**Dataset expansion release** — all training datasets consolidated into the `data/` directory for direct engine access. A new `evaluate_datasets.py` runner evaluates all engines against the v3.5.0 training sets. CLI tabular output across all POC files has been tidied for consistent column widths. The data engineering work was conducted by **Jai Gupta**; integration, evaluation tooling, and documentation were carried out by **Arnav**.

---

### 1. New Dataset Folder — `data/`

Eight new files (plus the SQL sub-directory) provide training, evaluation, and reference data across all three pipeline layers and three international degree systems. Each file has been designed for a distinct purpose:

| File | Rows / Entries | Purpose |
|---|---:|---|
| `layer1_exact_lookup_training.csv` | 6,976 | Gold-standard exact-match samples for L1 dictionary validation |
| `layer2_fuzzy_training.csv` | 15,233 | Noisy alias pairs with difficulty ratings for L2 threshold tuning |
| `layer3_unstructured_training.csv` | 1,124 | Conversational sentence examples with character-span annotations for L3 NER/regex evaluation |
| `degree_only_canonical_catalog.csv` | 141 | Multi-country canonical degree catalog (degree names only, no field combinations) |
| `indian_usa_degrees_training.csv` | 9,448 | India + USA combined degree alias permutations (49 canonical entries) |
| `indian_uk_degrees_training.csv` | 9,240 | India + UK combined degree alias permutations (43 canonical entries) |
| `indian_world_degrees_training.csv` | 17,913 | India + USA + UK + curated world systems (141 canonical entries) |
| `degree_only_manifest.json` | — | Manifest describing scope, permutation rules, and row counts |

---

### 2. Per-Layer Training Datasets

#### Layer 1 — Exact Lookup Training (`layer1_exact_lookup_training.csv`)
- **6,976 samples** covering the full current alias dictionary.
- Columns: `sample_id`, `raw_input`, `normalized_degree_part`, `canonical_degree`, `canonical_field`, `degree_level`, `degree_short_code`, `split_pattern`, `expected_layer`, `expected_status`, `gold_confidence`, `training_use`, `source`.
- Use case: regression testing of the exact-match dictionary; detecting alias regressions after dictionary updates.

#### Layer 2 — Fuzzy Matching Training (`layer2_fuzzy_training.csv`)
- **15,233 noisy alias samples** spanning multiple noise types (single vowel drops, adjacent transpositions, abbreviation variants, OCR artefacts, etc.) with per-row difficulty ratings (`easy`, `medium`, `hard`).
- Columns: `sample_id`, `raw_input`, `gold_clean_alias`, `canonical_degree`, `canonical_field`, `degree_level`, `noise_type`, `difficulty`, `expected_layer`, `expected_status`, `expected_min_confidence`, `training_use`, `source`.
- Use case: threshold calibration for RapidFuzz and TF-IDF engines; identifying confidence cut-off values per noise type.

#### Layer 3 — Unstructured Text Training (`layer3_unstructured_training.csv`)
- **1,124 conversational sentence examples** with character-span annotations marking degree and field mentions.
- Columns: `sample_id`, `raw_text`, `canonical_degree`, `canonical_field`, `degree_mention`, `field_mention`, `degree_span_start`, `degree_span_end`, `field_span_start`, `field_span_end`, `expected_layer`, `expected_status`, `strategy_hint`, `training_use`.
- Strategy hints include `completed_sentence`, `pursuing_sentence`, `shortcode_expansion` and others — directly aligned with L3 cascade strategies.
- Use case: evaluating and improving L3 sentence extraction regex patterns; future NER model fine-tuning.

---

### 3. International Degree Catalog (`data/degree_only_canonical_catalog.csv` + `indian_*_degrees_training.csv`)

The degree catalog and training sets cover **three international degree systems** alongside the existing India-centric dataset:

| Dataset | Canonical Entries | Degree Systems Covered |
|---|---:|---|
| `indian_usa_degrees_training.csv` | 49 | India + United States |
| `indian_uk_degrees_training.csv` | 43 | India + United Kingdom |
| `indian_world_degrees_training.csv` | 141 | India + USA + UK + curated world |
| `degree_only_canonical_catalog.csv` | 141 | All of the above (catalog view) |

Alias permutation rules applied per entry:
- Degree-only aliases (no field-of-study combinations)
- Abbreviation punctuation and spacing variants
- Country adjective/name/code prefixes
- Qualification/degree/country/duration/honours suffixes
- Catalogued, lowercase, uppercase, and title-case variants

---

### 4. Expanded SQL Reference Seeds (`data/education_reference_expanded_sql_files/`)

Three standalone SQL seed files targeting USA, UK, and global degree systems, expanded from the base Indian seed (`education_reference_seed.sql`). Sources used: NCES CIP 2020, IPEDS/NCES, HESA HECoS, QAA/UCAS, and UNESCO ISCED-F 2013.

| Scope | Canonical Fields | Canonical Degrees / Awards | Degree-Field Combinations |
|-------|---:|---:|---:|
| USA | 218 | 84 | 18,312 |
| UK | 218 | 61 | 13,298 |
| WORLD | 348 | 179 | 62,292 |

Each file includes `field_of_study_aliases`, `degree_aliases`, and `degree_field_map` tables. The `degree_field_map` is a deliberate exhaustive cross-product for CV parser coverage — not an accreditation list.

---

### 5. Bug Fix — RapidFuzz Scorer `**kwargs` (`normalizer_rapidfuzz.py`)

- **Bug**: `_combined_score()` was defined without `**kwargs`, causing `process.extractOne()` to crash when passing `score_cutoff` internally (`got an unexpected keyword argument 'score_cutoff'`). The exception was silently caught, causing all L2 matches to return `0.000` — including obviously resolvable inputs like `MBBS`.
- **Fix**: Updated function signature to `def _combined_score(query, choice, **kwargs)` and forwarded `**kwargs` to `fuzz.token_set_ratio` and `fuzz.token_sort_ratio`.
- **Impact**: L2 RapidFuzz now correctly scores all inputs. This also resolves the `MBBS` recognition gap identified in testing.

---

### 6. Medical Degrees Added to Dictionary (`generate_data.py` + regenerated data files)

- Added `UG MEDICINE` degree category to `generate_data.py` with three new canonical degrees:
  - **Bachelor of Medicine and Bachelor of Surgery (MBBS)** — aliases: `MBBS`, `M.B.B.S.`, `M B B S`, `MB ChB`, `BMBS`
  - **Bachelor of Dental Surgery (BDS)** — aliases: `BDS`, `B.D.S.`
  - **Bachelor of Pharmacy (BPHARM)** — aliases: `BPharm`, `B.Pharm`, `B. Pharma`, `B Pharma`
- Also added `MEDICINE & HEALTH` field-of-study mappings for medical degrees.
- Regenerated `degree_aliases.csv` (7,593 entries), `degree_dictionary.json`, and `education_seed.json`.

---

### Attribution

| Contributor | Contribution |
|---|---|
| **Jai Gupta** | Data engineering — authored all 8 files in `data/` including the three international training CSV sets, the layered training datasets, the expanded SQL seeds, the canonical catalog, and the manifest |
| **Arnav** | Integration — connected the new dataset folder to the project, fixed the RapidFuzz `**kwargs` bug, added medical degrees to the dictionary, created `evaluate_datasets.py`, tidied all CLI tables, updated all documentation |

---

### Files Changed in v3.5.0

| File | Change |
|---|---|
| `data/` | **New folder** — 8 dataset files + SQL sub-directory (Jai Gupta) |
| `poc/normalizer_rapidfuzz.py` | Bug fix — `_combined_score` now accepts `**kwargs` |
| `data/degree_aliases.csv` | Regenerated — 7,593 entries (added medical degrees) |
| `data/degree_dictionary.json` | Regenerated — added MBBS, BDS, BPHARM |
| `data/education_seed.json` | Regenerated — reflects new canonical set |
| `README.md` | Updated — v3.5.0 directory structure, data extensibility, dataset table |
| `CHANGELOG.md` | Added v3.5.0 entry |
| `explainme.md` | Updated — dataset context, international scope note |
| `platform_audit.md` | Updated — v3.5.0 status, dataset audit section |
| `ppt_generation_prompt.md` | Updated — slide content reflecting new dataset milestone |
| `poc/evaluate_datasets.py` | **New** — Dataset evaluation runner for all training CSVs |
| `poc/app.py` | Tidied — consistent column widths and Unicode separators in CLI tables |
| `poc/normalizer_rapidfuzz.py` | Tidied — consistent CLI table output formatting |
| `poc/normalizer_tfidf.py` | Tidied — consistent CLI table output formatting |
| `poc/normalizer_embeddings.py` | Tidied — consistent CLI table output formatting |
| `poc/engine_l2_combined.py` | Tidied — consistent CLI table output formatting |
| `poc/engine_l3.py` | Tidied — consistent CLI table output formatting |
| `poc/engine_orchestrator.py` | Tidied — consistent CLI table output formatting |

---

## Version 3.0.0 — 22 June 2026


### What's New

**Major architecture release** — the normalisation pipeline is now a complete, production-grade 3-layer system with consensus voting, a fully-implemented Layer 3 heuristic engine, a master orchestrator with selectable operating modes, and a unified interactive CLI that replaces the FastAPI server. 7 files modified, 3 new engine files created, FastAPI removed.

---

### 1. Layer 2 Combined Engine — Consensus Voting (`engine_l2_combined.py`) [NEW]

- Runs all three Layer 2 sub-engines (RapidFuzz, TF-IDF, Embeddings) in parallel.
- Each engine casts a **weighted vote** for its top canonical match:
  - RapidFuzz: base weight `0.35`, TF-IDF: `0.30`, Embeddings: `0.35`
  - Vote weight = `engine_base_weight × confidence_score`
- The canonical name with the highest total vote weight wins.
- **Consensus bonus**: when ≥2 engines agree, confidence is boosted by +0.05 (capped at 1.0).
- Degrades gracefully — if `sentence-transformers` is not installed, Embeddings is skipped and weights re-normalise automatically.
- Returns full `engine_detail` breakdown showing what each sub-engine reported.

---

### 2. Layer 3 NLP/Heuristic Engine (`engine_l3.py`) [NEW]

- **Replaces the L3 stub** with a fully-implemented, pure-Python heuristic cascade (zero ML dependencies).
- Four strategies applied in priority order:

| Strategy | Description | Confidence |
|----------|-------------|------------|
| S2 Shortcode Expansion | 50+ hard-coded abbreviations (BCA, PGDM, LLB, 12th…) → canonical | 0.80 |
| S1 Sentence Extraction | Regex patterns pull degree mentions from natural language | 0.60–0.72 |
| S3 Level Keyword Detection | Maps keywords (bachelor, master, phd…) to a degree level | 0.50 |
| S4 Field-Only Inference | Detects field of study when no degree level is identifiable | 0.35 |

- Can now handle inputs like: _"I completed my B.Tech in Computer Science from IIT Delhi in 2022"_, _"She holds a diploma in Electrical Engineering"_.

---

### 3. Master Orchestrator Engine (`engine_orchestrator.py`) [NEW]

- Full L1 → L2 → L3 pipeline with **three selectable operating modes**:

| Mode | L2 Engines Active | L3 | Latency |
|------|-------------------|-----|---------|
| `fast` | RapidFuzz only | No | ~1–5 ms |
| `standard` | RapidFuzz + TF-IDF | No | ~2–6 ms |
| `full` | All three + L3 heuristic | Yes | ~50–120 ms |

- Per-layer **audit trail** with timing breakdowns, engine votes, and decision rationale.
- Cross-engine comparison utility: `compare_all_engines()` runs every sub-engine independently and returns a structured side-by-side report.

---

### 4. RapidFuzz Scorer Fix — Superset Bias Eliminated

**Bug**: `fuzz.token_set_ratio` alone scored 100 for any input that was a token-subset of a long canonical name. This caused `"Bachelor of Business Admin"` to match `Bachelor of Business Administration` (correct), but also caused many shorter unrelated inputs to be absorbed by long canonical names.

**Fix**: Replaced single-scorer approach with a **weighted combined scorer**:
```
combined_score = token_set_ratio × 0.65 + token_sort_ratio × 0.35
```
`token_sort_ratio` penalises large length mismatches, preventing short inputs from scoring 100 against very long canonicals purely via subset containment.

**Result:**
| Input | v2.3 Result | v3.0 Result |
|---|---|---|
| `Bachelor of Business Admin` | Inconsistent / Error ❌ | Bachelor of Business Administration ✅ |
| `Bacheler of Technology` | Bachelor of Business Administration ❌ | Bachelor of Technology ✅ |
| `BBA` | Review needed (low confidence) ⚠️ | Bachelor of Business Administration ✅ (via L1) |

---

### 5. Field-Split Regex Fix — `\bin\b` → `\s+in\s+`

**Bug**: The `\bin\b` word-boundary regex in `clean()` was splitting on the substring "in" inside words like `Admin`, `Administration`, `Engineering`, `Business`, causing incorrect field extraction and broken degree strings.

**Fix**: Replaced `\bin\b` with `\s+in\s+` across all three standalone engines. This requires "in" to be surrounded by whitespace (a standalone preposition), not embedded inside another word.

---

### 6. FastAPI Server Removed — Unified CLI POC (`app.py`)

- **Removed**: `FastAPI`, `uvicorn`, `pydantic` dependencies and the REST API wrapper.
- **Added**: Rich interactive CLI application that provides unified access to all engines:
  - Engine selection: [A+B1] RapidFuzz, [B2] TF-IDF, [B3] Embeddings, [C] L2-Combined, [D] Orchestrator
  - Per-engine sub-menu: test suite, custom input, batch CSV processing (with optional output save), cross-engine comparison
- `requirements.txt` updated: FastAPI/uvicorn/pydantic removed; install tiers documented (minimum / standard / full).

---

### 7. Documentation Overhaul

- **`README.md`**: Complete rewrite — architecture diagram (ASCII art), updated directory structure, new engine reference table, quick-start guide with install tiers, key bug-fixes table.
- **`explainme.md`**: Updated for v3.0.0 — added Engine C (Combined), documented L3 heuristic cascade with strategy/confidence table, added orchestrator modes table, updated recommendation.
- **`requirements.txt`**: Removed FastAPI/uvicorn/pydantic; added install-tier comments (minimum / standard / full); marked sentence-transformers/torch as optional-heavy.
- **`CHANGELOG.md`**: This entry.

---

### 8. Cross-Engine Structural Consistency

All five engine files now share:
- Identical `_clean_token()` static method with the `\s+in\s+` fix.
- Identical `clean()` method (degree/field separator logic).
- Consistent result dict structure: `input`, `canonical_degree`, `canonical_field`, `confidence`, `status`, `layer_used`, `fuzzy_score`, `alternatives`, `engine`.
- `ENGINE_ID` class constant on each engine for audit/tracing.
- Graceful import guards and error handling (never raises to caller).

---

### Files Changed in v3.0.0

| File | Change |
|---|---|
| `poc/engine_l2_combined.py` | **New** — Layer 2 consensus voting engine |
| `poc/engine_l3.py` | **New** — Layer 3 NLP/heuristic cascade (4 strategies) |
| `poc/engine_orchestrator.py` | **New** — Master 3-layer orchestrator (3 modes) |
| `poc/app.py` | **Rewritten** — FastAPI removed; unified interactive CLI POC |
| `poc/normalizer_rapidfuzz.py` | Combined scorer fix, `\s+in\s+` regex fix, L3 stub improved |
| `poc/normalizer_tfidf.py` | `\s+in\s+` regex fix, engine ID, structural polish |
| `poc/normalizer_embeddings.py` | `\s+in\s+` regex fix, engine ID, graceful import guard |
| `README.md` | Complete rewrite — architecture diagram, engine table, install tiers |
| `explainme.md` | Updated — Engine C, L3 strategies, orchestrator modes |
| `requirements.txt` | Removed FastAPI deps; added install-tier documentation |
| `CHANGELOG.md` | Added v3.0.0 entry |

---

## Version 2.3.0 — 20 June 2026

### What's New

Comprehensive project audit and polish pass — 10 files modified/created across code, data, documentation, and project structure. Fixes 4 critical issues, 5 high-priority items, and 3 polish improvements.

---

### 1. SQL Seed File — Complete Rewrite (`education_seed.sql`)
- **Previously**: Only created tables and seeded `qualification_levels` (7 rows). The `qualification_canonical`, `qualification_aliases`, `field_of_study`, and `candidate_education` tables were **empty** — unusable as a handoff artifact.
- **Now**: Full seed file with:
  - 19 canonical degree INSERTs with foreign key references to levels
  - 68 field of study INSERTs with category and JSON alias arrays
  - 27 representative alias INSERTs (sample subset; full 6,980+ set in CSV)
  - 3 sample candidate education records demonstrating resolved, fuzzy_matched, and unresolved statuses
  - Proper `FOREIGN KEY` constraints, `INDEX` definitions, and `ENUM` types
  - Header/footer comments with bulk-import guidance

---

### 2. PGDM Mapping Collision Fixed (`generate_data.py`)
- **Bug**: `PGDM` was mapped to **both** `Master of Business Administration` and `Post Graduate Diploma` in the degree alias generator. Whichever appeared last in the CSV would win silently.
- **Fix**: Removed `PGDM` from MBA aliases. PGDM now exclusively maps to `Post Graduate Diploma` (which is the correct classification — PGDM is a diploma, not an MBA).
- Also replaced 24 nonsensical typo aliases (`"Tecnology of Technology"`, `"Master Bacheler"`, etc.) with **25 realistic Indian resume misspellings** (`"Bacheler of Technology"`, `"Batchelor of Technology"`, `"Master of Sciance"`, etc.).

---

### 3. API Improvements (`app.py`)
- **HTTP 404 → 422**: Unresolved normalization requests now return `422 Unprocessable Entity` instead of `404 Not Found` (semantically correct).
- **CORS middleware**: Added `CORSMiddleware` with open origins for development use.
- **Health endpoint**: New `GET /health` returns service status + loaded dictionary sizes.
- **Version bump**: API version string updated from `2.0.0` → `2.2.0` to match CHANGELOG.
- Added module-level docstring.

---

### 4. Interactive CLIs for All Normalizers
- `normalizer_tfidf.py` and `normalizer_embeddings.py` previously had a single hardcoded test line in their `__main__` blocks. Both now have **full interactive menus** matching the RapidFuzz normalizer's 3-option CLI (run default test suite / enter custom string / exit).
- Module-level docstrings added to all four PoC files (`normalizer_rapidfuzz.py`, `normalizer_tfidf.py`, `normalizer_embeddings.py`, `app.py`).
- Removed unused `import time` and duplicate `import os` from `normalizer_rapidfuzz.py`.

---

### 5. Documentation Fixes
- **README.md**: Fixed phantom directory references (`report/` → `reports/`, removed deleted `presentation/` dir), updated file descriptions to match actual contents, added `requirements.txt` reference, added project metadata header.
- **CHANGELOG.md**: Normalized version format to consistent 3-segment semver (`v2.0` → `v2.0.0`, `v1.0` → `v1.0.0`). Fixed stale `poc/normalizer.py` reference → `poc/normalizer_rapidfuzz.py`.
- **explainme.md**: Added closing separator and cross-reference links to README and CHANGELOG.

---

### 6. New Files
- **`requirements.txt`**: Python dependency manifest with version pins and per-script annotations. Supports lightweight install (RapidFuzz only) and full install (all engines).
- **`ppt_generation_prompt.md`**: Comprehensive 22-slide presentation generation brief with slide-by-slide content, layout specs, design guidelines, data tables, diagrams, and presenter notes.

---

### Files Changed in v2.3.0

| File | Change |
|---|---|
| `data/education_seed.sql` | Complete rewrite — now a functional seed file |
| `poc/app.py` | HTTP 422, CORS, /health, docstring, version bump |
| `poc/normalizer_rapidfuzz.py` | Docstring, removed unused imports |
| `poc/normalizer_tfidf.py` | Docstring + full interactive CLI |
| `poc/normalizer_embeddings.py` | Docstring + full interactive CLI |
| `README.md` | Fixed directory refs, added requirements.txt, metadata header |
| `CHANGELOG.md` | Semver normalization, stale reference fix, v2.3.0 entry |
| `explainme.md` | Cross-reference links, trailing separator |
| `requirements.txt` | **New** — Python dependency manifest |
| `ppt_generation_prompt.md` | **New** — 22-slide PPT generation brief |

*Also changed (outside repo):*
| `../generate_data.py` | PGDM collision fix, realistic typo aliases |

---

## Version 2.2.0 — 16 June 2026

### What's New

Restructured project documentation to present the normalisation pipeline as **three distinct, named deployment versions** (Version A / B / C) per Roadmap V2 requirements, enabling Growth Grids to evaluate and select a specific option.

---

### 1. Pipeline Options Decision Brief (`explainme.md` — Rewritten)
- Replaced the previous Layer 2 framework explainer with a comprehensive **Growth Grids Decision Brief**.
- Each version (A: Lookup Only, B: Lookup + Fuzzy, C: Full 3-Layer) now has its own section with:
  - Active layers table
  - Technical profile (latency, dependencies, infrastructure cost)
  - "When To Pick This" guidance and limitations
- Version B includes three interchangeable **Layer 2 engine sub-options** (B-1: RapidFuzz, B-2: TF-IDF, B-3: Embeddings) with per-engine specs.
- Added a **Decision Matrix** table for side-by-side comparison across all criteria.
- Added a formal **Recommendation** section (Version B with RapidFuzz as default).
- Original Layer 2 comparison table preserved in the Appendix.

---

### 2. README Deployment Section (Enhanced)
- Replaced the prose-based "Implementation Notes" section with a compact **decision matrix table**.
- Added a cross-reference link to the full decision brief in `explainme.md`.

---

### Files Changed in v2.2.0

| File | Change |
|---|---|
| `explainme.md` | Rewritten — now serves as the Growth Grids Pipeline Options Decision Brief |
| `README.md` | Deployment Options section replaced with decision matrix + cross-reference |
| `CHANGELOG.md` | Added v2.2.0 entry |

---

## Version 2.1.0 — 16 June 2026

### What's New

This version introduces a production-ready headless REST API wrapper and implements alternative algorithmic frameworks for **Layer 2 Fuzzy Matching**. 

---

### 1. Headless REST API Integration (`app.py`)
- Created [app.py](file:///c:/Users/arnav/Downloads/CV_SIP/cv_manager_sip/poc/app.py) to wrap the normalization logic using **FastAPI** and **Uvicorn**.
- Migrated code schema validation structures to **Pydantic V2** (`model_config` and `json_schema_extra` syntax).
- Created a single-string normalization endpoint (`POST /api/v1/normalize`) and a batch processing endpoint (`POST /api/v1/normalize/batch`).

---

### 2. Alternative Layer 2 Fuzzy Match PoCs
Exposed alternative fuzzy entity-resolution models to evaluate performance tradeoffs relative to the original RapidFuzz implementation:
- **Character N-Gram Cosine Similarity PoC** ([normalizer_tfidf.py](file:///c:/Users/arnav/Downloads/CV_SIP/cv_manager_sip/poc/normalizer_tfidf.py)): Uses `TfidfVectorizer(analyzer='char', ngram_range=(3, 5))` to index choices and resolve inputs via cosine similarity.
- **Dense Vector Semantic Embeddings PoC** ([normalizer_embeddings.py](file:///c:/Users/arnav/Downloads/CV_SIP/cv_manager_sip/poc/normalizer_embeddings.py)): Employs Sentence-Transformers (`all-MiniLM-L6-v2`) to represent degree meanings and matches them via dot products.
- Renamed the core Levenshtein distance module from `normalizer.py` to `normalizer_rapidfuzz.py`.

---

### 3. Layer 2 Match Framework Comparison

| Metric | RapidFuzz (Levenshtein) | TF-IDF (Char N-Gram) | Sentence-Transformers (Dense Embeddings) |
|---|---|---|---|
| **Mechanism** | String token set / edit distance | Sparse frequency cosine similarity | Dense vector transformer embeddings |
| **Execution Speed** | Fast (~1-5ms / query) | Extremely Fast (<1ms / query) | Slow (~50-100ms / query on CPU) |
| **Typo Resilience** | High (handles letters swaps/omissions) | High (n-gram subword matching) | Moderate (typos warp semantic embeddings) |
| **Semantic Matching** | Low (struggles with "B.S." vs "B.Sc.") | Low (depends on string characters) | Extremely High (interprets conceptual meaning) |
| **Infrastructure Needs**| Minimal (pure C/Python package) | Minimal (scikit-learn dependency) | High (requires PyTorch + Sentence-Transformers) |

---

### 4. SWOT / Strategic Analysis of Layer 2 Frameworks

```
                       STRENGTHS                                               WEAKNESSES
┌───────────────────────────────────────────────────────┐┌───────────────────────────────────────────────────────┐
│ • TF-IDF: Sub-millisecond latency; highly scalable.   ││ • TF-IDF/RapidFuzz: Completely blind to semantic      │
│ • RapidFuzz: Typos / letter transpositions handled.   ││   meanings ("B.S." and "Bachelor of Science" score    │
│ • Embeddings: Resolves conceptual aliases natively.   ││   poorly without explicit maps).                      │
│                                                       ││ • Embeddings: Requires large PyTorch CPU/GPU memory. │
└───────────────────────────────────────────────────────┘└───────────────────────────────────────────────────────┘
                       OPPORTUNITIES                                            THREATS
┌───────────────────────────────────────────────────────┐┌───────────────────────────────────────────────────────┐
│ • Hybrid Scoring: Combined TF-IDF character matching  ││ • Latency SLA: Dense Embeddings model might block     │
│   with Vector Embeddings for perfect precision.       ││   high-throughput batch uploads if CPU bound.         │
│ • API Scaling: Exposing headless microservices via    ││ • Out-of-Vocabulary: Completely novel slang words may │
│   FastAPI enables language-agnostic integrations.    ││   cause false positives in semantic models.           │
└───────────────────────────────────────────────────────┘└───────────────────────────────────────────────────────┘
```

---

### 5. Roadmap V2: Distinct Deployment Options
As per the Roadmap V2 specifications, the normalization pipeline has been packaged and documented as three distinct alternatives for Growth Grids to select based on their infrastructure and accuracy needs:
*   **Option A (Lookup Only)**: Strictly uses Layer 1. Maximum speed, lowest infrastructure cost, zero typo-tolerance.
*   **Option B (Lookup + Fuzzy)**: Uses Layer 1 and Layer 2. Balances speed and accuracy. Catches typos and aliases. (Recommended).
*   **Option C (Full 3-Layer)**: Uses Layer 1, Layer 2, and Layer 3 (NLP). Highest accuracy, capable of parsing conversational text, but requires heavy ML infrastructure.

---

## Version 2.0.0 — 15 June 2026

### What's New

This version represents a major upgrade to the normalisation engine and the underlying
reference data. The focus was on improving Layer 1 and Layer 2 accuracy, expanding the
alias dataset, and introducing a structured degree dictionary.

---

### 1. Layer 1 — Exact Match Engine (Upgraded)

**Problem in v1:** The text cleaner only handled parentheses and the keyword `in` as
field separators. Strings like `B.Tech - Computer Science`, `B.Tech, CSE` or `BE/CSE`
would not extract the field correctly, and the degree portion would fail exact matching.

**Fix in v2:**
- Replaced the basic `clean()` regex with a multi-stage parser that handles **four
  structural separators** as field extractors:
  - ` - ` (dash-separated)
  - ` / ` (slash-separated)
  - ` in ` (keyword-separated)
  - ` , ` (comma-separated)
  - `( )` (parentheses)
- Added `clean_alias_string()` as a shared normalisation helper so that both input
  strings and dictionary keys are cleaned using **exactly the same logic**, eliminating
  tokenisation mismatches.

---

### 2. Layer 2 — Fuzzy Match Engine (Upgraded)

**Problem in v1:** The fuzzy matcher (RapidFuzz) only compared inputs against the 19
strict canonical degree names (e.g., `"Bachelor of Science"`). With so few options and
the use of `fuzz.WRatio`, it was incorrectly returning `Bachelor of Business
Administration` for inputs like `"Bacelor of sci"` — because `WRatio` rewarded a
longer partial substring match over a more semantically correct short match.

**Fix in v2:**
- **Changed scorer** from `fuzz.WRatio` to `fuzz.token_set_ratio`. Token set ratio
  focuses on *token overlap* rather than substring length, correctly scoring "sci" as
  a match for "Science".
- **Expanded match target** from 19 canonical strings to the full **7,000+ alias
  dictionary**. Layer 2 now fuzzy-matches against every known alias permutation,
  meaning `"Bacelor of sci"` is now correctly scored against the known alias
  `"bachelor of sci"` from the dictionary.
- De-duplication logic added to the alternatives list to ensure you see distinct
  canonical suggestions, not repeated aliases of the same degree.
- Adjusted thresholds: `auto-accept` = 88, `flag-for-review` = 70 (tuned for the new scorer).

**Result:**
| Input | v1 Result | v2 Result |
|---|---|---|
| `Bacelor of sci` | Bachelor of Business Administration ❌ | Bachelor of Science ✅ |
| `Basherlo of SCience` | Bachelor of Business Administration ❌ | Bachelor of Science ✅ |
| `PGDBM` | Unresolved ❌ | Post Graduate Diploma ✅ |

---

### 3. Data Expansion — Permutation & Combination Engine (New)

**Problem in v1:** The `degree_aliases.csv` was generated with a limited set of
hand-crafted aliases (~600 entries). Many valid combinations like `B.Tech (Mechanical
Engineering)` or `BE - Civil Engineering` would have to fall through to the fuzzy Layer 2.

**Fix in v2:**
- Added a **permutation generation block** to `generate_data.py` that programmatically
  combines every known degree alias with every valid field of study using five common
  structural connectors.
- This expanded the alias dictionary from **~600 to 6,983 entries**.
- Layer 1 exact match now catches combinations that previously required fuzzy matching.

---

### 4. Degree Dictionary — `degree_dictionary.json` (New File)

A new structured JSON file has been introduced as a **maintained canonical dictionary**
of all degree types in the system.

**Structure:**
```json
{
  "Bachelor of Technology": {
    "level": "UG ENGINEERING",
    "short_code": "BTECH",
    "aliases": ["BTech", "B.Tech", "B. Tech", "BTECH", ...]
  },
  ...
}
```

**Purpose:**
- Serves as the **primary lookup table** for the normaliser. At startup, the engine
  detects and loads `degree_dictionary.json` before falling back to the CSV.
- Acts as a **handoff document** for the Growth Grids dev team — they can directly
  import this into their database seed or use it to populate their canonical degrees table.
- Keeps `degree_aliases.csv` intact for SQL seed purposes (the two files complement
  each other, neither replaces the other).

---

### 5. Auxiliary Sources Integration (v1.5 → v2)

In the previous session, `auxilary_sources/field_of_study.py` was identified as a
much more comprehensive and curated data source than the auto-generated mock data.

- `field_of_study_aliases.csv` was regenerated using this script: **68 UGC-recognised
  canonical fields** across **308 exact aliases**.
- `degree_field_map.csv` regenerated with **186 UGC-compliant degree-field pairings**.
- `full_education_reference.csv` added as a combined reference table (useful for UI
  drop-down population).
- The `field_of_study.py` script was patched from hardcoded Linux paths to local
  Windows paths and is now rerunnable from within the project.

---

### Files Changed in v2

| File | Change |
|---|---|
| `poc/normalizer_rapidfuzz.py` | Layer 1 regex overhaul + Layer 2 scorer swap + JSON dict loading |
| `data/degree_aliases.csv` | Expanded from ~600 → 6,983 entries |
| `data/degree_dictionary.json` | **New** — Structured canonical degree dictionary |
| `data/education_seed.json` | Updated to reflect new permutation data |
| `auxilary_sources/field_of_study.py` | Patched paths for Windows compatibility |
| `data/field_of_study_aliases.csv` | Regenerated from curated auxiliary source |
| `data/degree_field_map.csv` | Regenerated from curated auxiliary source |
| `data/full_education_reference.csv` | **New** — Combined degree × field reference |

---

## Version 1.0.0 — 13 June 2026

### Initial Deliverables

- **`data/degree_aliases.csv`** — 576 degree name alias pairs (manual + auto-generated)
- **`data/field_of_study_aliases.csv`** — 308 field alias pairs
- **`data/degree_field_map.csv`** — 186 valid degree-field combinations
- **`data/education_seed.sql`** — 5-table relational schema + seed INSERT statements
- **`data/education_seed.json`** — JSON export of aliases and sample candidates
- **`poc/normalizer.py`** — 3-layer normalisation engine (L1 exact, L2 fuzzy, L3 stub)
- **`report/final_report.docx`** — Full written report
- **`presentation/presentation.pptx`** — 15-slide presentation deck

### Architecture (Established in v1)
- **Layer 1:** Exact dictionary lookup after cleaning (dots, spaces, case)
- **Layer 2:** RapidFuzz string similarity against canonical degree names
- **Layer 3:** Rule-based stub (NLP/NER deferred to future sprint)
- **CLI Interface:** Interactive menu for testing single inputs or running default test suite

---

*This file is maintained as part of the SIP deliverables.*
