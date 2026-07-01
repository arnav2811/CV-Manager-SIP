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
  L3  Delegates to the full L3HeuristicEngine (engine_l3.py) — shortcode
      expansion, PhD normalization, sentence extraction, field acronym map.

Version: 3.6.5

Bug-fixes vs v2.3.0
  • Replaced \\bin\\b with \\s+in\\s+ in clean() — prevents false splits on
    words like "Admin", "Administration", "Engineering" that contain "in".
  • Layer 2 now uses a weighted combination scorer, not token_set_ratio alone.
  • Layer 3 now delegates to L3HeuristicEngine (v3.6.5) instead of a
    primitive keyword stub — proper PhD/shortcode canonicalization applied.
  • Full try/except guards in layer2_fuzzy and layer3_heuristic.

Run:  python normalizer_rapidfuzz.py
"""

import csv
import json
import re
import os
import sys

from rapidfuzz import process, fuzz

# --- L3 engine import (lazy, with fallback) --------------------------------
_L3_ENGINE_CLASS = None
try:
    _this_dir = os.path.dirname(os.path.abspath(__file__))
    if _this_dir not in sys.path:
        sys.path.insert(0, _this_dir)
    from engine_l3 import L3HeuristicEngine as _L3HeuristicEngine
    _L3_ENGINE_CLASS = _L3HeuristicEngine
except Exception as _l3_import_err:
    pass  # L3 will fall back to the primitive stub if engine_l3 is unavailable


# ---------------------------------------------------------------------------
# Helper: combined scorer
# ---------------------------------------------------------------------------

def _combined_score(query: str, choice: str, **kwargs) -> float:
    """
    Weighted combination of token_set_ratio and token_sort_ratio.

    token_set_ratio  ×0.65  — handles token reordering and supersets well
    token_sort_ratio ×0.35  — penalises large length mismatches, preventing
                               a short input from scoring 100 against a very
                               long canonical purely via subset containment.
    Returns a float in [0, 100].
    """
    set_s  = fuzz.token_set_ratio(query, choice, **kwargs)
    sort_s = fuzz.token_sort_ratio(query, choice, **kwargs)
    return 0.65 * set_s + 0.35 * sort_s


# ---------------------------------------------------------------------------
# Normalizer class
# ---------------------------------------------------------------------------

class Normalizer:
    """RapidFuzz-backed 3-layer degree normalizer."""

    ENGINE_ID = "B-1_RapidFuzz"
    FIELD_INFERENCE_DEGREES = {
        "Bachelor of Technology",
        "Bachelor of Engineering",
        "Bachelor of Science",
        "Bachelor of Computer Applications",
        "Master of Technology",
        "Master of Engineering",
        "Master of Science",
        "Master of Computer Applications",
        "Doctor of Philosophy",
    }

    def __init__(self, data_dir: str = "../data"):
        self.data_dir        = data_dir
        self.degree_aliases: dict[str, str] = {}   # cleaned_alias → canonical
        self.degree_aliases_by_canonical: dict[str, list[str]] = {}
        self.field_aliases:  dict[str, str] = {}   # cleaned_alias → canonical_field
        self.field_aliases_cleaned: dict[str, str] = {}
        self.canonical_degrees: set[str]    = set()
        self._load_aliases()
        # Initialise the real L3 heuristic engine (replaces primitive stub)
        self._l3_engine = _L3_ENGINE_CLASS() if _L3_ENGINE_CLASS is not None else None

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
                    cleaned_alias = self._clean_token(alias)
                    self.degree_aliases[cleaned_alias] = canon
                    self.degree_aliases_by_canonical.setdefault(canon, []).append(cleaned_alias)
        else:
            with open(degree_csv, "r", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    key = self._clean_token(row["normalized"])
                    self.degree_aliases[key] = row["canonical_name"]
                    self.canonical_degrees.add(row["canonical_name"])
                    self.degree_aliases_by_canonical.setdefault(row["canonical_name"], []).append(key)

        with open(field_csv, "r", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                key = row["alias"].strip().lower().replace(".", "")
                self.field_aliases[key] = row["canonical_field"]
                cleaned_key = self._clean_token(row["alias"])
                self.field_aliases_cleaned[cleaned_key] = row["canonical_field"]

        for canon, aliases in self.degree_aliases_by_canonical.items():
            self.degree_aliases_by_canonical[canon] = sorted(set(aliases), key=len, reverse=True)

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
        field_str = field_str.strip()
        candidates = [field_str]
        if field_str.count("(") > field_str.count(")"):
            candidates.append(field_str + ")")

        for candidate in candidates:
            key = candidate.strip().lower().replace(".", "")
            if key in self.field_aliases:
                return self.field_aliases[key]

            cleaned_key = self._clean_token(candidate)
            if cleaned_key in self.field_aliases_cleaned:
                return self.field_aliases_cleaned[cleaned_key]

        return None

    @staticmethod
    def _remove_token_phrase(text: str, phrase: str) -> str:
        padded_text = f" {text} "
        padded_phrase = f" {phrase} "
        if padded_phrase not in padded_text:
            return text
        return " ".join(padded_text.replace(padded_phrase, " ", 1).split())

    def _infer_field_from_cleaned(self, cleaned_raw: str, canonical_degree: str | None) -> str | None:
        """
        Infer fields from compact inputs such as "B.Tech CSE" or "BCA Computer Applications".

        The degree alias is removed first so a degree name like "Bachelor of Computer
        Applications" does not accidentally become a field match.
        """
        if not cleaned_raw or canonical_degree not in self.FIELD_INFERENCE_DEGREES:
            return None

        remainder = cleaned_raw
        degree_alias_removed = False
        for alias in self.degree_aliases_by_canonical.get(canonical_degree, []):
            updated = self._remove_token_phrase(remainder, alias)
            if updated != remainder:
                remainder = updated
                degree_alias_removed = True
                break

        if not degree_alias_removed or not remainder:
            return None

        padded = f" {remainder} "
        for alias, canonical_field in sorted(
            self.field_aliases_cleaned.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        ):
            if alias and (padded == f" {alias} " or f" {alias} " in padded):
                return canonical_field
        return None

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

    def layer3_heuristic(self, raw: str) -> dict | None:
        """
        Delegates to the full L3HeuristicEngine (engine_l3.py) when available,
        or falls back to a minimal keyword detector.

        The full engine applies shortcode expansion, PhD canonicalization,
        sentence extraction, field acronym mapping, and level keyword detection.
        Returns a structured dict or None when no signal is found.
        """
        if self._l3_engine is not None:
            try:
                result = self._l3_engine.normalize(raw)
                # Only return if the engine found something
                if result.get("status") != "unresolved":
                    return result
                return None
            except Exception:
                pass  # Fall through to primitive fallback

        # ── Primitive fallback (only used if engine_l3 failed to import) ──
        raw_lower = raw.lower()
        degree_keywords = [
            "bachelor", "master", "doctorate", "phd", "diploma",
            "certificate", "degree", "graduate", "undergraduate",
        ]
        if not any(kw in raw_lower for kw in degree_keywords):
            return None

        return {
            "canonical_degree": None,
            "canonical_field":  None,
            "confidence":       0.35,
            "status":           "review_needed",
            "layer_used":       "L3_stub",
            "fuzzy_score":      35,
            "alternatives":     [],
            "engine":           self.ENGINE_ID,
        }

    # Keep the old name as an alias for backward compatibility
    def layer3_stub(self, raw: str) -> dict | None:
        return self.layer3_heuristic(raw)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def normalize(self, raw_string: str) -> dict:
        """
        Run the full L1 → L2 → L3 pipeline on a single input string.
        Always returns a dict; never raises.
        """
        cleaned, extracted_field = self.clean(raw_string)
        cleaned_raw = self._clean_token(raw_string)
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
            if result["canonical_field"] is None:
                result["canonical_field"] = self._infer_field_from_cleaned(
                    cleaned_raw,
                    result["canonical_degree"],
                )
            return result

        # --- L2 ---
        l2 = self.layer2_fuzzy(cleaned)
        if l2:
            result.update(l2)
            if result["canonical_field"] is None:
                result["canonical_field"] = self._infer_field_from_cleaned(
                    cleaned_raw,
                    result["canonical_degree"],
                )
            if l2["status"] == "fuzzy_matched":
                return result
            # review_needed — still try L3 if confidence very low

        # --- L3 (only when L2 failed entirely or gave low confidence) ---
        if not l2 or l2["fuzzy_score"] < 55:
            l3 = self.layer3_heuristic(raw_string)
            if l3:
                result.update(l3)
                # Normalize L3-extracted field through field alias dictionary
                l3_field = result.get("canonical_field")
                if l3_field:
                    normalized = self._normalize_field(l3_field)
                    if normalized:
                        result["canonical_field"] = normalized
                    else:
                        # L3 extracted a raw field that doesn't map — clear it
                        # to avoid false positives with institution names etc.
                        result["canonical_field"] = None
                # If no field yet, try inference from the raw string
                if result["canonical_field"] is None and result.get("canonical_degree"):
                    result["canonical_field"] = self._infer_field_from_cleaned(
                        cleaned_raw,
                        result["canonical_degree"],
                    )

        # Final fallback: if we have a field from initial clean() but nothing
        # was set yet, keep the one from the initial parse
        if result["canonical_field"] is None and canonical_field:
            result["canonical_field"] = canonical_field

        return result

    def batch_normalize(self, inputs: list[str]) -> list[dict]:
        return [self.normalize(s) for s in inputs]


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")

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

    VERSION = "3.6.5"

    while True:
        print()
        print("╔" + "═" * 64 + "╗")
        print("║" + " CV MANAGER · RapidFuzz Engine (B-1) · Standalone CLI ".center(64) + "║")
        print("║" + f" Version {VERSION} ".center(64) + "║")
        print("╚" + "═" * 64 + "╝")
        print()
        print("    1.  Run default test suite")
        print("    2.  Enter custom degree string")
        print("    3.  Exit")
        print("─" * 68)

        choice = input("\n  Choice [1/2/3]: ").strip()

        if choice == "1":
            results = n.batch_normalize(TEST_CASES)
            W = {"inp": 33, "canon": 32, "layer": 10, "conf": 6}
            div = "  " + "─" * (W["inp"] + W["canon"] + W["layer"] + W["conf"] + 4 * 2 + 6)
            print(f"\n  {len(TEST_CASES)} inputs · RapidFuzz combined-score engine")
            print()
            print(f"  {'INPUT':<{W['inp']}}  {'CANONICAL':<{W['canon']}}  "
                  f"{'LAYER':<{W['layer']}}  {'CONF':<{W['conf']}}  STATUS")
            print(div)
            stats = {"L1": 0, "L2": 0, "L3": 0, "review": 0, "unresolved": 0}
            for r in results:
                inp    = (r["input"] or "")[:W["inp"] - 1]
                canon  = (r["canonical_degree"] or "—")[:W["canon"] - 1]
                layer  = r["layer_used"][:W["layer"] - 1]
                conf   = f"{r['confidence']:.2f}"
                status = r["status"]
                print(f"  {inp:<{W['inp']}}  {canon:<{W['canon']}}  "
                      f"{layer:<{W['layer']}}  {conf:<{W['conf']}}  {status}")
                if r["canonical_field"]:
                    print(f"  {'':>{W['inp']}}  ↳ field: {r['canonical_field']}")
                if   layer.startswith("L1"):         stats["L1"]         += 1
                elif layer.startswith("L2"):         stats["L2"]         += 1
                elif "L3" in layer:                  stats["L3"]         += 1
                elif status == "review_needed":       stats["review"]     += 1
                else:                                stats["unresolved"] += 1
            print(div)
            total = len(TEST_CASES)
            print(f"\n  {'LAYER/STATUS':<14}  {'N':>4}  {'%':>5}")
            print(f"  {'─'*14}  {'─'*4}  {'─'*5}")
            for k, v in stats.items():
                if v:
                    print(f"  {k:<14}  {v:>4}  {v/total*100:>4.0f}%")


        elif choice == "2":
            raw = input("\n  Enter degree string: ").strip()
            if not raw:
                continue
            r = n.normalize(raw)
            W = 22
            div = "  " + "─" * 66
            print(f"\n{div}")
            print("  NORMALISATION RESULT  (RapidFuzz Engine B-1)")
            print(div)
            print(f"  {'Input':<{W}}: {r['input']}")
            print(f"  {'Canonical Degree':<{W}}: {r['canonical_degree'] or '—'}")
            print(f"  {'Canonical Field':<{W}}: {r['canonical_field']  or '—'}")
            print(f"  {'Layer Used':<{W}}: {r['layer_used']}")
            conf = r['confidence']
            bar  = "█" * int(conf * 20) + "░" * (20 - int(conf * 20))
            print(f"  {'Confidence':<{W}}: {conf:.4f}  [{bar}]")
            print(f"  {'Fuzzy Score':<{W}}: {r['fuzzy_score']}")
            print(f"  {'Status':<{W}}: {r['status']}")
            if r["alternatives"]:
                print(f"\n  {'Alternatives':<{W}}:")
                for alt, sc in r["alternatives"]:
                    print(f"  {'':{W}}  • {alt:<38}  score: {sc:.1f}")
            print(div)

        elif choice == "3":
            print("\n  Goodbye.\n")
            sys.exit(0)
        else:
            print("  Invalid choice.")
