# Expanded Education Reference Seed Files

Generated: 2026-06-22

This package was built from the uploaded `education_reference_seed.sql` and expanded into three standalone SQL seed files:

- `education_reference_expanded_usa.sql`
- `education_reference_expanded_uk.sql`
- `education_reference_expanded_world.sql`

## What changed

The uploaded seed had 307 field alias rows, 186 degree-field rows, 68 canonical fields, and 15 canonical degrees.

The expanded files add:

- More canonical degree and award names.
- More aliases and abbreviation permutations for degrees.
- More field-of-study aliases and additional canonical fields.
- A new `degree_aliases` table for matching abbreviations such as BA, BSc, MBA, PhD, JD, MBBS, PGCE, etc.
- An exhaustive `degree_field_map` cross-product for parser/matcher coverage.

## Counts

| Scope | Canonical fields | Canonical degrees/awards | Degree-field combinations |
|---|---:|---:|---:|
| USA | 218 | 84 | 18312 |
| UK | 218 | 61 | 13298 |
| WORLD | 348 | 179 | 62292 |

## Important note

`degree_field_map` is deliberately permissive: it contains all combinations between the scope's degree/award list and the scope's canonical field list. This is useful for CV parsing, matching, and normalization, but it is not an accreditation list and does not mean every degree-field combination is offered in every country or institution.

## Sources used for expansion

- NCES CIP 2020 for U.S. instructional program field families.
- IPEDS/NCES award-level framing for U.S. award levels.
- HESA HECoS and QAA/UCAS for UK subject and qualification language.
- UNESCO ISCED-F 2013 for global field families.

See `education_reference_expanded_summary.json` for source URLs.
