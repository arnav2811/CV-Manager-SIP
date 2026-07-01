# Layer Training Datasets

Generated on 2026-06-22 from the canonical CV Manager reference data.

## Files

| File | Rows | Use |
|---|---:|---|
| layer1_exact_lookup_training.csv | 6,976 | Exact dictionary lookup and L1 regression tests |
| layer2_fuzzy_training.csv | 15,233 | Fuzzy matching, typo recovery, threshold tuning, hard negatives |
| layer3_unstructured_training.csv | 1,124 | Resume/conversational extraction with span columns |
| layer3_unstructured_training.jsonl | 1,124 | JSONL NLP/NER companion with entity arrays |
| layer_training_manifest.json | 1 | Dataset metadata, source files, and split recommendation |

## Layer 1: Exact Lookup

Use this file to populate or test the alias dictionary. Every row is a known
alias tied to a canonical degree and, when present, a canonical field.

Important columns:
- raw_input
- normalized_degree_part
- canonical_degree
- canonical_field
- degree_level
- split_pattern
- expected_layer
- expected_status

## Layer 2: Fuzzy Matching

Use this file to tune RapidFuzz, TF-IDF, embedding, or combined-vote thresholds.
Rows are generated from valid Layer 1 aliases, then mutated with controlled
noise types.

Important columns:
- raw_input
- gold_clean_alias
- canonical_degree
- canonical_field
- noise_type
- difficulty
- expected_status
- expected_min_confidence

## Layer 3: Unstructured Extraction

Use this file for heuristic extraction tests or supervised NER-style training.
The JSONL version includes an entities array with DEGREE and FIELD spans.

Important columns:
- raw_text
- canonical_degree
- canonical_field
- degree_mention
- field_mention
- degree_span_start
- degree_span_end
- field_span_start
- field_span_end
- strategy_hint

## Suggested Evaluation

- L1: exact accuracy, canonical field accuracy, unresolved rate.
- L2: top-1 accuracy, review precision, false-positive rate, threshold curves.
- L3: entity span F1, canonical degree accuracy, canonical field accuracy,
  false-positive rate on hard negatives.
