# CV Manager — Qualification Standardization (SIP)

This repository contains the deliverables for the Growth Grids Summer Internship Project (SIP) regarding the standardization of candidate qualifications in CV Manager.

> **Project:** Growth Grids × University of Southampton Delhi  
> **Deadline:** 3 July 2026

## Directory Structure

- `data/`: Contains the generated dictionaries and seed files.
  - `degree_aliases.csv`: Core alias mapping for degrees (~7,000 entries including permutations).
  - `degree_dictionary.json`: Structured canonical degree dictionary with levels and short codes.
  - `field_of_study_aliases.csv`: Core alias mapping for fields of study (308 aliases across 68 fields).
  - `degree_field_map.csv`: Valid pairings of degrees and fields (186 UGC-compliant pairs).
  - `full_education_reference.csv`: Combined degree × field reference with alias counts and example strings.
  - `education_reference_seed.sql`: SQL schema + INSERT statements for field aliases and degree-field mappings.
  - `education_seed.sql`: SQL definitions and seed data for the 5-table schema.
  - `education_seed.json`: JSON representation of aliases and candidate examples.
  - `education_schema_seed.csv`: CSV representation of sample candidate data.
- `auxilary_sources/`: Curated source scripts and reference data used to generate the final datasets.
  - `field_of_study.py`: Generator script for field aliases and degree-field mappings.
- `poc/`: Proof-of-concept Python scripts.
  - `normalizer_rapidfuzz.py`: Standalone normalizer utilizing RapidFuzz edit distance matching (Layer 2).
  - `normalizer_tfidf.py`: Standalone normalizer utilizing Scikit-learn character N-Gram TF-IDF cosine similarity.
  - `normalizer_embeddings.py`: Standalone normalizer utilizing Sentence-Transformer embeddings for semantic similarity.
  - `app.py`: FastAPI server wrapper exposing the `normalizer_rapidfuzz` engine as REST endpoints.
- `reports/`: Supporting documents and reference materials.
  - `Qualification_Normalisation_Frameworks.docx`: Research frameworks for qualification normalisation.
  - `SIP.pdf`: Summer Internship Project report.
- `requirements.txt`: Python dependency manifest (install with `pip install -r requirements.txt`).

## Running the PoC Engines & API

### 1. Installation of Dependencies
Ensure all packages are installed:
```bash
pip install -r requirements.txt
```
> **Lightweight install** (RapidFuzz engine only): `pip install rapidfuzz`

### 2. Standalone Normalization CLIs
Navigate to the `poc` directory:
```bash
cd poc
```

*   **To run the RapidFuzz Levenshtein Engine**:
    ```bash
    python normalizer_rapidfuzz.py
    ```
*   **To run the TF-IDF N-Gram Engine**:
    ```bash
    python normalizer_tfidf.py
    ```
*   **To run the Dense Embeddings (MiniLM) Engine**:
    ```bash
    python normalizer_embeddings.py
    ```

### 3. Exposing the API Server
To boot the headless REST service on `http://127.0.0.1:8000`:
```bash
python app.py
```
*   **API Docs**: Visually explore endpoints at `http://127.0.0.1:8000/docs`.
*   **Interactive Normalization Endpoint**: Send requests to `POST /api/v1/normalize`.

## Deployment Options (Roadmap V2)

The normalisation pipeline is packaged as **three distinct named versions** so Growth Grids can select the option that best fits their infrastructure and accuracy needs.

> **📄 Full Decision Brief**: See [`explainme.md`](explainme.md) for detailed per-version technical profiles, Layer 2 engine sub-options, and the complete recommendation rationale.

| Criterion | **Version A** — Lookup Only | **Version B** — Lookup + Fuzzy ⭐ | **Version C** — Full 3-Layer |
|-----------|-----------|-------------|-----------|
| **Layers** | L1 only | L1 + L2 | L1 + L2 + L3 |
| **Latency** | ~0 ms | 1–100 ms | Variable |
| **Typo Handling** | ❌ None | ✅ High | ✅ High |
| **Synonym Resolution** | ❌ None | ⚠️ Engine-dependent | ✅ Yes |
| **Unstructured Text** | ❌ No | ❌ No | ✅ Yes |
| **Dependencies** | stdlib only | +1 package | Full ML stack |
| **Infra Cost** | Lowest | Low–Medium | High |
| **Best For** | Structured / dropdown data | Mixed-quality text fields | Raw resumes / free-text |

> **Recommendation**: Start with **Version B** (RapidFuzz engine) for production. Upgrade to Version C only when unstructured resume parsing becomes a requirement.

### Data Extensibility
We have included `JSON` and `CSV/Excel` formats for the candidate seeds and aliases alongside the required `SQL` file to ensure the data is easily consumable across various systems.
