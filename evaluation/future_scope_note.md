# Layer 3 Future Scope Note

Layer 3 data contains resume-like sentences and span annotations. It can be used for future extraction scoring, but it should be reported separately from Layer 1 and Layer 2.

Layer 3 is included in the complete evaluation run, but its scores should be interpreted separately because it measures unstructured extraction behavior rather than direct alias normalization.

## Post-feedback international coverage workflow

The manager feedback highlighted weaker performance on the international degree-only datasets, especially `indian_world`. Treat this as a data-quality follow-up after the Layer 3 contract fix, not as a reason to change thresholds blindly.

Recommended workflow:

1. Rerun `python poc/evaluate_f1.py --dataset all` after logic changes.
2. Review `evaluation/indian_world_failures.csv`, `evaluation/indian_uk_failures.csv`, and `evaluation/indian_usa_failures.csv`.
3. Group repeated false negatives and false positives by expected canonical degree.
4. Add aliases only for high-frequency, unambiguous naming gaps in `data/degree_aliases.csv` and the relevant training CSV.
5. Rerun the full evaluation and confirm that international F1 improves without reducing core `layer1`, `layer2`, or `layer3` scores.
