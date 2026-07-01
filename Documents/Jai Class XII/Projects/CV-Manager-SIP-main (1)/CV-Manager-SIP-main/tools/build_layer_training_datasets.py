"""Build layer-specific training datasets for the CV qualification normalizer.

The generator uses the maintained reference files in ../data as the source of
truth and writes reproducible CSV/JSONL assets to ../data/training.
"""

from __future__ import annotations

import csv
import json
import random
import re
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
OUT_DIR = DATA_DIR / "training"
SEED = 20260622


INSTITUTIONS = [
    "IIT Delhi",
    "Delhi University",
    "University of Mumbai",
    "Anna University",
    "Pune University",
    "Amity University",
    "IIM Ahmedabad",
    "Jadavpur University",
    "VIT Vellore",
    "Manipal University",
]

NAMES = ["Aarav", "Ananya", "Riya", "Kabir", "Neha", "Arjun", "Isha", "Rohan"]


def clean_token(raw: str) -> str:
    norm = (
        str(raw)
        .lower()
        .replace(".", "")
        .replace(" (hons)", "")
        .replace(" hons", "")
        .replace("-", " ")
        .replace("/", " ")
        .replace(",", "")
        .replace("(", "")
        .replace(")", "")
        .strip()
    )
    return " ".join(w for w in norm.split() if w != "in")


def field_key(raw: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(raw).lower())


def split_degree_field(raw: str) -> tuple[str, str | None, str]:
    text = str(raw).strip()
    field = None
    split_pattern = "none"

    m = re.split(r"\s+-\s+|\s+/\s+|\s+in\s+", text, maxsplit=1, flags=re.IGNORECASE)
    if len(m) == 2:
        degree, field = m[0].strip(), m[1].strip()
        if re.search(r"\s+-\s+", text):
            split_pattern = "dash"
        elif re.search(r"\s+/\s+", text):
            split_pattern = "slash"
        else:
            split_pattern = "in"
    else:
        paren = re.search(r"\((.*?)\)", text)
        if paren:
            degree = re.sub(r"\(.*?\)", "", text).strip()
            field = paren.group(1).strip()
            split_pattern = "parentheses"
        elif "," in text:
            degree, field = [part.strip() for part in text.split(",", 1)]
            split_pattern = "comma"
        else:
            degree = text

    return degree, field, split_pattern


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def load_reference_data() -> tuple[dict, dict[str, str], dict[str, list[str]], list[dict[str, str]]]:
    degree_dict = json.loads((DATA_DIR / "degree_dictionary.json").read_text(encoding="utf-8"))
    field_rows = read_csv(DATA_DIR / "field_of_study_aliases.csv")
    degree_field_rows = read_csv(DATA_DIR / "degree_field_map.csv")

    field_alias_to_canonical: dict[str, str] = {}
    canonical_to_field_aliases: dict[str, list[str]] = {}
    for row in field_rows:
        canonical = row["canonical_field"].strip()
        aliases = {row["alias"].strip(), row["normalized"].strip(), canonical}
        canonical_to_field_aliases.setdefault(canonical, [])
        for alias in aliases:
            if alias:
                field_alias_to_canonical[field_key(alias)] = canonical
                if alias not in canonical_to_field_aliases[canonical]:
                    canonical_to_field_aliases[canonical].append(alias)

    return degree_dict, field_alias_to_canonical, canonical_to_field_aliases, degree_field_rows


def build_layer1_rows(
    degree_dict: dict,
    field_alias_to_canonical: dict[str, str],
) -> list[dict]:
    rows: list[dict] = []
    seen: set[tuple[str, str, str | None]] = set()

    for canonical_degree, meta in sorted(degree_dict.items()):
        aliases = [canonical_degree, meta.get("short_code", ""), *meta.get("aliases", [])]
        for alias in aliases:
            if not alias:
                continue
            degree_part, field_part, split_pattern = split_degree_field(alias)
            canonical_field = None
            if field_part:
                canonical_field = field_alias_to_canonical.get(field_key(field_part))

            key = (alias.strip(), canonical_degree, canonical_field)
            if key in seen:
                continue
            seen.add(key)

            rows.append(
                {
                    "sample_id": f"L1-{len(rows) + 1:05d}",
                    "raw_input": alias.strip(),
                    "normalized_degree_part": clean_token(degree_part),
                    "canonical_degree": canonical_degree,
                    "canonical_field": canonical_field or "",
                    "degree_level": meta.get("level", ""),
                    "degree_short_code": meta.get("short_code", ""),
                    "split_pattern": split_pattern,
                    "expected_layer": "L1",
                    "expected_status": "resolved",
                    "gold_confidence": "1.00",
                    "training_use": "exact_lookup_dictionary",
                    "source": "degree_dictionary.json",
                }
            )

    return rows


