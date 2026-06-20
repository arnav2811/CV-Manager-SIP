# Pipeline Deployment Options — Growth Grids Decision Brief

> **Purpose**: This document packages the CV Manager normalisation pipeline as **three distinct, named deployment versions** so that Growth Grids can evaluate and select the option that best fits their infrastructure, latency, and accuracy requirements.

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
| **Dependencies** | Python standard library only (csv, json, re) |
| **Infrastructure** | Minimal — runs anywhere, no ML runtime needed |
| **Accuracy** | High on structured data; **zero tolerance for typos** |

### When To Pick This
- Your candidate data is **mostly structured** (e.g., entered via dropdowns or constrained forms).
- You need the **absolute lowest latency** and simplest deployment.
- Unmapped entries can be safely **discarded or queued for manual review** without impacting business flow.
- You want a **zero-risk, zero-dependency** starting point that can be upgraded later.

### Limitations
- Any input not explicitly present in the alias dictionary will be rejected.
- Typos like `"Bacheler of Technology"` or abbreviation variants like `"B.S."` vs `"Bachelor of Science"` will fail unless they are pre-mapped.

---

## Version B: Lookup + Fuzzy (Layer 1 & Layer 2) — ⭐ Recommended

### What It Does
Performs exact dictionary matching first (Layer 1). If no match is found, the input **falls back to an algorithmic similarity engine** that scores the input against all 6,980+ known aliases and returns the closest match above a configurable confidence threshold.

Three interchangeable Layer 2 engines are provided (choose one at deployment time):

#### Engine Option B-1: RapidFuzz (Levenshtein Edit Distance)
- **File**: `poc/normalizer_rapidfuzz.py`
- **How**: Uses `fuzz.token_set_ratio` to compare token overlap, resilient to word reordering and character transpositions.
- **Speed**: ~1–5 ms per query.
- **Best at**: Catching typos (`"Btehc"` → `"BTech"`), handling word reorderings.
- **Weakness**: Blind to semantics — cannot resolve `"B.S."` to `"Bachelor of Science"`.
- **Dependencies**: `rapidfuzz` (pure C extension, lightweight).

#### Engine Option B-2: TF-IDF Character N-Gram Cosine Similarity
- **File**: `poc/normalizer_tfidf.py`
- **How**: Converts strings to sparse vectors using character 3-to-5-grams weighted by TF-IDF, then measures cosine distance.
- **Speed**: <1 ms per query (fastest L2 option).
- **Best at**: High-throughput batch processing; excellent typo tolerance since errors only corrupt a fraction of n-grams.
- **Weakness**: Threshold tuning is sensitive; fails on conceptual synonyms with entirely different character layouts.
- **Dependencies**: `scikit-learn`.

#### Engine Option B-3: Sentence-Transformer Semantic Embeddings
- **File**: `poc/normalizer_embeddings.py`
- **How**: Passes input through a `all-MiniLM-L6-v2` neural network to produce a 384-dim dense vector; matches via dot product against pre-encoded canonical aliases.
- **Speed**: ~50–100 ms per query (CPU).
- **Best at**: Resolving conceptual abbreviations and synonyms (`"B.S."`, `"B.Sc."`, `"Bachelor of Science"` all map correctly).
- **Weakness**: Heaviest footprint; requires PyTorch + Sentence-Transformers + ~90 MB model download.
- **Dependencies**: `sentence-transformers`, `torch`.

### Layers Active
| Layer | Status |
|-------|--------|
| **L1 — Exact Lookup** | ✅ Active |
| **L2 — Fuzzy Match** | ✅ Active (choose one engine above) |
| L3 — NLP / Heuristics | ❌ Disabled |

### Technical Profile (varies by chosen L2 engine)
| Metric | B-1 RapidFuzz | B-2 TF-IDF | B-3 Embeddings |
|--------|--------------|------------|----------------|
| **Latency (L2 fallback)** | ~1–5 ms | <1 ms | ~50–100 ms |
| **Typo Resilience** | High | High | Moderate |
| **Synonym Resolution** | Low | Low | Excellent |
| **Infrastructure** | Light | Light | Heavy (PyTorch) |

### When To Pick This
- Your data contains **natural human variation** — spelling mistakes, abbreviation differences, minor formatting inconsistencies.
- You are processing **historical free-text input fields** or **OCR outputs** where data is somewhat clean but not perfectly structured.
- You want a **strong balance of accuracy and speed** without deploying heavy NLP infrastructure.
- **Recommended as the default starting point** for most production use cases.

