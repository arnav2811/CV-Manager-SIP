# CHANGELOG — CV Manager Qualification Normalizer

> **Project:** CV Manager — Qualification Standardization (SIP)  
> **Organisation:** Growth Grids × University of Southampton Delhi  
> **Deadline:** 3 July 2026

---

## Version 2.0 — 15 June 2026

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
| `poc/normalizer.py` | Layer 1 regex overhaul + Layer 2 scorer swap + JSON dict loading |
| `data/degree_aliases.csv` | Expanded from ~600 → 6,983 entries |
| `data/degree_dictionary.json` | **New** — Structured canonical degree dictionary |
| `data/education_seed.json` | Updated to reflect new permutation data |
| `auxilary_sources/field_of_study.py` | Patched paths for Windows compatibility |
| `data/field_of_study_aliases.csv` | Regenerated from curated auxiliary source |
| `data/degree_field_map.csv` | Regenerated from curated auxiliary source |
| `data/full_education_reference.csv` | **New** — Combined degree × field reference |

---

## Version 1.0 — 13 June 2026

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
