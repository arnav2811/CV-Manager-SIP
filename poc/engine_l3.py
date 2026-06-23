"""
CV Manager — Layer 3 NLP / Heuristic Engine
============================================
Handles unstructured and conversational text that L1 (exact match) and
L2 (fuzzy) fail to resolve.  Implemented as a pure-Python regex cascade —
no external NLP dependencies required.

Strategy cascade (applied in order until a result is found)
-----------------------------------------------------------
S1  Sentence extraction
    Regex patterns pull degree mentions from natural-language sentences,
    e.g. "I completed my B.Tech in CSE from IIT Delhi in 2022".

S2  Shortcode / abbreviation expansion
    Hard-coded map of single-token abbreviations → canonical degree.
    Catches standalone tokens like "BE", "ME", "MS", "PhD", "BCA"
    that survive L1/L2 because they have no surrounding context.

S3  Degree-level keyword detection
    Maps level keywords (bachelor, master, phd, diploma …) to a
    degree-level group, then performs a secondary regex pass to extract
    field mentions.  Returns the most specific inferred canonical.

S4  Field-only inference
    If a field of study is mentioned but no degree level, returns a
    low-confidence "field detected, degree unknown" result.

Result confidence levels
    S1 extraction with field  : 0.72
    S1 extraction no field    : 0.60
    S2 shortcode match        : 0.80
    S3 level keyword only     : 0.50
    S4 field only             : 0.35
    No signal found           : None (returns None, caller handles)

Run:  python engine_l3.py
"""

from __future__ import annotations

import os
import re
import sys
from typing import Optional

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

ENGINE_ID = "L3_Heuristic"

# ---------------------------------------------------------------------------
# Short-code → canonical map  (single tokens that survive L1/L2)
# ---------------------------------------------------------------------------
_SHORTCODE_MAP: dict[str, str] = {
    # Engineering
    "be":   "Bachelor of Engineering",
    "btech": "Bachelor of Technology",
    "bе":   "Bachelor of Engineering",      # cyrillic е safety
    "me":   "Master of Engineering",
    "mtech": "Master of Technology",
    "mе":   "Master of Engineering",
    # Science
    "bsc":  "Bachelor of Science",
    "msc":  "Master of Science",
    "bs":   "Bachelor of Science",
    "ms":   "Master of Science",
    # Arts
    "ba":   "Bachelor of Arts",
    "ma":   "Master of Arts",
    # Commerce / Business
    "bcom": "Bachelor of Commerce",
    "mcom": "Master of Commerce",
    "bba":  "Bachelor of Business Administration",
    "mba":  "Master of Business Administration",
    # Computer
    "bca":  "Bachelor of Computer Applications",
    "mca":  "Master of Computer Applications",
    # PhD / Research
    "phd":  "Doctor of Philosophy",
    "dphil":"Doctor of Philosophy",
    "med":  "Master of Education",
    "bed":  "Bachelor of Education",
    # Pharmacy
    "bpharma": "Bachelor of Pharmacy",
    "mpharma": "Master of Pharmacy",
    # School
    "12th": "Senior Secondary (Class XII)",
    "10th": "Secondary (Class X)",
    "hsc":  "Senior Secondary (Class XII)",
    "ssc":  "Secondary (Class X)",
    # Law
    "llb":  "Bachelor of Laws",
    "llm":  "Master of Laws",
    # Design
    "bdes": "Bachelor of Design",
    "mdes": "Master of Design",
    # Diploma
    "pgdm": "Post Graduate Diploma",
    "pgd":  "Post Graduate Diploma",
    "pgdba":"Post Graduate Diploma in Business Administration",
}

