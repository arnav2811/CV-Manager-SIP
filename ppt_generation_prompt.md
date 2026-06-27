# PPT Generation Prompt — CV Manager Qualification Standardization (SIP)

> **Version**: v3.6.0 — Updated 27 June 2026  
> **Use this prompt** to generate a professional 25-slide PowerPoint presentation for the Growth Grids Summer Internship Project. Use it as a slide-by-slide brief for manual creation or for a presentation-building tool.

---

## Global Design Brief

### Visual Identity
- **Theme**: Clean, modern, corporate-tech. Dark navy (#1B2A4A) backgrounds with white (#FFFFFF) and accent teal (#00BFA6) text.
- **Fonts**: Headings in **Poppins Bold** or **Montserrat Bold**. Body text in **Inter** or **Open Sans** at 16–20pt minimum.
- **Accent Colours**: Teal (#00BFA6) for highlights, amber (#FFB300) for warnings/review items, soft green (#66BB6A) for resolved/success, coral (#EF5350) for unresolved/errors.
- **Layout**: 16:9 widescreen. Generous whitespace. No walls of text — aim for ≤6 bullet points per content slide.
- **Iconography**: Use flat/line icons (Material Design style) for pipeline layers, data tables, and architecture diagrams.
- **Charts/Tables**: Use the colour palette consistently. Tables should have alternating row shading.
- **Branding**: Include a subtle "Growth Grids × University of Southampton Delhi" footer on every slide. Slide numbers in bottom-right.

### Tone
- Professional but accessible — the audience includes both technical developers and non-technical management (Dr. Rashi R. Sharma, Growth Grids leadership).
- Tell a story: Problem → Analysis → Solution → Proof → Recommendation.
- Use data to back every claim.

---

## SLIDE-BY-SLIDE CONTENT

---

### SLIDE 1 — Title Slide

**Layout**: Full-bleed dark background with centred text.

**Content**:
- **Title**: CV Manager — Qualification Standardization
- **Subtitle**: Summer Internship Project (SIP) — Final Presentation
- **Organisation**: Growth Grids × University of Southampton Delhi
- **Date**: July 2026
- **Team**: Arnav · Jai Gupta · Himanshi Kaushik · Keshav Singhal
- **Mentor**: Dr. Rashi R. Sharma

**Design Notes**: Large title, clean logo placement. No clutter.

---

### SLIDE 2 — Agenda / Roadmap

**Layout**: Numbered vertical timeline or horizontal stepper.

**Content** (section titles only):
1. The Problem
2. Why It Matters
3. CV Manager — Current State
4. Competitor Landscape
5. Our Solution — 3-Layer Pipeline
6. Layer 1: Dictionary Lookup
7. Layer 2: Fuzzy Matching — Engine Options
8. Layer 2: Engine C — Consensus Voting (NEW)
9. Layer 3: NLP/Heuristic Extraction (Fully Implemented)
10. The Data Model
11. The Alias Dictionary — By the Numbers
12. International Training Datasets (NEW v3.5.0)
13. F1 Scoring & Evaluation Results (NEW v3.6.0)
14. Deployment Options (A / B / C)
15. Proof of Concept — Unified CLI Demo
16. Results & Pipeline Performance
17. Bug Fixes & Engine Improvements (v3.0.0 + v3.6.0)
18. Data Formats & Extensibility
19. SWOT Analysis
20. Implementation Roadmap
21. Recommendations
22. Q&A

**Design Notes**: Use a progress-bar or stepper visual. Keep it scannable.

---

### SLIDE 3 — The Problem

**Layout**: Two-column. Left = problem description. Right = visual table of variations.

**Content**:

**Heading**: "One Degree, Fifty Names"

**Left column** (3 bullet points):
- Candidates write their education qualification in wildly inconsistent formats on resumes
- Recruiters searching for "B.Tech" miss candidates who wrote "Bachelor of Technology", "BTech", or "BE"
- The same problem exists for fields of study: CSE vs Computer Science vs Comp Science

**Right column** — Visual table:
```
B.Tech          BTech           Bachelor of Technology
B. Tech         BTECH           B.Tech (Hons)
B.Tech.         B.E.            Bacheler of Technology  ← typo
BE              BEng            4-Year B.Tech
```
All of these mean the **same thing**.

**Key stat callout**: "A recruiter search returns only ~40% of matching candidates without normalization."

---

### SLIDE 4 — Why This Matters

**Layout**: Three KPI cards + one paragraph.

**Content**:

**Heading**: "The Business Impact"

**KPI Card 1**: 🔍 **Search Accuracy** — Recruiters miss 60%+ of relevant candidates when searching by degree
**KPI Card 2**: ⏱️ **Time Wasted** — Manual screening of non-standardized data adds hours per search
**KPI Card 3**: 💰 **Revenue Impact** — Missed candidates = missed placements = lost revenue

**Bottom paragraph**: "Qualification normalization is not a nice-to-have — it is a prerequisite for any recruiter search feature to function correctly. Without it, the search is fundamentally broken."

---

### SLIDE 5 — CV Manager — Current State Assessment

**Layout**: Left = screenshot/mockup of CV Manager dashboard. Right = severity table.

**Content**:

**Heading**: "Where CV Manager Stands Today"

**Issues found** (severity table):

| Severity | Issue |
|----------|-------|
| 🔴 Critical | CV parser does not extract degree-level data as structured fields |
| 🔴 Critical | Dashboard stats broken — shows 0 despite uploaded CVs |
| 🟡 High | Location filter non-functional |
| 🟡 High | Analytics widgets empty |
| 🟡 High | No ATS pipeline, no bulk upload, no job posting module |
| 🟢 Medium | Search relies on raw text matching, no canonicalization |

**Callout**: "The search fundamentally cannot work without structured, normalized education data."

---

### SLIDE 6 — Competitor Landscape

**Layout**: Feature comparison matrix (table with green ✅ / red ❌ cells).

**Content**:

**Heading**: "How the Market Handles This"

| Feature | Naukri | LinkedIn | Foundit | Apna | Indeed | **CV Manager** |
|---------|--------|----------|---------|------|--------|---------------|
| Structured Education Fields | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ❌ |
| Degree Normalization | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Fuzzy/AI Matching | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| Boolean Search on Education | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| Bulk CV Upload & Parse | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Resume Database Size | 7.83 Cr | 100M+ | 5 Cr+ | 5 Cr+ | — | Early stage |

**Key insight callout**: "Naukri (62–70% market share) and LinkedIn both normalize education data at ingestion. This is table stakes."

**Source note**: Market data from respective platform annual reports, 2024–2025.

---

### SLIDE 7 — Our Solution — The 3-Layer Pipeline (Overview)

**Layout**: Vertical flowchart diagram — the centrepiece slide.

**Content**:

**Heading**: "A Three-Layer Normalization Pipeline"

**Flow diagram** (top to bottom):
```
          ┌──────────────────┐
          │   RAW CV TEXT     │
          │ "Bacheler of Tech"│
          └────────┬─────────┘
                   ▼
    ┌──────────────────────────────┐
    │  LAYER 1 — EXACT LOOKUP     │  ~85% of inputs resolved here
    │  Hash-map against 6,980+    │  Latency: ~0ms
    │  pre-computed aliases       │  Confidence: 1.00
    └───────┬──────────┬──────────┘
        MATCHED     NOT MATCHED
            │              │
            ▼              ▼
      ✅ Resolved   ┌──────────────────────────────┐
                    │  LAYER 2 — FUZZY MATCHING    │  ~12% resolved
                    │  RapidFuzz / TF-IDF /        │  Latency: 1–100ms
                    │  Sentence-Transformers       │  Confidence: 0.70–0.99
                    └──────┬──────────┬────────────┘
                        ≥88%        <70%
                           │           │
                     ✅ Auto-Accept   ⚠️ Review Queue
                           │           │
                           ▼           ▼
                     ┌──────────────────────────────┐
                     │  LAYER 3 — NLP/HEURISTIC     │  ~3% edge cases
                     │  4-Strategy pure-Python      │  For conversational text
                     │  cascade (zero ML deps)      │  Conf: 0.35–0.80
                     └──────────────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  CANONICAL OUTPUT       │
                    │  degree: "Bachelor of   │
                    │           Technology"   │
                    │  field:  "Computer Sci  │
                    │           & Engg"       │
                    │  confidence: 0.91       │
                    └─────────────────────────┘
```

---

### SLIDE 8 — Layer 1: Exact Dictionary Lookup

**Layout**: Left = algorithm steps. Right = worked example.

**Content**:

**Heading**: "Layer 1 — Rule-Based Lookup"

**Algorithm** (numbered steps):
1. Take raw input: `"B.Tech (CSE)"`
2. Extract field if in parentheses → field = `"CSE"`
3. Clean degree part: lowercase, strip dots/spaces → `"btech"`
4. Lookup `"btech"` in alias dictionary (hash-map, O(1))
5. **Match found** → `"Bachelor of Technology"`, confidence = 1.00

**Worked example box** (visual):
```
Input:    "B. Tech in Computer Science"
Clean:    "b tech" + field: "Computer Science"
Lookup:   degree_aliases["b tech"] → "Bachelor of Technology" ✅
          field_aliases["computer science"] → "Computer Science and Engineering" ✅
Output:   Resolved | L1 | Confidence 1.00
```

**Stats callout**: "6,980+ aliases covering 19 canonical degrees. Handles dots, spaces, Hons, slashes, dashes, commas, and parenthetical fields."

---

### SLIDE 9 — Layer 2: Fuzzy String Matching

**Layout**: Split — top half = mechanism, bottom half = scored example.

**Content**:

**Heading**: "Layer 2 — Catching Typos & Variations"

**Mechanism** (3 bullets):
- Input that fails Layer 1 is compared against all 6,980+ known aliases using `fuzz.token_set_ratio`
- Token set ratio focuses on **token overlap** rather than substring length — handles word reordering and character transpositions
- Decision: score ≥ 88 → auto-accept | 70–87 → flag for review | < 70 → unresolved

**Worked example** (visual table):

| Input | Best Match | Score | Decision |
|-------|-----------|-------|----------|
| `"Bacheler of Technology"` | `"bachelor of technology"` | 91 | ✅ Auto-accept |
| `"Basherlo of SCience"` | `"bachelor of science"` | 88 | ✅ Auto-accept |
| `"PGDBM"` | `"pgdbm"` → Post Graduate Diploma | 100 | ✅ Auto-accept |
| `"B.Pharma"` | `"b pharma"` | 72 | ⚠️ Review needed |
| `"Kuchh bhi degree"` | — | 34 | ❌ Unresolved |

**v1 → v2 improvement callout**:
- v1 compared against only 19 canonical names → wrong matches
- v2 compares against 6,980+ aliases → correct matches

---

### SLIDE 10 — Layer 2: Engine Options Comparison

**Layout**: Four-column comparison cards (add Engine C).

**Content**:

**Heading**: "Four Interchangeable Fuzzy Engines"

**Card 1 — RapidFuzz (B-1)**
- Mechanism: Combined scorer: `token_set_ratio×0.65 + token_sort_ratio×0.35`
- Speed: ~1–5 ms/query
- Typo handling: ✅ Excellent
- Synonym handling: ❌ Poor
- Dependency: `rapidfuzz` (lightweight, pure C)

**Card 2 — TF-IDF (B-2)**
- Mechanism: Character 3–5-gram cosine similarity
- Speed: <1 ms/query (fastest)
- Typo handling: ✅ Excellent
- Synonym handling: ❌ Poor
- Dependency: `scikit-learn`

**Card 3 — Embeddings (B-3)**
- Mechanism: MiniLM neural network, 384-dim dense vectors
- Speed: ~50–100 ms/query
- Typo handling: ⚠️ Moderate
- Synonym handling: ✅ Excellent ("B.S." → "Bachelor of Science")
- Dependency: `torch` + `sentence-transformers` (~90 MB model)

**Card 4 — Combined Engine (C)** ⭐ Recommended (NEW in v3.0.0)
- Mechanism: Weighted consensus vote across B-1 + B-2 + B-3
- Speed: Combined latency (~2–110 ms)
- Typo handling: ✅ Excellent (B-1 + B-2 vote)
- Synonym handling: ✅ Good (Embeddings vote)
- Consensus bonus: +0.05 confidence when ≥2 engines agree
- Graceful degradation: works with only B-1+B-2 if torch not installed

---

### SLIDE 11 — Layer 3: Pure-Python Heuristic Engine (Fully Implemented)

**Layout**: Left = 4-strategy cascade diagram. Right = worked example.

**Content**:

**Heading**: "Layer 3 — Heuristic NLP Extraction (LIVE in v3.0.0)"

**Status badge**: ✅ Fully Implemented — zero ML dependencies

**Four-Strategy Cascade** (shown as numbered steps):

| # | Strategy | What It Does | Confidence |
|---|----------|-------------|------------|
| 1 | **S2 Shortcode Expansion** | 50+ hard-coded abbreviations (BCA, PGDM, LLB, 12th…) → canonical | 0.80 |
| 2 | **S1 Sentence Extraction** | Regex patterns pull degree mentions from full sentences | 0.60–0.72 |
| 3 | **S3 Level Keyword Detection** | Maps keywords (bachelor, master, phd, diploma…) to a degree level | 0.50 |
| 4 | **S4 Field-Only Inference** | Detects field of study even when degree level is unknown | 0.35 |

**Worked example**:
```
Input: "I completed my Masters in Data Science from IIT Delhi"

S2 Shortcode: no match
S1 Sentence:  degree mention → "Masters"
              field mention → "Data Science"
Output: canonical_degree = "Master of Science"
        canonical_field  = "Data Science"
        confidence       = 0.72  |  status = review_needed
```

**All L3 results are flagged `review_needed` by design** — human review closes the loop.

---

### SLIDE 12 — The Data Model (5-Table Schema)

**Layout**: ER diagram filling most of the slide.

**Content**:

**Heading**: "Relational Data Model — 5 Tables"

**ER Diagram** (show relationships with crow's-foot notation):

```
qualification_levels          qualification_canonical
┌──────────────────┐         ┌───────────────────────┐
│ level_id (PK)    │←────────│ level_id (FK)         │
│ level_name       │         │ canonical_id (PK)     │
│ level_rank       │         │ canonical_name        │
└──────────────────┘         │ short_code            │
                             └───────────┬───────────┘
                                         │
                                         ↓
                             qualification_aliases
                             ┌───────────────────────┐
                             │ alias_id (PK)         │
                             │ raw_string            │
                             │ canonical_id (FK)     │
                             │ normalized            │
                             │ source                │
                             │ confidence            │
                             └───────────────────────┘

field_of_study               candidate_education
┌──────────────────┐         ┌───────────────────────┐
│ field_id (PK)    │←────────│ field_id (FK)         │
│ canonical_field  │         │ edu_id (PK)           │
│ category         │         │ candidate_id          │
│ field_aliases    │         │ raw_degree            │
└──────────────────┘         │ raw_field             │
                             │ canonical_id (FK) ────→ qualification_canonical
                             │ institution           │
                             │ graduation_year       │
                             │ cgpa                  │
                             │ parse_status          │
                             │ confidence            │
                             └───────────────────────┘
```

**Key design principle callout**: "Store both raw and canonical. Raw for audit trail, canonical for search. If normalization improves, only the mapping changes — not the underlying data."

---

### SLIDE 13 — The Alias Dictionary — By the Numbers

**Layout**: Large stat cards across the top, sample table below.

**Content**:

**Heading**: "The Alias Dictionary — Our Core Data Asset"

**Stat Cards** (big numbers, colour-coded):
- **22** Canonical Degree Types (incl. MBBS, BDS, BPharm — added v3.5.0)
- **68** Canonical Fields of Study (UGC/AICTE recognised)
- **7,593** Degree Name Aliases (incl. permutations + medical degrees)
- **308** Field of Study Aliases
- **186** Valid Degree × Field Combinations

**Sample table** (4 rows from the dataset):

| Raw String (what candidates write) | Canonical Name (what we store) | Level |
|-------------------------------------|-------------------------------|-------|
| B.Tech, BTech, B. Tech, BTECH, B.Tech (Hons) | Bachelor of Technology | UG Engineering |
| MBA, M.B.A., EMBA | Master of Business Administration | PG Other |
| MBBS, M.B.B.S., MB ChB | Bachelor of Medicine and Bachelor of Surgery | UG Medicine |
| HSC, 10+2, XII, Plus Two, ISC | 12th Standard | School |

**Callout**: "Each alias was manually verified or programmatically generated via a permutation engine combining degree abbreviations × structural connectors (dash, slash, parentheses, comma, keyword 'in')."

---

### SLIDE 12 (NEW — v3.5.0) — International Training Datasets

**Layout**: Header stat bar + two-column table.

**Content**:

**Heading**: "The Training Dataset — Built for the Real World"

**Contributor badge**: 🏗️ **Data Engineering: Jai Gupta** · Integration: Arnav

**Stat Bar** (3 big numbers across the top):
- **59,949** total training rows across all datasets
- **3** international degree systems covered (India · USA · UK · World)
- **3** pipeline layers with dedicated evaluation data

**Per-Layer Dataset Table**:

| Dataset | Rows | Layer | Purpose |
|---------|-----:|-------|----------|
| `layer1_exact_lookup_training.csv` | 6,976 | L1 | Gold-standard dictionary regression tests |
| `layer2_fuzzy_training.csv` | 15,233 | L2 | Noisy aliases with noise-type & difficulty labels for threshold tuning |
| `layer3_unstructured_training.csv` | 1,124 | L3 | Conversational sentence examples with character-span annotations |
| `indian_usa_degrees_training.csv` | 9,448 | Multi | India + USA degree alias permutations (49 canonical entries) |
| `indian_uk_degrees_training.csv` | 9,240 | Multi | India + UK degree alias permutations (43 canonical entries) |
| `indian_world_degrees_training.csv` | 17,913 | Multi | India + USA + UK + world alias permutations (141 canonical entries) |

**Expanded SQL Seeds** (bottom callout):
- USA scope: 218 canonical fields × 84 canonical degrees = **18,312 combinations**
- UK scope: 218 canonical fields × 61 canonical degrees = **13,298 combinations**
- World scope: 348 canonical fields × 179 canonical degrees = **62,292 combinations**
- *Sources: NCES CIP 2020 · HESA HECoS · QAA/UCAS · UNESCO ISCED-F 2013*

**Callout**: "This dataset transforms the pipeline from an India-only proof-of-concept into a globally-scalable normalization system — ready to handle CVs from any international market Growth Grids enters."

---

### SLIDE 13 (NEW — v3.6.0) — F1 Scoring & Evaluation Results

**Layout**: Two-column. Left = workflow steps. Right = F1 result table.

**Content**:

**Heading**: "F1 Scoring — Measuring the Pipeline"

**Contributor badge**: 📊 **F1 Scoring: Himanshi Kaushik** · Support: Keshav Singhal

**Workflow Steps**:
1. Prepare cleaned datasets using `poc/prepare_f1_datasets.py`
2. Run all evaluation datasets using `poc/evaluate_f1.py --dataset all`
3. Review `evaluation/evaluation_summary.csv`
4. Check accuracy, TP/FP/FN, resolution rate, and average latency
5. Use `evaluation/*_failures.csv` and `evaluation/*_confusion.csv` to identify incorrect predictions
6. Confirm CLI path with `poc/smoke_test_cli.py`

**F1 Summary Table**:

| Dataset | Degree F1 | Field F1 | Pair F1 |
|---------|----------:|---------:|--------:|
| Layer 1 | 0.7618 | 0.9134 | 0.6353 |
| Layer 2 | 0.7863 | 0.8312 | 0.5323 |
| Layer 3 | 0.3975 | 0.5153 | 0.1604 |
| India + USA | 0.5393 | N/A | 0.4400 |
| India + UK | 0.5533 | N/A | 0.4509 |
| India + World | 0.3479 | N/A | 0.2572 |

**Callout**: "The project now has measurable precision, recall, F1, accuracy, TP/FP/FN, latency, and confusion outputs instead of only manual CLI checks."

---

### SLIDE 14 — Deployment Options (A / B / C)

**Layout**: Three-column comparison table (the decision matrix).

**Content**:

**Heading**: "Three Named Deployment Versions"

| Criterion | **Version A** — Lookup Only | **Version B** — Lookup + Fuzzy ⭐ | **Version C** — Full 3-Layer |
|-----------|:---:|:---:|:---:|
| **Layers** | L1 only | L1 + L2 | L1 + L2 + L3 |
| **Latency** | ~0 ms | 1–100 ms | Variable |
| **Typo Handling** | ❌ None | ✅ High | ✅ High |
| **Synonym Resolution** | ❌ None | ⚠️ Engine-dependent | ✅ Yes |
| **Unstructured Text** | ❌ No | ❌ No | ✅ Yes |
| **Dependencies** | stdlib only | +1 package | Full ML stack |
| **Infra Cost** | Lowest | Low–Medium | High |
| **Best For** | Dropdown/structured data | Mixed-quality text fields | Raw resumes / free-text |

**Recommendation box** (highlighted): "Start with **Version B** (RapidFuzz engine) for production. Upgrade to Version C only when unstructured resume parsing becomes a requirement."

---

### SLIDE 15 — Proof of Concept — Demo Results

**Layout**: Terminal-style output screenshot / formatted results table.

**Content**:

**Heading**: "PoC — Pipeline in Action"

**Test results table** (from the actual normalizer output):

| Input | Canonical Degree | Layer | Conf | Status |
|-------|-----------------|-------|------|--------|
| B.Tech | Bachelor of Technology | L1 | 1.00 | ✅ resolved |
| BTech | Bachelor of Technology | L1 | 1.00 | ✅ resolved |
| Bacheler of Technology | Bachelor of Technology | L2 | 0.91 | ✅ fuzzy_matched |
| B. Tech in CSE | Bachelor of Technology | L1 | 1.00 | ✅ resolved |
| → field: | Computer Science & Engg | L1 | 1.00 | |
| M.Tech (Computer Science) | Master of Technology | L1 | 1.00 | ✅ resolved |
| MBA | Master of Business Adm. | L1 | 1.00 | ✅ resolved |
| Bachellor of Technolgy in CSE | Bachelor of Technology | L2 | 0.87 | ✅ fuzzy_matched |
| BE Hons | Bachelor of Engineering | L1 | 1.00 | ✅ resolved |
| 12th | 12th Standard | L1 | 1.00 | ✅ resolved |
| B.Pharma | — | L2 | 0.61 | ⚠️ review_needed |
| Kuchh bhi degree | — | — | — | ❌ unresolved |

---

### SLIDE 16 — Pipeline Performance Summary

**Layout**: Donut/pie chart + stat cards.

**Content**:

**Heading**: "Pipeline Performance — 12 Test Cases"

**Donut chart** (colour-coded):
- 🟢 Resolved (L1): 66.7% (8/12)
- 🔵 Fuzzy Matched (L2): 16.7% (2/12)
- 🟡 Review Needed: 8.3% (1/12)
- 🔴 Unresolved: 8.3% (1/12)

**Combined resolution rate**: **83.4%** of inputs automatically resolved without human intervention.

**Expected real-world distribution** (from the Agent Brief):
- ~85% resolved at Layer 1
- ~12% resolved at Layer 2
- ~3% to review queue

**Callout**: "The review queue is by design. Ambiguous inputs should be flagged for human review, not silently accepted."

---

### SLIDE 17 — Unified CLI Proof of Concept

**Layout**: Left = engine menu screenshot. Right = result breakdown.

**Content**:

**Heading**: "Interactive CLI — All Engines, One Application"

**Status**: FastAPI REST server **removed** (was unstable, added unnecessary server overhead). Replaced with a rich interactive CLI (`app.py`) that is simpler, faster, and fully portable.

**Engine Menu** (as shown in the terminal):
```
  MAIN MENU — Select an engine
  ═══════════════════════════════════════════
    1.  [A+B1] RapidFuzz (L1+L2)        ✓
    2.  [B2]   TF-IDF (L1+L2)           ✓
    3.  [B3]   Embeddings (L1+L2)       ✓
    4.  [C]    L2 Combined (voting)     ✓
    5.  [D]    Orchestrator (full)      ✓
    6.  Compare all engines on input
    7.  Exit
```

**Per-engine sub-menu features**:
- Run 20-input standard test suite with stats
- Normalise a custom input with full audit trail
- Batch-process from a CSV/TXT file (with optional output save)
- Cross-engine comparison on any single input

**Integration note**: For production integration, the orchestrator class (`CVNormalizationOrchestrator`) exposes a clean Python API — simply import and call `orchestrator.normalize(raw_string)` or `orchestrator.batch_normalize(list_of_strings)` in any backend service.

---

### SLIDE 18 — Data Formats & Extensibility

**Layout**: Four file-type cards showing the delivered formats.

**Content**:

**Heading**: "Multi-Format Data Delivery"

**Card 1 — SQL** 📄
- `education_seed.sql`: Full 5-table schema + seed data
- `education_reference_seed.sql`: Field aliases + degree-field mappings
- Ready for direct import into MySQL/MariaDB

**Card 2 — JSON** 📋
- `degree_dictionary.json`: Structured canonical dictionary with levels, short codes, and alias arrays
- `education_seed.json`: Complete export for NoSQL/API consumption

**Card 3 — CSV** 📊
- `degree_aliases.csv`: 7,593 aliases including medical degrees — ideal for bulk import
- `field_of_study_aliases.csv`: 308 field aliases
- `degree_field_map.csv`: 186 valid degree-field pairs
- `full_education_reference.csv`: Combined reference for UI dropdowns
- `layer1_exact_lookup_training.csv` / `layer2_fuzzy_training.csv` / `layer3_unstructured_training.csv`: **Layer-specific training datasets** for evaluation & threshold calibration
- `indian_usa/uk/world_degrees_training.csv`: **International alias sets** covering 17,913+ rows across three degree systems

**Card 4 — Python PoC** 🐍
- 6 engine files: RapidFuzz, TF-IDF, Embeddings, L2 Combined, L3 Heuristic, Orchestrator
- Unified interactive CLI (`app.py`) — zero-config, no database needed
- Python API: import `CVNormalizationOrchestrator` and call `.normalize()` or `.batch_normalize()`

---

### SLIDE 19 — SWOT Analysis of the v3.0.0 Pipeline

**Layout**: 2×2 SWOT grid.

**Content**:

**Heading**: "Strategic Analysis — v3.0.0 Pipeline Architecture"

| | **Positive** | **Negative** |
|---|---|---|
| **Internal** | **STRENGTHS** | **WEAKNESSES** |
| | • Engine C consensus voting cancels out individual engine weaknesses | • L3 heuristics are regex-based — may need tuning for uncommon formats |
| | • RapidFuzz combined scorer eliminates superset bias (v3 fix) | • Embeddings engine requires ~500 MB PyTorch + model download |
| | • L3 fully implemented with zero ML dependencies | • L3 confidence is inherently lower (0.35–0.80); all results need review |
| | • 59,949-row internationally-scoped training dataset ready for evaluation | • Combined engine latency is sum of all sub-engine latencies |
| **External** | **OPPORTUNITIES** | **THREATS** |
| | • International datasets (USA/UK/World) enable cross-market expansion | • Novel degree formats (new UGC programmes) may miss L1+L2+L3 |
| | • Alias dictionary is extensible — any new degree can be added in minutes | • Synthetic resumes may produce highly irregular education text |
| | • Same architecture can normalise job titles, skills, and locations | • Without a review queue UI, L3 results risk being accepted unchecked |

---

### SLIDE 20 — Implementation Roadmap

**Layout**: Horizontal Gantt-style timeline.

**Content**:

**Heading**: "5-Phase Implementation Roadmap"

| Phase | Task | Timeline | Owner |
|-------|------|----------|-------|
| **Phase 1** | Seed alias tables into production DB | Week 1–2 | GG Dev Team |
| **Phase 2** | Refactor CV parser to write canonical_id | Week 2–3 | GG Dev Team |
| **Phase 3** | Integrate fuzzy matching + build review queue UI | Week 3–4 | GG Dev Team |
| **Phase 4** | Update search to query canonical_id (not raw text) | Week 4–5 | GG Dev Team |
| **Phase 5** | Layer 3 NLP integration (future, post-SIP) | TBD | GG Dev Team |

**Callout**: "Phases 1–4 require no ML infrastructure. A junior developer can implement them using the provided SQL seeds and Python PoC as reference."

**Quick win**: "Phase 1 alone (seeding the alias tables) enables dropdown-based structured entry, which prevents new bad data from entering the system."

---

### SLIDE 21 — Recommendations & Next Steps

**Layout**: Numbered list with icons.

**Content**:

**Heading**: "Recommendations for Growth Grids"

1. **🚀 Deploy Version B immediately** — RapidFuzz engine provides the strongest balance of accuracy, speed, and simplicity. No ML infra needed.

2. **🔧 Fix the CV parser first** — The pipeline is only as good as its input. Ensure the parser extracts degree and field as separate structured fields.

3. **📊 Build a Review Queue UI** — Items flagged `review_needed` should surface in a recruiter dashboard. Approved items auto-expand the alias dictionary.

4. **🔄 Adopt the 5-table schema** — Separate raw from canonical. This enables backward-compatible upgrades to the normalization logic.

5. **📈 Track resolution rates** — Monitor L1/L2/review/unresolved percentages over time. Dropping L1 rates indicate new degree patterns entering the market.

6. **🧠 Evaluate Layer 3 when ready** — Train spaCy NER on Indian resume corpora only when unstructured resume parsing becomes a business requirement.

7. **🌐 Extend to other fields** — The same alias-dictionary + fuzzy-matching pattern applies to job titles, skills, and locations.

---

### SLIDE 22 — Thank You & Q&A

**Layout**: Clean, centred, with contact info.

**Content**:
- **Heading**: "Thank You"
- **Subheading**: "Questions & Discussion"
- **Contact**: Arnav — [email]
- **Repository**: [GitHub link if applicable]
- **Footer**: "Growth Grids × University of Southampton Delhi — SIP 2026"

**Design Notes**: Minimal slide. Large heading. Subtle background gradient.

---

## APPENDIX — Slide Count Summary (v3.0.0 — 24 slides)

| Slide # | Title | Type |
|---------|-------|------|
| 1 | Title | Cover |
| 2 | Agenda | Navigation |
| 3 | The Problem | Context |
| 4 | Why It Matters | Business Case |
| 5 | CV Manager Current State | Assessment |
| 6 | Competitor Landscape | Analysis |
| 7 | 3-Layer Pipeline Overview | Solution |
| 8 | Layer 1: Dictionary Lookup | Technical |
| 9 | Layer 2: Fuzzy Matching — Engine Options | Technical |
| 10 | Layer 2: Engine C — Consensus Voting ⭐ NEW | Technical |
| 11 | Layer 3: Pure-Python Heuristic Engine ✅ LIVE | Technical |
| 12 | Data Model (5 Tables) | Architecture |
| 13 | Alias Dictionary Stats | Data |
| 14 | Deployment Options (A/B/C) | Decision |
| 15 | PoC Demo Results | Evidence |
| 16 | Pipeline Performance | Analytics |
| 17 | Unified CLI Proof of Concept | Technical |
| 18 | Data Formats & Extensibility | Deliverables |
| 19 | SWOT Analysis | Strategy |
| 20 | Bug Fixes & Engine Improvements (v3.0.0) | Technical |
| 21 | Implementation Roadmap | Planning |
| 22 | Recommendations | Action Items |
| 23 | Thank You & Q&A | Closing |

---

## NOTES FOR THE PRESENTER

1. **Slide 7** (Pipeline Overview) is the centrepiece. Spend 2–3 minutes here. Walk through the flow top-to-bottom. Emphasise that Layer 3 is **live, not a stub** as of v3.0.0.
2. **Slide 10** (Engine C — Consensus Voting) — this is your strongest new technical addition. Explain that individual engine weaknesses cancel out when engines vote together.
3. **Slide 11** (Layer 3) — emphasise that this was a stub in v2 and is now fully operational. Highlight that it requires **zero ML dependencies** — pure Python regex.
4. **Slide 15** (Demo Results) — if presenting live, run `python app.py` from the `poc/` directory, choose engine [D] Orchestrator, then run the test suite. The live output mirrors this slide.
5. **Slide 17** (CLI POC) — show the engine selection menu live. Pick "Compare all engines on custom input" and type `"Bacheler of Technology in CSE"` to show the cross-engine comparison.
6. **Slide 14** (Deployment Options) — pause here and ask the audience which version they'd prefer. This creates engagement and leads naturally into the recommendation slide.
7. **Time budget**: ~1.5 minutes per content slide = ~33 minutes total. Leave 10 minutes for Q&A.

---

### NEW SLIDE — Bug Fixes & Engine Improvements (v3.0.0 + v3.6.0)

Insert this as **Slide 16** (before Data Formats).

**Heading**: "What We Fixed — v3.0.0 to v3.6.0"

**Layout**: Five-row before/after comparison table with status badges.

| Issue | Root Cause | Fix Applied | Version | Result |
|-------|-----------|-------------|---------|--------|
| `"Bachelor of Business Admin"` misclassified | `token_set_ratio` superset bias — short inputs absorbed into long canonicals | Combined scorer: `token_set_ratio×0.65 + token_sort_ratio×0.35` | v3.0.0 | ✅ Correct match every time |
| False field-splits on "Admin", "Engineering", "Business" | `\bin\b` regex matched inside word boundaries | Replaced with `\s+in\s+` (requires whitespace around keyword) | v3.0.0 | ✅ No more corrupt degree strings |
| FastAPI server instability | External HTTP server overhead, startup failures | Removed FastAPI; replaced with self-contained CLI application | v3.0.0 | ✅ Zero-dependency deployment |
| Layer 3 returning `None` canonical crashing display | No null guard in stub implementation | L3 now returns structured dict; caller always gets displayable output | v3.0.0 | ✅ Graceful handling |
| `MBBS` and all L2 inputs scoring 0.000 | `_combined_score()` missing `**kwargs` — `score_cutoff` kwarg crash silently swallowed | Added `**kwargs` to scorer signature; forwarded to sub-scorers | v3.5.0 | ✅ L2 fully operational |
| Medical degrees (MBBS, BDS, BPharm) not resolvable | Absent from training dictionary | Added `UG MEDICINE` category; dictionary regenerated (7,593 entries) | v3.5.0 | ✅ Medical degrees now resolve |
| Compact CS/IT inputs missed field inference | Field abbreviation stayed attached to the degree text | Added compact CS/IT field inference after degree alias removal | v3.6.0 | ✅ CS/IT fields now resolve better |

**Design Note**: Use ❌ (coral) for Before, ✅ (soft green) for After. Use amber for the "Root Cause" column.
