# CV Manager - Qualification Standardization (SIP)

This repository contains the deliverables for the Growth Grids Summer Internship Project (SIP) regarding the standardization of candidate qualifications in CV Manager.

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
- `poc/`: Proof of concept python scripts.
  - `normalizer_rapidfuzz.py`: Standalone normalizer utilizing RapidFuzz edit distance matching (Layer 2).
  - `normalizer_tfidf.py`: Standalone normalizer utilizing Scikit-learn character N-Gram TF-IDF cosine similarity.
  - `normalizer_embeddings.py`: Standalone normalizer utilizing Sentence-Transformer embeddings for semantic similarity.
  - `app.py`: FastAPI server wrapper exposing the `normalizer_rapidfuzz` engine as REST endpoints.
- `report/`:
  - `final_report.docx`: The fully detailed written report outlining the findings, implementation, and future scope.
- `presentation/`:
  - `presentation.pptx`: The slide deck for the project presentation.

## Running the PoC Engines & API

### 1. Installation of Dependencies
Ensure all packages are installed:
```bash
pip install fastapi uvicorn rapidfuzz pydantic scikit-learn sentence-transformers
```

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

## Implementation Notes

- **Layer 1 & 2 Focus**: The majority of the normalization robustness comes from exact dict lookups (Layer 1) and similarity scoring (Layer 2). These are heavily implemented in the PoCs.
- **Layer 3 (NLP)**: Layer 3 relies heavily on a stable base from Layers 1 & 2. A simple regex-based stub is provided in the code, but its true implementation via spaCy NER models is left as a future scope (detailed extensively in the report).
- **Data Extensibility**: We have included `JSON` and `CSV/Excel` formats for the candidate seeds and aliases alongside the required `SQL` file to ensure the data is easily consumable across various systems.
