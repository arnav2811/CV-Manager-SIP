# F1 Metrics Explanation

This evaluation reports several scores instead of only one overall number.

| Metric | Meaning |
|---|---|
| Degree F1 | Checks whether the predicted canonical degree is correct. |
| Field F1 | Checks whether the predicted field or specialization is correct. |
| Pair F1 | Checks degree and field together. Both must match. |
| Accuracy | Percentage of exact matches for degree, field, or degree-field pair. |
| TP / FP / FN | True positives, false positives, and false negatives used to calculate precision and recall. |
| Micro F1 | Overall score across degree and field labels together. |
| Macro F1 | Average of degree macro F1 and field macro F1, so rare labels still matter. |
| Resolution Rate | Percentage of rows that produced a non-`unresolved` status. |
| Average Latency | Average scoring time per row in milliseconds. |

Confusion matrix CSVs are also written for each dataset:

- `{dataset}_degree_confusion.csv`
- `{dataset}_field_confusion.csv` when field labels are available
- `{dataset}_pair_confusion.csv`

Missing field values are treated as blank values. They are not treated as the text `nan`.

Rows in `ambiguous_cases.csv` are excluded from the cleaned evaluation files until the team decides the correct business rule.

International datasets are degree-only. Their field metrics are reported as `N/A`.

Layer 3 is included in the complete evaluation summary, but it should be interpreted separately because it scores unstructured sentence extraction rather than direct alias lookup.
