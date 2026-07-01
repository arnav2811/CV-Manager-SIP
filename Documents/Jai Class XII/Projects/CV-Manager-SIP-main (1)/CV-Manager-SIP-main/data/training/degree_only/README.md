# Degree-Only Country/System Training Files

Generated on 2026-06-22.

These corpora contain degree or qualification names only. They exclude fields of
study and specializations.

## Files

| File | Purpose |
|---|---|
| indian_usa_degrees_training.csv | India + USA degree-name training variants |
| indian_uk_degrees_training.csv | India + UK degree-name training variants |
| indian_world_degrees_training.csv | India + USA + UK + broader world degree-name variants |
| degree_only_canonical_catalog.csv | Canonical country/system degree catalog used by the generator |
| degree_only_manifest.json | Row counts, scope, and permutation definition |

## Permutation Rules

Each training file contains every generated combination of:
- degree-only aliases
- abbreviation punctuation and spacing forms
- country adjective, country name, and country code prefixes
- degree/qualification, country, duration, and honours suffixes
- catalogued, lowercase, uppercase, and title-case variants

Because global qualifications are open-ended, "every permutation" means every
permutation over this curated canonical catalog and the deterministic rules in
`tools/build_degree_system_training_datasets.py`.
