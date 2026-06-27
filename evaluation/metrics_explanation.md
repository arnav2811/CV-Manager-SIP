# F1 Metrics Explanation

This evaluation reports several scores instead of only one overall number.

| Metric | Meaning |
|---|---|
| Degree F1 | Checks whether the predicted canonical degree is correct. |
| Field F1 | Checks whether the predicted field or specialization is correct. |
| Pair F1 | Checks degree and field together. Both must match. |
| Micro F1 | Overall score across degree and field labels together. |
| Macro F1 | Average of degree macro F1 and field macro F1, so rare labels still matter. |

Missing field values are treated as blank values. They are not treated as the text `nan`.

Rows in `ambiguous_cases.csv` are excluded from the cleaned evaluation files until the team decides the correct business rule.

International datasets are degree-only. Their field metrics are reported as `N/A`.

Layer 3 is included in the complete evaluation summary, but it should be interpreted separately because it scores unstructured sentence extraction rather than direct alias lookup.
