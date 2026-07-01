# F1 Dataset Column Mapping

This note explains which columns are used for F1 scoring.

| Dataset | Input column | Expected degree | Expected field | Notes |
|---|---|---|---|---|
| `cleaned_eval_layer1.csv` | `raw_input` | `canonical_degree` | `canonical_field` | Exact alias lookup examples. Ambiguous raw inputs are excluded. |
| `cleaned_eval_layer2.csv` | `raw_input` | `canonical_degree` | `canonical_field` | Fuzzy, typo, and noisy examples. Hard negatives and ambiguous raw inputs are excluded. |
| `cleaned_eval_layer3.csv` | `raw_text` | `canonical_degree` | `canonical_field` | Unstructured sentence examples. Use carefully because Layer 3 is still a heuristic extractor. |
| `cleaned_eval_indian_usa.csv` | `raw_input` | `canonical_degree` | none | India + USA degree-only examples. Cross-system and cross-degree ambiguous rows are excluded. |
| `cleaned_eval_indian_uk.csv` | `raw_input` | `canonical_degree` | none | India + UK degree-only examples. Cross-system and cross-degree ambiguous rows are excluded. |
| `cleaned_eval_indian_world.csv` | `raw_input` | `canonical_degree` | none | India + world degree-only examples. Cross-system and cross-degree ambiguous rows are excluded. |

Rows listed in `ambiguous_cases.csv` should not be scored until the team decides the correct business rule.