def delete_one_vowel(text: str) -> str:
    for idx, char in enumerate(text):
        if char.lower() in "aeiou" and idx > 1:
            return text[:idx] + text[idx + 1 :]
    return text


def transpose_middle(text: str) -> str:
    chars = list(text)
    for idx in range(1, len(chars) - 2):
        if chars[idx].isalpha() and chars[idx + 1].isalpha():
            chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]
            return "".join(chars)
    return text


def ocr_confuse(text: str) -> str:
    replacements = [
        ("Bachelor", "Bache1or"),
        ("Master", "Mastcr"),
        ("Technology", "Techn0logy"),
        ("Science", "Sc1ence"),
        ("Engineering", "Engincering"),
        ("Administration", "Administratlon"),
    ]
    for src, dst in replacements:
        if src.lower() in text.lower():
            return re.sub(src, dst, text, flags=re.IGNORECASE)
    return text.replace("l", "1", 1)


def truncate_last_word(text: str) -> str:
    parts = text.split()
    if not parts:
        return text
    last = parts[-1]
    if len(last) > 5:
        parts[-1] = last[: max(3, len(last) // 2)]
    elif len(parts) > 1 and len(parts[-2]) > 5:
        parts[-2] = parts[-2][: max(3, len(parts[-2]) // 2)]
    return " ".join(parts)


NOISE_FUNCTIONS = [
    ("single_vowel_drop", "medium", "fuzzy_matched", "0.82", delete_one_vowel),
    ("adjacent_transposition", "medium", "fuzzy_matched", "0.82", transpose_middle),
    ("ocr_confusion", "hard", "review_needed", "0.60", ocr_confuse),
    ("truncated_term", "hard", "review_needed", "0.60", truncate_last_word),
]


def build_layer2_rows(layer1_rows: list[dict]) -> list[dict]:
    rows: list[dict] = []
    l1_keys = {row["normalized_degree_part"] for row in layer1_rows}
    seen: set[str] = set()

    for base in layer1_rows:
        raw = base["raw_input"]
        if len(raw) < 4:
            continue
        for noise_type, difficulty, expected_status, expected_min_conf, func in NOISE_FUNCTIONS:
            noisy = func(raw)
            degree_part, _field_part, _split = split_degree_field(noisy)
            if noisy == raw or clean_token(degree_part) in l1_keys:
                continue

            key = f"{noisy}|{base['canonical_degree']}|{base['canonical_field']}|{noise_type}"
            if key in seen:
                continue
            seen.add(key)

            rows.append(
                {
                    "sample_id": f"L2-{len(rows) + 1:05d}",
                    "raw_input": noisy,
                    "gold_clean_alias": raw,
                    "canonical_degree": base["canonical_degree"],
                    "canonical_field": base["canonical_field"],
                    "degree_level": base["degree_level"],
                    "noise_type": noise_type,
                    "difficulty": difficulty,
                    "expected_layer": "L2",
                    "expected_status": expected_status,
                    "expected_min_confidence": expected_min_conf,
                    "training_use": "fuzzy_matching_threshold_tuning",
                    "source": base["sample_id"],
                }
            )

    negative_inputs = [
        "captain of football team",
        "worked as software developer for five years",
        "fluent in english and hindi",
        "completed online webinar",
        "sales certification pending",
        "interested in data analytics",
        "school house captain",
        "python java sql",
        "available immediately",
        "project management internship",
    ]
    for phrase in negative_inputs:
        rows.append(
            {
                "sample_id": f"L2-{len(rows) + 1:05d}",
                "raw_input": phrase,
                "gold_clean_alias": "",
                "canonical_degree": "",
                "canonical_field": "",
                "degree_level": "",
                "noise_type": "hard_negative",
                "difficulty": "negative",
                "expected_layer": "none",
                "expected_status": "unresolved",
                "expected_min_confidence": "0.00",
                "training_use": "false_positive_control",
                "source": "curated_negative",
            }
        )

    return rows


def is_degree_only_alias(alias: str) -> bool:
    without_hons = re.sub(
        r"\s*\((?:hons|honours|honors)\)", "", alias, flags=re.IGNORECASE
    )
    without_hons = re.sub(
        r"\b(?:hons|honours|honors)\b", "", without_hons, flags=re.IGNORECASE
    )
    _degree_part, field_part, _split = split_degree_field(without_hons)
    return field_part is None


def choose_degree_mention(canonical_degree: str, degree_dict: dict, idx: int) -> str:
    meta = degree_dict[canonical_degree]
    aliases = [meta.get("short_code", ""), canonical_degree, *meta.get("aliases", [])]
    aliases = [alias for alias in aliases if alias and is_degree_only_alias(alias)]
    if not aliases:
        aliases = [meta.get("short_code", ""), canonical_degree]
        aliases = [alias for alias in aliases if alias]
    return aliases[idx % len(aliases)]


def choose_field_mention(
    canonical_field: str,
    canonical_to_field_aliases: dict[str, list[str]],
    idx: int,
) -> str:
    aliases = canonical_to_field_aliases.get(canonical_field, [canonical_field])
    return aliases[idx % len(aliases)]


def make_l3_record(
    raw_text: str,
    canonical_degree: str,
    canonical_field: str,
    degree_mention: str,
    field_mention: str,
    strategy_hint: str,
    status: str = "review_needed",
) -> dict:
    degree_start = raw_text.lower().find(degree_mention.lower()) if degree_mention else -1
    field_start = raw_text.lower().find(field_mention.lower()) if field_mention else -1

    entities = []
    if degree_start >= 0:
        entities.append(
            {
                "label": "DEGREE",
                "start": degree_start,
                "end": degree_start + len(degree_mention),
                "text": raw_text[degree_start : degree_start + len(degree_mention)],
            }
        )
    if field_start >= 0:
        entities.append(
            {
                "label": "FIELD",
                "start": field_start,
                "end": field_start + len(field_mention),
                "text": raw_text[field_start : field_start + len(field_mention)],
            }
        )

    return {
        "raw_text": raw_text,
        "canonical_degree": canonical_degree,
        "canonical_field": canonical_field,
        "degree_mention": degree_mention,
        "field_mention": field_mention,
        "degree_span_start": degree_start,
        "degree_span_end": degree_start + len(degree_mention) if degree_start >= 0 else -1,
        "field_span_start": field_start,
        "field_span_end": field_start + len(field_mention) if field_start >= 0 else -1,
        "entities": entities,
        "expected_layer": "L3",
        "expected_status": status,
        "strategy_hint": strategy_hint,
        "training_use": "unstructured_extraction_and_ner",
    }


def build_layer3_rows(
    degree_dict: dict,
    canonical_to_field_aliases: dict[str, list[str]],
    degree_field_rows: list[dict[str, str]],
) -> list[dict]:
    random.seed(SEED)
    rows: list[dict] = []

    templates = [
        ("completed_sentence", "I completed my {degree} in {field} from {institution} in {year}."),
        ("pursuing_sentence", "Currently pursuing {degree} with specialization in {field} at {institution}."),
        ("holds_sentence", "{name} holds a {degree} degree in {field}."),
        ("resume_line", "Education: {degree}, {field}, {institution}, batch of {year}."),
        ("profile_summary", "Graduate of {institution}; qualification {degree} ({field})."),
        ("compact_resume", "{degree} - {field} - {institution} - {year}"),
    ]

    for idx, pair in enumerate(degree_field_rows):
        canonical_degree = pair["degree_canonical"].strip()
        canonical_field = pair["field_canonical"].strip()
        if canonical_degree not in degree_dict:
            continue

        for template_idx, (strategy_hint, template) in enumerate(templates):
            degree_mention = choose_degree_mention(canonical_degree, degree_dict, idx + template_idx)
            field_mention = choose_field_mention(canonical_field, canonical_to_field_aliases, idx + template_idx)
            institution = INSTITUTIONS[(idx + template_idx) % len(INSTITUTIONS)]
            year = str(2016 + ((idx + template_idx) % 11))
            name = NAMES[(idx + template_idx) % len(NAMES)]
            raw_text = template.format(
                degree=degree_mention,
                field=field_mention,
                institution=institution,
                year=year,
                name=name,
            )
            record = make_l3_record(
                raw_text,
                canonical_degree,
                canonical_field,
                degree_mention,
                field_mention,
                strategy_hint,
            )
            record["sample_id"] = f"L3-{len(rows) + 1:05d}"
            rows.append(record)

    negative_texts = [
        "Led a team of six interns for a market research project.",
        "Experienced in Python, SQL, Excel, Power BI, and dashboard reporting.",
        "Managed campus placement coordination and student outreach.",
        "Won first prize in the annual debate competition.",
        "Available for relocation and immediate joining.",
        "Handled customer support tickets and prepared weekly reports.",
        "Completed an internal company onboarding program.",
        "Interested in machine learning, product analytics, and consulting.",
    ]
    for text in negative_texts:
        rows.append(
            {
                "sample_id": f"L3-{len(rows) + 1:05d}",
                "raw_text": text,
                "canonical_degree": "",
                "canonical_field": "",
                "degree_mention": "",
                "field_mention": "",
                "degree_span_start": -1,
                "degree_span_end": -1,
                "field_span_start": -1,
                "field_span_end": -1,
                "entities": [],
                "expected_layer": "none",
                "expected_status": "unresolved",
                "strategy_hint": "hard_negative",
                "training_use": "false_positive_control",
            }
        )

    return rows


def write_manifest(layer1_rows: list[dict], layer2_rows: list[dict], layer3_rows: list[dict]) -> None:
    manifest = {
        "generated_on": date.today().isoformat(),
        "seed": SEED,
        "source_files": [
            "data/degree_dictionary.json",
            "data/degree_aliases.csv",
            "data/field_of_study_aliases.csv",
            "data/degree_field_map.csv",
        ],
        "datasets": {
            "layer1_exact_lookup_training.csv": {
                "rows": len(layer1_rows),
                "purpose": "Exact alias lookup training/loading and regression tests.",
                "gold_rule": "raw_input should resolve to canonical_degree at confidence 1.0.",
            },
            "layer2_fuzzy_training.csv": {
                "rows": len(layer2_rows),
                "purpose": "Fuzzy matcher threshold tuning, typo handling, and false-positive control.",
                "gold_rule": "raw_input is intentionally noisy and should not be solved by exact lookup.",
            },
            "layer3_unstructured_training.csv": {
                "rows": len(layer3_rows),
                "purpose": "Conversational/resume-text extraction and optional NER training.",
                "gold_rule": "entity spans identify degree and field mentions in raw_text.",
            },
            "layer3_unstructured_training.jsonl": {
                "rows": len(layer3_rows),
                "purpose": "JSONL companion with entity arrays for NLP pipelines.",
            },
        },
        "recommended_splits": {
            "train": "70%",
            "validation": "15%",
            "test": "15%",
            "split_key": "sample_id",
        },
    }
    (OUT_DIR / "layer_training_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_readme(layer1_rows: list[dict], layer2_rows: list[dict], layer3_rows: list[dict]) -> None:
    readme = f"""# Layer Training Datasets

Generated on {date.today().isoformat()} from the canonical CV Manager reference data.

## Files

| File | Rows | Use |
|---|---:|---|
| layer1_exact_lookup_training.csv | {len(layer1_rows):,} | Exact dictionary lookup and L1 regression tests |
| layer2_fuzzy_training.csv | {len(layer2_rows):,} | Fuzzy matching, typo recovery, threshold tuning, hard negatives |
| layer3_unstructured_training.csv | {len(layer3_rows):,} | Resume/conversational extraction with span columns |
| layer3_unstructured_training.jsonl | {len(layer3_rows):,} | JSONL NLP/NER companion with entity arrays |
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
"""
    (OUT_DIR / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    degree_dict, field_alias_to_canonical, canonical_to_field_aliases, degree_field_rows = (
        load_reference_data()
    )

    layer1_rows = build_layer1_rows(degree_dict, field_alias_to_canonical)
    layer2_rows = build_layer2_rows(layer1_rows)
    layer3_rows = build_layer3_rows(degree_dict, canonical_to_field_aliases, degree_field_rows)

    write_csv(
        OUT_DIR / "layer1_exact_lookup_training.csv",
        layer1_rows,
        [
            "sample_id",
            "raw_input",
            "normalized_degree_part",
            "canonical_degree",
            "canonical_field",
            "degree_level",
            "degree_short_code",
            "split_pattern",
            "expected_layer",
            "expected_status",
            "gold_confidence",
            "training_use",
            "source",
        ],
    )
    write_csv(
        OUT_DIR / "layer2_fuzzy_training.csv",
        layer2_rows,
        [
            "sample_id",
            "raw_input",
            "gold_clean_alias",
            "canonical_degree",
            "canonical_field",
            "degree_level",
            "noise_type",
            "difficulty",
            "expected_layer",
            "expected_status",
            "expected_min_confidence",
            "training_use",
            "source",
        ],
    )
    write_csv(
        OUT_DIR / "layer3_unstructured_training.csv",
        layer3_rows,
        [
            "sample_id",
            "raw_text",
            "canonical_degree",
            "canonical_field",
            "degree_mention",
            "field_mention",
            "degree_span_start",
            "degree_span_end",
            "field_span_start",
            "field_span_end",
            "expected_layer",
            "expected_status",
            "strategy_hint",
            "training_use",
        ],
    )
    write_jsonl(OUT_DIR / "layer3_unstructured_training.jsonl", layer3_rows)
    write_manifest(layer1_rows, layer2_rows, layer3_rows)
    write_readme(layer1_rows, layer2_rows, layer3_rows)

    print(f"Layer 1 rows: {len(layer1_rows):,}")
    print(f"Layer 2 rows: {len(layer2_rows):,}")
    print(f"Layer 3 rows: {len(layer3_rows):,}")
    print(f"Wrote datasets to: {OUT_DIR}")


if __name__ == "__main__":
    main()
