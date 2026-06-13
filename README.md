# CV Manager - Qualification Standardization (SIP)

This repository contains the deliverables for the Growth Grids Summer Internship Project (SIP) regarding the standardization of candidate qualifications in CV Manager.

## Directory Structure

- `data/`: Contains the generated dictionaries and seed files.
  - `degree_aliases.csv`: Core alias mapping for degrees.
  - `field_of_study_aliases.csv`: Core alias mapping for fields of study.
  - `degree_field_map.csv`: Valid pairings of degrees and fields.
  - `education_seed.sql`: SQL definitions and seed data for the 5-table schema.
  - `education_seed.json`: JSON representation of aliases and candidate examples.
  - `education_schema_seed.csv`: CSV representation of sample candidate data.
- `poc/`: Proof of concept python scripts.
  - `normalizer.py`: The 3-layer standalone normalization engine.
- `report/`:
  - `final_report.docx`: The fully detailed written report outlining the findings, implementation, and future scope.
- `presentation/`:
  - `presentation.pptx`: The slide deck for the project presentation.

## Running the PoC Normalizer

The python normalizer script requires `rapidfuzz` to handle the Layer 2 fuzzy string matching. It operates entirely offline using the CSV dictionaries generated in the `data/` folder.

1. Ensure requirements are installed:
   ```bash
   pip install rapidfuzz pandas
   ```
2. Navigate to the `poc` directory and run the script:
   ```bash
   cd poc
   python normalizer.py
   ```

## Implementation Notes

- **Layer 1 & 2 Focus**: The majority of the normalization robustness comes from exact dict lookups (Layer 1) and RapidFuzz scoring (Layer 2). These are heavily implemented in the PoC.
- **Layer 3 (NLP)**: Layer 3 relies heavily on a stable base from Layers 1 & 2. A simple regex-based stub is provided in the code, but its true implementation via spaCy NER models is left as a future scope (detailed extensively in the report).
- **Data Extensibility**: We have included `JSON` and `CSV/Excel` formats for the candidate seeds and aliases alongside the required `SQL` file to ensure the data is easily consumable across various systems.
