# PPT Generation Prompt — CV Manager Qualification Standardization (SIP)

> **Use this prompt** to generate a professional 22-slide PowerPoint presentation for the Growth Grids Summer Internship Project. Feed this document to any AI presentation tool (Gamma, SlidesAI, Beautiful.AI, Claude, GPT, etc.) or use it as a slide-by-slide brief for manual creation.

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
- **Team**: Arnav [add surname]
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
7. Layer 2: Fuzzy Matching
8. Layer 3: NLP Extraction (Proposed)
9. The Data Model
10. The Alias Dictionary — By the Numbers
11. Deployment Options (A / B / C)
12. Proof of Concept — Live Demo
13. API Integration
14. Results & Pipeline Performance
15. Implementation Roadmap
16. Recommendations
17. Q&A

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
                     │  LAYER 3 — NLP/NER (Stub)    │  ~3% edge cases
                     │  Regex extraction from       │  For unstructured text
                     │  free-form sentences         │
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

**Layout**: Three-column comparison cards.

**Content**:

**Heading**: "Three Interchangeable Fuzzy Engines"

**Card 1 — RapidFuzz (B-1)** ⭐ Recommended
- Mechanism: Levenshtein edit distance / token overlap
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

---

### SLIDE 11 — Layer 3: NLP/NER Extraction (Proposed)

**Layout**: Left = architecture diagram. Right = example.

**Content**:

**Heading**: "Layer 3 — Extracting Degrees from Free Text (Future)"

**Status badge**: 🟡 Proposed / Stub Implementation

**Architecture**:
- Use **spaCy** with custom NER model trained on Indian resume sentences
- Custom entity labels: `DEGREE_TYPE`, `FIELD`, `INSTITUTION`, `GRAD_YEAR`
- Triggered only when L1 + L2 both fail (score < 50)

**Example**:
```
Input:  "I completed my four-year engineering degree in
         Computer Science from VIT in 2022"

NER Output:
  DEGREE_TYPE  → "four-year engineering degree" → Master of Technology
  FIELD        → "Computer Science" → Computer Science and Engineering
  INSTITUTION  → "VIT"
  GRAD_YEAR    → "2022"
```

**Current stub**: Regex-based keyword detection (`"degree in"`, `"bachelor"`, `"master"`) — demonstrates the hook point for future NER integration.

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
- **19** Canonical Degree Types
- **68** Canonical Fields of Study (UGC/AICTE recognised)
- **6,980+** Degree Name Aliases (incl. permutations)
- **308** Field of Study Aliases
- **186** Valid Degree × Field Combinations

**Sample table** (4 rows from the dataset):

| Raw String (what candidates write) | Canonical Name (what we store) | Level |
|-------------------------------------|-------------------------------|-------|
| B.Tech, BTech, B. Tech, BTECH, B.Tech (Hons) | Bachelor of Technology | UG Engineering |
| MBA, M.B.A., EMBA | Master of Business Administration | PG Other |
| PGDM, PGD, PGDBA, PG Diploma | Post Graduate Diploma | Diploma |
| HSC, 10+2, XII, Plus Two, ISC | 12th Standard | School |

**Callout**: "Each alias was manually verified or programmatically generated via a permutation engine combining degree abbreviations × structural connectors (dash, slash, parentheses, comma, keyword 'in')."

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

### SLIDE 17 — REST API Integration

**Layout**: Left = endpoint list. Right = request/response JSON.

**Content**:

**Heading**: "Headless REST API — Ready for Integration"

**Endpoints**:
| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/normalize` | Normalize a single education string |
| `POST` | `/api/v1/normalize/batch` | Batch-process a list of strings |
| `GET` | `/health` | Service health check + loaded dictionary size |
| `GET` | `/docs` | Interactive Swagger UI |

**Example Request**:
```json
POST /api/v1/normalize
{
  "raw_text": "Bacheler of Technology in CSE"
}
```

**Example Response**:
```json
{
  "input_text": "Bacheler of Technology in CSE",
  "layer_used": "L2",
  "canonical_degree": "Bachelor of Technology",
  "canonical_field": "Computer Science and Engineering",
  "confidence": 0.91,
  "status": "fuzzy_matched",
  "fuzzy_score": 91.0,
  "alternatives": [
    ["Bachelor of Engineering", 84.0],
    ["Master of Technology", 61.0]
  ]
}
```

**Tech stack**: FastAPI + Uvicorn + Pydantic V2 + CORS-enabled

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
- `degree_aliases.csv`: 6,980+ aliases (ideal for bulk import via LOAD DATA INFILE)
- `field_of_study_aliases.csv`: 308 field aliases
- `degree_field_map.csv`: 186 valid degree-field pairs
- `full_education_reference.csv`: Combined reference for UI dropdowns

**Card 4 — Python PoC** 🐍
- 4 standalone scripts: RapidFuzz, TF-IDF, Embeddings, FastAPI wrapper
- Interactive CLI + REST API modes
- Zero-config — loads from CSV/JSON, no database needed

---

### SLIDE 19 — SWOT Analysis of Layer 2 Frameworks

**Layout**: 2×2 SWOT grid.

**Content**:

**Heading**: "Strategic Analysis — Layer 2 Engine Options"

| | **Positive** | **Negative** |
|---|---|---|
| **Internal** | **STRENGTHS** | **WEAKNESSES** |
| | • TF-IDF: Sub-millisecond latency; highly scalable | • TF-IDF/RapidFuzz: Blind to semantic meanings |
| | • RapidFuzz: Typos and letter transpositions handled | • "B.S." and "Bachelor of Science" score poorly without explicit maps |
| | • Embeddings: Resolves conceptual aliases natively | • Embeddings: Requires large PyTorch CPU/GPU memory |
| **External** | **OPPORTUNITIES** | **THREATS** |
| | • Hybrid scoring: TF-IDF + Embeddings for perfect precision | • Dense Embeddings may block high-throughput batch uploads on CPU |
| | • FastAPI microservices enable language-agnostic integration | • Novel slang words may cause false positives in semantic models |

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

## APPENDIX — Slide Count Summary

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
| 9 | Layer 2: Fuzzy Matching | Technical |
| 10 | Layer 2: Engine Options | Comparison |
| 11 | Layer 3: NLP/NER | Technical |
| 12 | Data Model (5 Tables) | Architecture |
| 13 | Alias Dictionary Stats | Data |
| 14 | Deployment Options (A/B/C) | Decision |
| 15 | PoC Demo Results | Evidence |
| 16 | Pipeline Performance | Analytics |
| 17 | REST API Integration | Technical |
| 18 | Data Formats & Extensibility | Deliverables |
| 19 | SWOT Analysis | Strategy |
| 20 | Implementation Roadmap | Planning |
| 21 | Recommendations | Action Items |
| 22 | Thank You & Q&A | Closing |

---

## NOTES FOR THE PRESENTER

1. **Slide 7** (Pipeline Overview) is the centrepiece. Spend 2–3 minutes here. Walk through the flow top-to-bottom.
2. **Slide 9** (Fuzzy Matching) — use the v1 vs v2 comparison to show improvement. This is your strongest "before/after" moment.
3. **Slide 15** (Demo Results) — if presenting live, run `python normalizer_rapidfuzz.py` and select option 1. The terminal output mirrors this slide exactly.
4. **Slide 14** (Deployment Options) — pause here and ask the audience which version they'd prefer. This creates engagement.
5. **Time budget**: ~1.5 minutes per content slide = ~30 minutes total. Leave 10 minutes for Q&A.
