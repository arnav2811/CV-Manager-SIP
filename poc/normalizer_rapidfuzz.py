"""
CV Manager Normalizer — RapidFuzz Levenshtein Engine  (Layer 2 · Engine B-1)
=============================================================================
Three-layer qualification normalization pipeline:
  L1  Exact dictionary lookup against 6,980+ pre-computed aliases.
  L2  RapidFuzz combined-score fuzzy matching (token_set_ratio × 0.65 +
      token_sort_ratio × 0.35) with configurable confidence thresholds.
      Combined scorer eliminates the "superset-string bias" that caused long
      canonical names (e.g. Bachelor of Business Administration) to absorb
      unrelated short inputs under the old token_set_ratio-only approach.
  L3  Lightweight regex heuristic stub (detects unstructured degree mentions).

Bug-fixes vs v2.3.0
  • Replaced \\bin\\b with \\s+in\\s+ in clean() — prevents false splits on
    words like "Admin", "Administration", "Engineering" that contain "in".
  • Layer 2 now uses a weighted combination scorer, not token_set_ratio alone.
  • Layer 3 stub is only triggered if L2 also fails; return value is properly
    structured so downstream consumers never see a None canonical_degree crash.
  • Full try/except guards in layer2_fuzzy and layer3_stub.

Run:  python normalizer_rapidfuzz.py
"""

import csv
import json
import re
import os

from rapidfuzz import process, fuzz


# ---------------------------------------------------------------------------
# Helper: combined scorer
# ---------------------------------------------------------------------------

def _combined_score(query: str, choice: str) -> float:
    """
    Weighted combination of token_set_ratio and token_sort_ratio.

    token_set_ratio  ×0.65  — handles token reordering and supersets well
    token_sort_ratio ×0.35  — penalises large length mismatches, preventing
                               a short input from scoring 100 against a very
                               long canonical purely via subset containment.
    Returns a float in [0, 100].
    """
    set_s  = fuzz.token_set_ratio(query, choice)
    sort_s = fuzz.token_sort_ratio(query, choice)
    return 0.65 * set_s + 0.35 * sort_s


# ---------------------------------------------------------------------------
# Normalizer class
# ---------------------------------------------------------------------------