### Limitations
- Cannot parse complex unstructured sentences (e.g., `"I completed my B.S. in Computer Science in 2022"`).
- Confidence thresholds (`auto-accept ≥ 88`, `review ≥ 70`) may need tuning for your specific data distribution.

---

## Version C: Full 3-Layer Pipeline (Lookup + Fuzzy + NLP/Heuristics)

### What It Does
The **complete stack**. Inputs flow through all three layers sequentially:
1. **Layer 1** — Exact dictionary lookup (instant resolution for known aliases).
2. **Layer 2** — Algorithmic fuzzy matching (catches typos, abbreviations).
3. **Layer 3** — NLP/regex-based extraction for fully unstructured conversational text (extracts degree mentions from sentences).

### Layers Active
| Layer | Status |
|-------|--------|
| **L1 — Exact Lookup** | ✅ Active |
| **L2 — Fuzzy Match** | ✅ Active |
| **L3 — NLP / Heuristics** | ✅ Active |

### Technical Profile
| Metric | Value |
|--------|-------|
| **Latency** | Variable (ms to seconds depending on L3 model) |
| **Extraction Rate** | Maximum possible — parses even conversational text |
| **Dependencies** | Full ML stack (RapidFuzz or equivalent + spaCy/NER models) |
| **Infrastructure** | Heaviest — requires dedicated ML runtime, model training, and maintenance |
| **Accuracy** | Highest for unstructured data; may over-extract on ambiguous text |

### Layer 3 Details (Current Status: Stub/Prototype)
- The current L3 implementation (`layer3_stub` in `normalizer_rapidfuzz.py`) is a **regex-based prototype** that detects keywords like `"degree in"`, `"bachelor"`, `"master"` in raw text.
- A production L3 would use **spaCy Named Entity Recognition (NER)** trained on education-domain corpora to extract degree and field mentions from arbitrary sentences.
- L3 is triggered only when L1 and L2 both fail or return low-confidence results (score < 50).

### When To Pick This
- You need to process **entirely raw, unstructured resume blocks** or free-text candidate summaries.
- Your input data includes **conversational sentences** like *"I completed my B.S. in Computer Science from MIT in 2022"*.
- You have the engineering capacity to **train and maintain NER models** for the education domain.
- **Maximum extraction rate** is more important than deployment simplicity.

### Limitations
- Layer 3 NLP models (spaCy NER) require **dedicated training data and maintenance**.
- Higher risk of **false positives** on ambiguous text.
- Significantly more complex deployment and monitoring.

---

## Decision Matrix — Side-by-Side Comparison

| Criterion | Version A | Version B ⭐ | Version C |
|-----------|-----------|-------------|-----------|
| **Layers** | L1 only | L1 + L2 | L1 + L2 + L3 |
| **Latency** | ~0 ms | 1–100 ms | Variable |
| **Typo Handling** | ❌ None | ✅ High | ✅ High |
| **Synonym Resolution** | ❌ None | ⚠️ Engine-dependent | ✅ Yes |
| **Unstructured Text** | ❌ No | ❌ No | ✅ Yes |
| **Dependencies** | stdlib only | +1 package | Full ML stack |
| **Infra Cost** | Lowest | Low–Medium | High |
| **Maintenance** | Near zero | Threshold tuning | Model retraining |
| **Risk** | Lowest | Low | Moderate |
| **Recommended For** | Structured/dropdown data | Mixed-quality text fields | Raw resumes/free-text |

---

## Recommendation

> **Start with Version B** (using Engine B-1: RapidFuzz) for immediate production deployment. It provides the strongest balance of accuracy, speed, and simplicity. Upgrade to Version C only when unstructured resume parsing becomes a business requirement and the engineering team has capacity to train and maintain NLP models.

---

## Appendix: Layer 2 Engine Strategic Comparison

| Feature | RapidFuzz (Levenshtein) | TF-IDF (Char N-Gram) | Sentence-Transformers (Embeddings) |
|---|---|---|---|
| **Mechanism** | String token overlaps | Sub-string vector overlaps | Neural network semantic vectors |
| **Speed** | Fast (~1-5ms) | Extremely Fast (<1ms) | Slow (~50-100ms) |
| **Synonym Matching** | Poor | Poor | Excellent |
| **Typo Resilience** | High | High | Moderate |
| **Infrastructure** | Light (Pure C extension) | Light (scikit-learn) | Heavy (PyTorch + SentenceTransformers) |

---

*This document is part of the SIP deliverables. See [README.md](README.md) for project overview and [CHANGELOG.md](CHANGELOG.md) for version history.*
