# CHANGELOG — CV Manager Qualification Normalizer

> **Project:** CV Manager — Qualification Standardization (SIP)  
> **Organisation:** Growth Grids × University of Southampton Delhi  
> **Deadline:** 3 July 2026

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