# ---------------------------------------------------------------------------
# Level keyword groups  →  most specific default canonical
# ---------------------------------------------------------------------------
_LEVEL_KEYWORD_MAP: list[tuple[list[str], str, str]] = [
    # (keywords,                     level_label,        default_canonical)
    (["phd", "doctorate", "doctoral", "ph.d"],
     "doctoral", "Doctor of Philosophy"),

    (["master", "masters", "mtech", "m.tech", "msc", "m.sc", "mba",
      "m.b.a", "postgrad", "post-grad", "post grad", "pg"],
     "postgrad", "Master of Science"),

    (["bachelor", "bachelors", "btech", "b.tech", "bsc", "b.sc",
      "undergraduate", "under-grad", "ug", "undergrad",
      "bachelar", "bacheler", "batchelor"],
     "undergrad", "Bachelor of Science"),

    (["diploma", "pgdm", "pgd", "polytechnic", "poly"],
     "diploma", "Post Graduate Diploma"),

    (["certificate", "certification", "certified"],
     "certificate", "Certificate Program"),
]

# ---------------------------------------------------------------------------
# Sentence extraction patterns  (ordered most-specific first)
# ---------------------------------------------------------------------------
_SENTENCE_PATTERNS: list[str] = [
    # "completed / pursuing / have my B.Tech in Computer Science"
    r"(?:complet(?:ed|ing)|pursu(?:ed|ing)|finish(?:ed|ing)|did|doing|have|holds?)\s+"
    r"(?:a\s+|an\s+|my\s+|the\s+)?([A-Z][A-Za-z\.\s]{2,45}?)\s+"
    r"(?:in|from|at|with|specializ)\b",

    # "B.Tech in Computer Science from IIT"
    r"\b([A-Z][A-Za-z\.\s]{1,35}?)\s+in\s+([A-Za-z\s]{3,40}?)\s+"
    r"(?:from|at|with|college|university|institute)\b",

    # "a degree / qualification in X"
    r"\b(?:a|an|my)\s+([A-Za-z\.\s]{3,45}?)\s+degree\b",
    r"\b(?:hold(?:s|ing)?|possess(?:es|ing)?|earned?)\s+"
    r"(?:a\s+|an\s+|the\s+)?([A-Z][A-Za-z\.\s]{2,45})\b",

    # Bare degree at start of string  "B.Tech Computer Science 2022"
    r"^([A-Z][A-Za-z\.\s]{1,30}?)(?:\s+\d{4}|\s*$)",
]