class Normalizer:
    """RapidFuzz-backed 3-layer degree normalizer."""

    ENGINE_ID = "B-1_RapidFuzz"

    def __init__(self, data_dir: str = "../data"):
        self.data_dir        = data_dir
        self.degree_aliases: dict[str, str] = {}   # cleaned_alias → canonical
        self.field_aliases:  dict[str, str] = {}   # cleaned_alias → canonical_field
        self.canonical_degrees: set[str]    = set()
        self._load_aliases()

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_aliases(self) -> None:
        degree_csv  = os.path.join(self.data_dir, "degree_aliases.csv")
        degree_json = os.path.join(self.data_dir, "degree_dictionary.json")
        field_csv   = os.path.join(self.data_dir, "field_of_study_aliases.csv")

        if not os.path.exists(degree_csv) or not os.path.exists(field_csv):
            print("[RapidFuzz] ERROR: Alias files not found. Check data_dir path.")
            return

        # Prefer JSON dictionary (richer structure); fall back to CSV
        if os.path.exists(degree_json):
            with open(degree_json, "r", encoding="utf-8") as fh:
                deg_dict = json.load(fh)
            for canon, data in deg_dict.items():
                self.canonical_degrees.add(canon)
                for alias in data.get("aliases", []):
                    self.degree_aliases[self._clean_token(alias)] = canon
        else:
            with open(degree_csv, "r", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    key = self._clean_token(row["normalized"])
                    self.degree_aliases[key] = row["canonical_name"]
                    self.canonical_degrees.add(row["canonical_name"])

        with open(field_csv, "r", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                key = row["alias"].strip().lower().replace(".", "")
                self.field_aliases[key] = row["canonical_field"]

        print(f"[RapidFuzz] Loaded {len(self.degree_aliases):,} degree aliases  |  "
              f"{len(self.field_aliases):,} field aliases")

    # ------------------------------------------------------------------
    # String helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_token(raw: str) -> str:
        """
        Normalise a raw alias string so dictionary keys and query strings
        are prepared identically.
        """
        norm = (
            raw.lower()
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
        # Remove the standalone conjunction "in" (it is a field separator)
        return " ".join(w for w in norm.split() if w != "in")

    def clean(self, raw_string: str) -> tuple[str, str | None]:
        """
        Split a raw education string into (degree_part, field_part).

        Recognised separators (in priority order):
          1. " - "  or  " / "  (dash / slash surrounded by spaces)
          2. " in "           (standalone preposition — uses \\s+in\\s+ to
                               avoid false splits inside words like "Admin")
          3. Parentheses      e.g. "B.Tech (Computer Science)"
          4. Comma            e.g. "MBA, Finance"
        """
        raw_string    = str(raw_string).strip()
        field_part    = None

        # 1 & 2: dash, slash, or standalone " in "
        m = re.split(r"\s+-\s+|\s+/\s+|\s+in\s+", raw_string, maxsplit=1,
                     flags=re.IGNORECASE)
        if len(m) == 2:
            raw_string = m[0].strip()
            field_part = m[1].strip()
        else:
            # 3: parentheses
            paren = re.search(r"\((.*?)\)", raw_string)
            if paren:
                field_part = paren.group(1).strip()
                raw_string = re.sub(r"\(.*?\)", "", raw_string).strip()
            else:
                # 4: comma
                parts = raw_string.split(",", 1)
                if len(parts) == 2:
                    raw_string = parts[0].strip()
                    field_part = parts[1].strip()

        return self._clean_token(raw_string), field_part

    def _normalize_field(self, field_str: str | None) -> str | None:
        if not field_str:
            return None
        key = field_str.strip().lower().replace(".", "")
        return self.field_aliases.get(key)

    # ------------------------------------------------------------------
    # Layer 1 — Exact lookup
    # ------------------------------------------------------------------

    def layer1_lookup(self, cleaned: str) -> dict | None:
        if cleaned in self.degree_aliases:
            return {
                "canonical_degree": self.degree_aliases[cleaned],
                "confidence":       1.0,
                "status":           "resolved",
                "layer_used":       "L1",
                "fuzzy_score":      100,
                "alternatives":     [],
                "engine":           self.ENGINE_ID,
            }
        return None

    # ------------------------------------------------------------------
    # Layer 2 — RapidFuzz combined-score fuzzy matching
    # ------------------------------------------------------------------

    def layer2_fuzzy(self, cleaned: str,
                     threshold_auto: float = 88.0,
                     threshold_flag: float = 70.0) -> dict | None:
        """
        Match *cleaned* against all known alias keys using the combined scorer.

        threshold_auto  → score ≥ this → auto-accept (status=fuzzy_matched)
        threshold_flag  → score ≥ this → flag for review (status=review_needed)
        """
        if not self.degree_aliases:
            return None

        choices = list(self.degree_aliases.keys())

        try:
            result = process.extractOne(
                cleaned, choices,
                scorer=_combined_score,
                score_cutoff=0,
            )
        except Exception as exc:
            print(f"[RapidFuzz] layer2 extractOne error: {exc}")
            return None

        if result is None:
            return None

        # rapidfuzz >= 3.x: (match, score, index)
        try:
            best_alias, score, _idx = result
        except (TypeError, ValueError):
            best_alias, score = result[0], result[1]

        best_canonical = self.degree_aliases.get(best_alias)
        if best_canonical is None:
            return None

        # Build de-duplicated alternatives list
        try:
            top5 = process.extract(
                cleaned, choices,
                scorer=_combined_score,
                limit=8,
            )
        except Exception:
            top5 = []

        seen      = {best_canonical}
        alt_list  = []
        for item in top5:
            try:
                alt_alias, alt_score = item[0], item[1]
            except Exception:
                continue
            canon = self.degree_aliases.get(alt_alias)
            if canon and canon not in seen:
                seen.add(canon)
                alt_list.append((canon, round(alt_score, 1)))
            if len(alt_list) >= 3:
                break

        base = {
            "canonical_degree": best_canonical,
            "confidence":       round(score / 100.0, 4),
            "fuzzy_score":      round(score, 1),
            "alternatives":     alt_list,
            "layer_used":       "L2",
            "engine":           self.ENGINE_ID,
        }

        if score >= threshold_auto:
            return {**base, "status": "fuzzy_matched"}
        if score >= threshold_flag:
            return {**base, "status": "review_needed"}
        return None

    # ------------------------------------------------------------------
    # Layer 3 — Lightweight heuristic stub
    # ------------------------------------------------------------------

    def layer3_stub(self, raw: str) -> dict | None:
        """
        Regex-based keyword detector for unstructured text.
        Returns a low-confidence 'review_needed' result when degree-level
        keywords are found, so the caller can queue the record for human review.
        Returns None when no degree signal is detected at all.
        """
        raw_lower = raw.lower()
        degree_keywords = [
            "bachelor", "master", "doctorate", "phd", "diploma",
            "certificate", "degree", "graduate", "undergraduate",
        ]
        if not any(kw in raw_lower for kw in degree_keywords):
            return None

        # Try to extract a degree mention using sentence patterns
        patterns = [
            r"(?:completed?|finished?|pursuing?|did|have|holds?)\s+(?:a\s+|an\s+|my\s+)?([A-Z][\w\.\s]{2,40}?)(?:\s+(?:from|at|in)\b|$)",
            r"([A-Z][\w\.\s]{2,30}?)\s+(?:graduate|degree|program)",
        ]
        extracted = None
        for pat in patterns:
            m = re.search(pat, raw, re.IGNORECASE)
            if m:
                extracted = m.group(1).strip()
                break

        return {
            "canonical_degree": extracted,   # may be None — caller handles display
            "confidence":       0.35,
            "status":           "review_needed",
            "layer_used":       "L3_stub",
            "fuzzy_score":      35,
            "alternatives":     [],
            "engine":           self.ENGINE_ID,
        }

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def normalize(self, raw_string: str) -> dict:
        """
        Run the full L1 → L2 → L3 pipeline on a single input string.
        Always returns a dict; never raises.
        """
        cleaned, extracted_field = self.clean(raw_string)
        canonical_field = self._normalize_field(extracted_field)

        result = {
            "input":            raw_string,
            "layer_used":       "unresolved",
            "canonical_degree": None,
            "canonical_field":  canonical_field,
            "confidence":       0.0,
            "status":           "unresolved",
            "fuzzy_score":      0,
            "alternatives":     [],
            "engine":           self.ENGINE_ID,
        }

        # --- L1 ---
        l1 = self.layer1_lookup(cleaned)
        if l1:
            result.update(l1)
            return result

        # --- L2 ---
        l2 = self.layer2_fuzzy(cleaned)
        if l2:
            result.update(l2)
            if l2["status"] == "fuzzy_matched":
                return result
            # review_needed — still try L3 if confidence very low

        # --- L3 (only when L2 failed entirely or gave low confidence) ---
        if not l2 or l2["fuzzy_score"] < 55:
            l3 = self.layer3_stub(raw_string)
            if l3:
                result.update(l3)

        return result

    def batch_normalize(self, inputs: list[str]) -> list[dict]:
        return [self.normalize(s) for s in inputs]


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, "..", "data")
    n = Normalizer(data_dir)

    TEST_CASES = [
        "B.Tech",
        "BTech",
        "Bachelor of Technology",
        "Bacheler of Technology",
        "B. Tech in CSE",
        "M.Tech (Computer Science)",
        "MBA",
        "Bachellor of Technolgy in CSE",
        "BE Hons",
        "12th",
        "B.Pharma",
        "Bachelor of Business Administration",
        "Bachelor of Business Admin",
        "BBA",
        "Kuchh bhi degree",
        "I completed my Masters in Data Science from IIT",
    ]

    while True:
        print("\n" + "=" * 60)
        print("  CV MANAGER · RapidFuzz Engine (B-1)   [standalone CLI]")
        print("=" * 60)
        print("  1. Run default test suite")
        print("  2. Enter custom degree string")
        print("  3. Exit")

        choice = input("\n  Choice [1/2/3]: ").strip()

        if choice == "1":
            results = n.batch_normalize(TEST_CASES)
            print(f"\n  {len(TEST_CASES)} inputs · RapidFuzz combined-score engine\n")
            print(f"  {'INPUT':<32} {'CANONICAL':<30} {'LAYER':<8} {'CONF':<6} STATUS")
            print("  " + "-" * 90)

            stats = {"L1": 0, "L2": 0, "L3": 0, "review": 0, "unresolved": 0}
            for r in results:
                inp    = (r["input"] or "")[:30]
                canon  = (r["canonical_degree"] or "-")[:28]
                layer  = r["layer_used"]
                conf   = f"{r['confidence']:.2f}"
                status = r["status"]
                print(f"  {inp:<32} {canon:<30} {layer:<8} {conf:<6} {status}")
                if r["canonical_field"]:
                    print(f"  {'':>32} ↳ field: {r['canonical_field']}")

                if   layer == "L1":              stats["L1"]         += 1
                elif layer == "L2":              stats["L2"]         += 1
                elif "L3" in layer:              stats["L3"]         += 1
                elif status == "review_needed":  stats["review"]     += 1
                else:                            stats["unresolved"] += 1

            total = len(TEST_CASES)
            print("\n  SUMMARY")
            for k, v in stats.items():
                print(f"    {k:<12}: {v}  ({v/total*100:.0f}%)")

        elif choice == "2":
            raw = input("\n  Enter degree string: ").strip()
            if not raw:
                continue
            r = n.normalize(raw)
            print("\n" + "  " + "-" * 50)
            print("  NORMALIZATION RESULT")
            print("  " + "-" * 50)
            print(f"  Input            : {r['input']}")
            print(f"  Canonical Degree : {r['canonical_degree'] or 'None'}")
            print(f"  Canonical Field  : {r['canonical_field']  or 'None'}")
            print(f"  Layer Used       : {r['layer_used']}")
            print(f"  Confidence       : {r['confidence']:.4f}")
            print(f"  Fuzzy Score      : {r['fuzzy_score']}")
            print(f"  Status           : {r['status']}")
            if r["alternatives"]:
                print("\n  Alternatives:")
                for alt, sc in r["alternatives"]:
                    print(f"    • {alt}  (score: {sc})")
            print("  " + "-" * 50)

        elif choice == "3":
            print("  Exiting.")
            sys.exit(0)
        else:
            print("  Invalid choice.")