# Field-of-study extraction helper patterns
_FIELD_PATTERNS: list[str] = [
    r"\b(?:in|of|specializ(?:ed|ing)\s+in|majoring\s+in|with\s+(?:a\s+)?(?:focus|major)\s+in)\s+"
    r"([A-Za-z][A-Za-z\s&/\-]{2,50}?)(?:\s+(?:from|at|college|university|department|dept)|[,\.\n]|$)",
    r"\(([A-Za-z][A-Za-z\s&/]{2,40}?)\)",
]


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class L3HeuristicEngine:
    """
    Pure-Python, dependency-free Layer 3 heuristic/NLP engine.

    Designed to be called AFTER L1 and L2 have both failed.
    Also usable standalone for analysis / debugging.
    """

    def __init__(self):
        self._shortcode_map = {k.lower(): v for k, v in _SHORTCODE_MAP.items()}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _light_clean(text: str) -> str:
        """Minimal normalisation — keep case for pattern matching."""
        return re.sub(r"\s{2,}", " ", text.strip())

    @staticmethod
    def _extract_field(text: str) -> Optional[str]:
        """Try to pull a field-of-study string from raw text."""
        for pat in _FIELD_PATTERNS:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                field = m.group(1).strip()
                if len(field) > 2:
                    return field
        return None

    # ------------------------------------------------------------------
    # Strategy 1: Sentence extraction
    # ------------------------------------------------------------------

    def _s1_sentence(self, raw: str) -> Optional[dict]:
        for pat in _SENTENCE_PATTERNS:
            m = re.search(pat, raw, re.IGNORECASE)
            if m:
                degree_mention = m.group(1).strip()
                if len(degree_mention) < 2:
                    continue
                field_mention = self._extract_field(raw)
                conf = 0.72 if field_mention else 0.60
                return {
                    "canonical_degree": degree_mention,
                    "extracted_mention": degree_mention,
                    "field_mention":     field_mention,
                    "confidence":        conf,
                    "strategy":          "S1_sentence",
                }
        return None

    # ------------------------------------------------------------------
    # Strategy 2: Shortcode / abbreviation expansion
    # ------------------------------------------------------------------

    def _s2_shortcode(self, raw: str) -> Optional[dict]:
        # Try the whole cleaned string as a shortcode key
        key = raw.strip().lower().replace(".", "").replace(" ", "")
        if key in self._shortcode_map:
            return {
                "canonical_degree": self._shortcode_map[key],
                "extracted_mention": raw.strip(),
                "field_mention":     None,
                "confidence":        0.80,
                "strategy":          "S2_shortcode",
            }
        # Try token-by-token (first meaningful token)
        tokens = re.split(r"[\s\./,\-]+", raw.strip().lower())
        for tok in tokens:
            if tok in self._shortcode_map:
                return {
                    "canonical_degree": self._shortcode_map[tok],
                    "extracted_mention": tok,
                    "field_mention":     self._extract_field(raw),
                    "confidence":        0.75,
                    "strategy":          "S2_shortcode_token",
                }
        return None

    # ------------------------------------------------------------------
    # Strategy 3: Level keyword detection
    # ------------------------------------------------------------------

    def _s3_level_keyword(self, raw: str) -> Optional[dict]:
        raw_lower = raw.lower()
        for keywords, level_label, default_canonical in _LEVEL_KEYWORD_MAP:
            if any(kw in raw_lower for kw in keywords):
                field_mention = self._extract_field(raw)
                return {
                    "canonical_degree": default_canonical,
                    "extracted_mention": None,
                    "field_mention":     field_mention,
                    "confidence":        0.50,
                    "strategy":          f"S3_level_{level_label}",
                }
        return None

    # ------------------------------------------------------------------
    # Strategy 4: Field-only signal
    # ------------------------------------------------------------------

    def _s4_field_only(self, raw: str) -> Optional[dict]:
        field = self._extract_field(raw)
        if field:
            return {
                "canonical_degree": None,
                "extracted_mention": None,
                "field_mention":     field,
                "confidence":        0.35,
                "strategy":          "S4_field_only",
            }
        return None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def analyze(self, raw_string: str) -> Optional[dict]:
        """
        Run the heuristic cascade on *raw_string*.

        Returns a result dict on any positive signal, or None when the
        text contains no recognisable degree/field information at all.
        Result dict keys:
            canonical_degree   str or None
            extracted_mention  str or None   (the raw extracted text)
            field_mention      str or None
            confidence         float
            strategy           str           (which strategy fired)
            layer_used         "L3"
            engine             ENGINE_ID
        """
        text = self._light_clean(raw_string)

        result = (
            self._s2_shortcode(text)
            or self._s1_sentence(text)
            or self._s3_level_keyword(text)
            or self._s4_field_only(text)
        )

        if result is None:
            return None

        result["layer_used"] = "L3"
        result["engine"]     = ENGINE_ID
        return result

    def normalize(self, raw_string: str) -> dict:
        """
        Wrapper that always returns a structured dict (never raises).
        Matches the interface expected by the orchestrator.
        """
        inner = self.analyze(raw_string)

        if inner:
            return {
                "input":            raw_string,
                "layer_used":       "L3",
                "canonical_degree": inner.get("canonical_degree"),
                "canonical_field":  inner.get("field_mention"),
                "confidence":       inner.get("confidence", 0.0),
                "status":           "review_needed",
                "fuzzy_score":      round(inner.get("confidence", 0.0) * 100, 1),
                "alternatives":     [],
                "engine":           ENGINE_ID,
                "l3_strategy":      inner.get("strategy"),
                "extracted_mention": inner.get("extracted_mention"),
            }

        return {
            "input":            raw_string,
            "layer_used":       "unresolved",
            "canonical_degree": None,
            "canonical_field":  None,
            "confidence":       0.0,
            "status":           "unresolved",
            "fuzzy_score":      0,
            "alternatives":     [],
            "engine":           ENGINE_ID,
            "l3_strategy":      None,
            "extracted_mention": None,
        }

    def batch_normalize(self, inputs: list[str]) -> list[dict]:
        return [self.normalize(s) for s in inputs]


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    engine = L3HeuristicEngine()

    UNSTRUCTURED_CASES = [
        # Conversational sentences
        "I completed my B.Tech in Computer Science from IIT Delhi in 2022",
        "She is pursuing her Masters in Data Science at IIM Ahmedabad",
        "He holds a Bachelor of Business Administration from DU",
        "Finished my PhD in Biotechnology last year",
        "Have a diploma in Mechanical Engineering from a polytechnic",
        # Abbreviations without context
        "BCA",
        "MBA",
        "BSc",
        "LLB",
        "PGDM",
        # Mixed / ambiguous
        "Graduate from Computer Science department",
        "Undergraduate degree — Electrical Engineering",
        "Some random text with no educational information",
        # Already-structured (should still work)
        "B.Tech (CSE)",
        "Master of Technology in Artificial Intelligence",
    ]

    while True:
        print("\n" + "=" * 65)
        print("  CV MANAGER · Layer 3 Heuristic Engine   [standalone CLI]")
        print("=" * 65)
        print("  1. Run default test suite (unstructured / conversational)")
        print("  2. Enter custom text to analyse")
        print("  3. Exit")

        choice = input("\n  Choice [1/2/3]: ").strip()

        if choice == "1":
            print(f"\n  {len(UNSTRUCTURED_CASES)} inputs · L3 Heuristic cascade")
            W = {"inp": 46, "canon": 34, "conf": 6}
            div = "  " + "─" * (W["inp"] + W["canon"] + W["conf"] + 3 * 2 + 8)
            print()
            print(f"  {'INPUT':<{W['inp']}}  {'CANONICAL':<{W['canon']}}  "
                  f"{'CONF':<{W['conf']}}  STRATEGY")
            print(div)
            for raw in UNSTRUCTURED_CASES:
                r = engine.analyze(raw)
                inp = raw[:W["inp"] - 1]
                if r:
                    canon = (r["canonical_degree"] or "(field only)")[:W["canon"] - 1]
                    conf  = f"{r['confidence']:.2f}"
                    strat = r["strategy"]
                    field = r.get("field_mention") or ""
                    print(f"  {inp:<{W['inp']}}  {canon:<{W['canon']}}  {conf:<{W['conf']}}  {strat}")
                    if field:
                        print(f"  {'':>{W['inp']}}  ↳ field: {field}")
                else:
                    print(f"  {inp:<{W['inp']}}  {'— no signal —':<{W['canon']}}  {'—':<{W['conf']}}  —")
            print(div)


        elif choice == "2":
            raw = input("\n  Enter any text containing a degree mention: ").strip()
            if not raw:
                continue
            r = engine.analyze(raw)
            print("\n  " + "─" * 55)
            if r:
                print(f"  Strategy         : {r['strategy']}")
                print(f"  Canonical Degree : {r['canonical_degree'] or 'Not extracted'}")
                print(f"  Field Mention    : {r['field_mention'] or 'None'}")
                print(f"  Extracted Text   : {r['extracted_mention'] or '—'}")
                print(f"  Confidence       : {r['confidence']:.2f}")
                print(f"  Layer            : {r['layer_used']}")
            else:
                print("  No degree signal detected in the input text.")
            print("  " + "─" * 55)

        elif choice == "3":
            sys.exit(0)
        else:
            print("  Invalid choice.")
