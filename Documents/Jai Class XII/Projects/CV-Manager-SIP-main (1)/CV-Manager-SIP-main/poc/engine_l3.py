"""
CV Manager — Layer 3 NLP / Heuristic Engine
============================================
Handles unstructured and conversational text that L1 (exact match) and
L2 (fuzzy) fail to resolve.  Implemented as a pure-Python regex cascade —
no external NLP dependencies required.

Strategy cascade (applied in order until a result is found)
-----------------------------------------------------------
S2  Shortcode / abbreviation expansion
    Hard-coded map of single-token abbreviations → canonical degree.
    Catches standalone tokens like "BE", "ME", "MS", "PhD", "BCA"
    that survive L1/L2 because they have no surrounding context.

S1  Sentence extraction
    Regex patterns pull degree mentions from natural-language sentences,
    e.g. "I completed my B.Tech in CSE from IIT Delhi in 2022".
    Extracted text is passed through the shortcode + PhD canonicalizer
    before being returned.

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

Version: 3.6.5
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
    "be":       "Bachelor of Engineering",
    "beng":     "Bachelor of Engineering",
    "b.eng":    "Bachelor of Engineering",
    "btech":    "Bachelor of Technology",
    "b.tech":   "Bachelor of Technology",
    "bе":       "Bachelor of Engineering",      # cyrillic е safety
    "me":       "Master of Engineering",
    "meng":     "Master of Engineering",
    "m.eng":    "Master of Engineering",
    "mtech":    "Master of Technology",
    "m.tech":   "Master of Technology",
    "mе":       "Master of Engineering",
    # Combined slash-forms common in Indian CVs
    "btech/be": "Bachelor of Technology",
    "btechbe":  "Bachelor of Technology",
    "be/btech": "Bachelor of Technology",
    # Science
    "bsc":      "Bachelor of Science",
    "b.sc":     "Bachelor of Science",
    "msc":      "Master of Science",
    "m.sc":     "Master of Science",
    "bs":       "Bachelor of Science",
    "ms":       "Master of Science",
    # Arts
    "ba":       "Bachelor of Arts",
    "ma":       "Master of Arts",
    # Commerce / Business
    "bcom":     "Bachelor of Commerce",
    "b.com":    "Bachelor of Commerce",
    "mcom":     "Master of Commerce",
    "m.com":    "Master of Commerce",
    "bba":      "Bachelor of Business Administration",
    "b.b.a":    "Bachelor of Business Administration",
    "mba":      "Master of Business Administration",
    "m.b.a":    "Master of Business Administration",
    "emba":     "Master of Business Administration",
    # Computer
    "bca":      "Bachelor of Computer Applications",
    "b.c.a":    "Bachelor of Computer Applications",
    "mca":      "Master of Computer Applications",
    "m.c.a":    "Master of Computer Applications",
    # PhD / Research
    "phd":      "Doctor of Philosophy",
    "ph.d":     "Doctor of Philosophy",
    "ph.d.":    "Doctor of Philosophy",
    "dphil":    "Doctor of Philosophy",
    "d.phil":   "Doctor of Philosophy",
    # Education
    "med":      "Master of Education",
    "bed":      "Bachelor of Education",
    "b.ed":     "Bachelor of Education",
    "m.ed":     "Master of Education",
    # Pharmacy
    "bpharma":  "Bachelor of Pharmacy",
    "b.pharma": "Bachelor of Pharmacy",
    "mpharma":  "Master of Pharmacy",
    "m.pharma": "Master of Pharmacy",
    "bpharm":   "Bachelor of Pharmacy",
    "mpharm":   "Master of Pharmacy",
    # School
    "12th":     "Senior Secondary (Class XII)",
    "10th":     "Secondary (Class X)",
    "hsc":      "Senior Secondary (Class XII)",
    "ssc":      "Secondary (Class X)",
    # Law
    "llb":      "Bachelor of Laws",
    "ll.b":     "Bachelor of Laws",
    "llm":      "Master of Laws",
    "ll.m":     "Master of Laws",
    # Design
    "bdes":     "Bachelor of Design",
    "mdes":     "Master of Design",
    # Architecture
    "b.arch":   "Bachelor of Architecture",
    "march":    "Master of Architecture",
    # Diploma
    "pgdm":     "Post Graduate Diploma",
    "pgd":      "Post Graduate Diploma",
    "pgdba":    "Post Graduate Diploma in Business Administration",
    "pg":       "Post Graduate Diploma",
    # Medicine
    "mbbs":     "Bachelor of Medicine and Bachelor of Surgery",
    "bds":      "Bachelor of Dental Surgery",
}

# ---------------------------------------------------------------------------
# PhD canonical variants — any extracted text that looks like a PhD alias
# should be normalized to the single canonical string
# ---------------------------------------------------------------------------
_PHD_PATTERNS: list[str] = [
    r"ph\.?\s*d\.?",
    r"d\.?\s*phil\.?",
    r"doctor(?:ate)?\s+of\s+philosophy",
    r"doctoral\s+degree",
    r"doctorate",
]
_PHD_REGEX = re.compile(
    r"(?:" + "|".join(_PHD_PATTERNS) + r")",
    re.IGNORECASE,
)

_DEGREE_SIGNAL_REGEX = re.compile(
    r"\b(?:"
    r"b\.?\s*tech|m\.?\s*tech|b\.?\s*eng|m\.?\s*eng|"
    r"b\.?\s*e\b|m\.?\s*e\b|b\.?\s*sc|m\.?\s*sc|"
    r"b\.?\s*a\b|m\.?\s*a\b|b\.?\s*com|m\.?\s*com|"
    r"bba|mba|bca|mca|llb|llm|mbbs|bds|"
    r"b\.?\s*ed|m\.?\s*ed|b\.?\s*arch|b\.?\s*pharm(?:a)?|m\.?\s*pharm(?:a)?|"
    r"ph\.?\s*d|d\.?\s*phil|pgdm|pgd|12th|10th|"
    r"bachelor|bachelors|master|masters|doctorate|doctoral|diploma|polytechnic|certificate"
    r")\b",
    re.IGNORECASE,
)

_DEGREE_PREFIX_REGEX = re.compile(
    r"^\s*("
    r"b\.?\s*tech|m\.?\s*tech|b\.?\s*eng|m\.?\s*eng|"
    r"b\.?\s*e\b|m\.?\s*e\b|b\.?\s*sc|m\.?\s*sc|"
    r"b\.?\s*a\b|m\.?\s*a\b|b\.?\s*com|m\.?\s*com|"
    r"bba|mba|bca|mca|llb|llm|mbbs|bds|"
    r"b\.?\s*ed|m\.?\s*ed|b\.?\s*arch|b\.?\s*pharm(?:a)?|m\.?\s*pharm(?:a)?|"
    r"ph\.?\s*d|d\.?\s*phil|pgdm|pgd|12th|10th"
    r")\b",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Field acronym map — catches compact field abbreviations that bypass the
# full alias CSV (e.g., "CSE", "ECE", "IT", "AI & ML", "CS")
# ---------------------------------------------------------------------------
_FIELD_ACRONYM_MAP: dict[str, str] = {
    # Computer / IT
    "cse":      "Computer Science and Engineering",
    "cs":       "Computer Science and Engineering",
    "compsci":  "Computer Science and Engineering",
    "it":       "Information Technology",
    "is":       "Information Technology",
    # Electronics
    "ece":      "Electronics and Communication Engineering",
    "ec":       "Electronics and Communication Engineering",
    "eee":      "Electrical Engineering",
    "ee":       "Electrical Engineering",
    "el":       "Electrical Engineering",
    # Mechanical
    "me":       "Mechanical Engineering",
    "mech":     "Mechanical Engineering",
    "mechengg": "Mechanical Engineering",
    # Civil
    "ce":       "Civil Engineering",
    "civil":    "Civil Engineering",
    # Chemical
    "che":      "Chemical Engineering",
    "chem":     "Chemical Engineering",
    "chemengg": "Chemical Engineering",
    # AI / DS
    "ai":       "Artificial Intelligence and Machine Learning",
    "ml":       "Artificial Intelligence and Machine Learning",
    "ds":       "Data Science",
    # Other engineering
    "ie":       "Instrumentation Engineering",
    "iandc":    "Instrumentation Engineering",
    "i&c":      "Instrumentation Engineering",
    "aero":     "Aerospace Engineering",
    "aeroengg": "Aerospace Engineering",
    "biotech":  "Biotechnology Engineering",
    "biotechengg": "Biotechnology Engineering",
    "enviro":   "Environmental Engineering",
    "maths":    "Mathematics",
    "stats":    "Statistics",
    "phy":      "Physics",
    "bio":      "Biology",
    "env":      "Environmental Science",
    "zoo":      "Zoology",
    "microbio": "Microbiology",
    "biochem":  "Biochemistry",
    # Commerce / Business
    "fin":      "Finance",
    "financeandaccounts": "Finance",
    "hr":       "Human Resources Management",
    "mktg":     "Marketing",
    "se":       "Software Engineering",
    "softwareengg": "Software Engineering",
    "infosec":  "Cybersecurity",
    "networksecurity": "Cybersecurity",
    "informationsecurity": "Cybersecurity",
}

# Stopwords: extracted field tokens that are noise (institution names, cities, etc.)
_FIELD_STOPWORDS: set[str] = {
    # Prepositions / articles
    "from", "at", "in", "the", "a", "an", "and", "of", "or",
    "by", "with", "for", "to", "on", "my", "his", "her", "their",
    # Academic structure words
    "college", "university", "institute", "institution", "school",
    "batch", "dept", "department", "campus", "faculty", "centre", "center",
    "hons", "hons.", "honors", "honours", "programme", "program", "course",
    "semester", "year", "class", "grade", "section", "branch",
    # Common Indian institution names that leak through field regex
    "iit", "nit", "iiit", "bits", "vit", "srmist", "manipal",
    "amity", "jadavpur", "anna", "pune", "delhi", "mumbai", "bangalore",
    "chennai", "hyderabad", "kolkata", "chandigarh", "lucknow", "jaipur",
    "bhu", "banaras", "pilani", "roorkee", "kharagpur", "madras",
    "bombay", "kanpur", "guwahati", "dhanbad", "varanasi", "patna",
    "indore", "bhopal", "nagpur", "ahmedabad", "surat", "kota",
    "du", "jnu", "ignou", "amu", "jamia", "dtu", "nsut", "iisc",
    # International institution abbreviations
    "mit", "stanford", "harvard", "oxford", "cambridge",
    # Degree words (should not be field)
    "degree", "diploma", "certificate", "qualification",
}

# ---------------------------------------------------------------------------
# Level keyword groups  →  most specific default canonical
# ---------------------------------------------------------------------------
_LEVEL_KEYWORD_MAP: list[tuple[list[str], str, str]] = [
    # (keywords,                     level_label,        default_canonical)
    (["phd", "doctorate", "doctoral", "ph.d", "dphil"],
     "doctoral", "Doctor of Philosophy"),

    (["master", "masters", "mtech", "m.tech", "msc", "m.sc", "mba",
      "m.b.a", "postgrad", "post-grad", "post grad", "pg", "meng", "m.eng"],
     "postgrad", "Master of Science"),

    (["bachelor", "bachelors", "btech", "b.tech", "bsc", "b.sc",
      "undergraduate", "under-grad", "ug", "undergrad",
      "bachelar", "bacheler", "batchelor", "bachelorofarts",
      "bachelorofscience", "bachelorofengineering", "bachelorofcommerce",
      "bachelorofbusiness", "bachelorofcomputer"],
     "undergrad", "Bachelor of Science"),

    (["diploma", "pgdm", "pgd", "polytechnic", "poly"],
     "diploma", "Post Graduate Diploma"),

    (["certificate", "certification", "certified"],
     "certificate", "Certificate Program"),
]

_GENERIC_LEVEL_CANONICAL: dict[str, str] = {
    "master": "Master of Science",
    "masters": "Master of Science",
    "postgrad": "Master of Science",
    "post grad": "Master of Science",
    "post graduate": "Master of Science",
    "bachelor": "Bachelor of Science",
    "bachelors": "Bachelor of Science",
    "undergrad": "Bachelor of Science",
    "under graduate": "Bachelor of Science",
    "undergraduate": "Bachelor of Science",
    "diploma": "Post Graduate Diploma",
    "polytechnic": "Post Graduate Diploma",
    "certificate": "Certificate Program",
    "certification": "Certificate Program",
}

# ---------------------------------------------------------------------------
# Sentence extraction patterns  (ordered most-specific first)
# ---------------------------------------------------------------------------
_SENTENCE_PATTERNS: list[str] = [
    # "completed / pursuing / have my B.Tech in Computer Science"
    r"(?:complet(?:ed|ing)|pursu(?:ed|ing)|finish(?:ed|ing)|did|doing|have|holds?)\\s+"
    r"(?:a\\s+|an\\s+|my\\s+|the\\s+)?([A-Z][A-Za-z\\.\\s]{2,45}?)\\s+"
    r"(?:in|from|at|with|specializ)\\b",

    # "B.Tech in Computer Science from IIT"
    r"\\b([A-Z][A-Za-z\\.\\s]{1,35}?)\\s+in\\s+([A-Za-z\\s]{3,40}?)\\s+"
    r"(?:from|at|with|college|university|institute)\\b",

    # "a degree / qualification in X"
    r"\\b(?:a|an|my)\\s+([A-Za-z\\.\\s]{3,45}?)\\s+degree\\b",
    r"\\b(?:hold(?:s|ing)?|possess(?:es|ing)?|earned?)\\s+"
    r"(?:a\\s+|an\\s+|the\\s+)?([A-Z][A-Za-z\\.\\s]{2,45})\\b",

    # Bare degree at start of string  "B.Tech Computer Science 2022"
    r"^([A-Z][A-Za-z\\.\\s]{1,30}?)(?:\\s+\\d{4}|\\s*$)",
]

# Re-compile without the double-escaped backslashes for actual use
_SENTENCE_PATTERNS_COMPILED = [
    re.compile(
        r"(?:complet(?:ed|ing)|pursu(?:ed|ing)|finish(?:ed|ing)|did|doing|have|holds?)\s+"
        r"(?:a\s+|an\s+|my\s+|the\s+)?([A-Z][A-Za-z\.\s]{2,45}?)\s+"
        r"(?:in|from|at|with|specializ)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b([A-Z][A-Za-z\.\s]{1,35}?)\s+in\s+([A-Za-z\s]{3,40}?)\s+"
        r"(?:from|at|with|college|university|institute)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:a|an|my)\s+([A-Za-z\.\s]{3,45}?)\s+degree\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:hold(?:s|ing)?|possess(?:es|ing)?|earned?)\s+"
        r"(?:a\s+|an\s+|the\s+)?([A-Z][A-Za-z\.\s]{2,45})\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"^([A-Z][A-Za-z\.\s]{1,30}?)(?:\s+\d{4}|\s*$)",
        re.IGNORECASE,
    ),
]

# Field-of-study extraction helper patterns
_FIELD_PATTERNS: list[re.Pattern] = [
    re.compile(
        r"\b(?:in|of|specializ(?:ed|ing)\s+in|majoring\s+in|with\s+(?:a\s+)?(?:focus|major)\s+in)\s+"
        r"([A-Za-z][A-Za-z\s&/\-]{1,50}?)(?:\s+(?:from|at|college|university|department|dept)|[,\.\n]|$)",
        re.IGNORECASE,
    ),
    re.compile(
        r"\(([A-Za-z][A-Za-z\s&/]{1,40}?)\)",
        re.IGNORECASE,
    ),
    # Catch compact acronym forms: "in CSE", "in ECE", "in IT"
    re.compile(
        r"\b(?:in|of|specialization)\s+([A-Z][A-Z0-9\s&/\.]{1,12}?)(?:\s+(?:from|at|college|university|batch)|[,\.\n]|$)",
        re.IGNORECASE,
    ),
]


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------

class L3HeuristicEngine:
    """
    Pure-Python, dependency-free Layer 3 heuristic/NLP engine.

    Designed to be called AFTER L1 and L2 have both failed.
    Also usable standalone for analysis / debugging.

    v3.6.5 improvements
    --------------------
    • Expanded _SHORTCODE_MAP with BEng, B.Eng, slash-combined forms,
      EMBA, B.B.A, M.B.A, B.C.A, M.C.A, B.Ed, M.Ed, B.Arch, MBBS, BDS.
    • Post-processes S1 sentence-extracted text through the shortcode map
      so raw mentions like "B.Tech" → "Bachelor of Technology" instead of
      being returned verbatim.
    • PhD variant normalization — any result containing a PhD alias is
      canonicalized to "Doctor of Philosophy".
    • Field acronym map for compact field abbreviations (CSE, ECE, IT, AI…).
    • Relaxed field minimum length from > 2 to > 1 with a stopword blocklist.
    • Improved _FIELD_PATTERNS to catch compact acronym field forms.
    """

    def __init__(self):
        # Normalize shortcode map keys: strip dots and spaces for lookup
        self._shortcode_map: dict[str, str] = {}
        for k, v in _SHORTCODE_MAP.items():
            normalized_key = k.lower().replace(".", "").replace(" ", "").replace("/", "")
            self._shortcode_map[normalized_key] = v
            # Also store original key (already lowercased)
            self._shortcode_map[k.lower()] = v

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _light_clean(text: str) -> str:
        """Minimal normalisation — keep case for pattern matching."""
        return re.sub(r"\s{2,}", " ", text.strip())

    def _try_shortcode(self, raw: str) -> Optional[str]:
        """
        Attempt to map *raw* (a degree mention string) to a canonical degree
        via the shortcode map.  Returns canonical string or None.
        """
        # Strip common noise suffixes before lookup
        cleaned = raw.strip().lower()
        for suffix in (" degree", " hons", " hons.", " (hons)", " honors",
                       " with specialization", " programme", " program"):
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)].strip()

        # Normalize: remove dots, spaces, slashes
        key1 = cleaned.replace(".", "").replace(" ", "").replace("/", "")
        key2 = cleaned  # try with spaces too

        return (
            self._shortcode_map.get(key1)
            or self._shortcode_map.get(key2)
        )

    @staticmethod
    def _canonicalize_phd(text: str) -> Optional[str]:
        """If text matches any PhD alias, return the canonical string."""
        if _PHD_REGEX.search(text):
            return "Doctor of Philosophy"
        return None

    def _canonicalize_degree_mention(self, raw_mention: str) -> Optional[str]:
        """
        Try to turn a raw extracted mention into a canonical degree.
        Order: shortcode lookup -> degree-prefix lookup -> PhD normalization
        -> return None (caller will use the raw mention only if it still has
        a degree signal).
        """
        if not raw_mention or len(raw_mention.strip()) < 2:
            return None
        canon = self._try_shortcode(raw_mention)
        if canon:
            return canon
        prefix = _DEGREE_PREFIX_REGEX.search(raw_mention)
        if prefix:
            canon = self._try_shortcode(prefix.group(1))
            if canon:
                return canon
        generic_key = re.sub(r"[^a-z]+", " ", raw_mention.lower()).strip()
        if generic_key in _GENERIC_LEVEL_CANONICAL:
            return _GENERIC_LEVEL_CANONICAL[generic_key]
        canon = self._canonicalize_phd(raw_mention)
        return canon

    def _extract_field(self, text: str) -> Optional[str]:
        """Try to pull a field-of-study string from raw text."""
        for pat in _FIELD_PATTERNS:
            m = pat.search(text)
            if m:
                field = m.group(1).strip()
                # Filter stopwords and very short noise
                if len(field) <= 1:
                    continue
                if field.lower() in _FIELD_STOPWORDS:
                    continue
                # Try acronym map first
                acronym_key = field.lower().replace(".", "").replace(" ", "").replace("&", "").replace("/", "")
                if acronym_key in _FIELD_ACRONYM_MAP:
                    return _FIELD_ACRONYM_MAP[acronym_key]
                # Also try space-separated version
                acronym_key2 = field.lower().strip()
                if acronym_key2 in _FIELD_ACRONYM_MAP:
                    return _FIELD_ACRONYM_MAP[acronym_key2]
                if len(field) > 2:
                    return field
        return None

    # ------------------------------------------------------------------
    # Strategy 1: Sentence extraction
    # ------------------------------------------------------------------

    def _s1_sentence(self, raw: str) -> Optional[dict]:
        for pat in _SENTENCE_PATTERNS_COMPILED:
            m = pat.search(raw)
            if m:
                raw_mention = m.group(1).strip()
                if len(raw_mention) < 2:
                    continue
                # Attempt to canonicalize the raw mention
                canonical = self._canonicalize_degree_mention(raw_mention)
                if not canonical and not _DEGREE_SIGNAL_REGEX.search(raw_mention):
                    continue
                field_mention = self._extract_field(raw)
                conf = 0.72 if field_mention else 0.60

                if canonical:
                    # Successfully canonicalized — higher confidence
                    return {
                        "canonical_degree":  canonical,
                        "extracted_mention": raw_mention,
                        "field_mention":     field_mention,
                        "confidence":        conf,
                        "strategy":          "S1_sentence_canonical",
                    }
                else:
                    # Could not canonicalize — return raw mention as-is with lower conf
                    return {
                        "canonical_degree":  raw_mention,
                        "extracted_mention": raw_mention,
                        "field_mention":     field_mention,
                        "confidence":        max(conf - 0.10, 0.35),
                        "strategy":          "S1_sentence",
                    }
        return None

    # ------------------------------------------------------------------
    # Strategy 2: Shortcode / abbreviation expansion
    # ------------------------------------------------------------------

    def _s2_shortcode(self, raw: str) -> Optional[dict]:
        # Try the whole cleaned string as a shortcode key
        canon = self._try_shortcode(raw)
        if canon:
            return {
                "canonical_degree": canon,
                "extracted_mention": raw.strip(),
                "field_mention":     self._extract_field(raw),
                "confidence":        0.80,
                "strategy":          "S2_shortcode",
            }
        # Try token-by-token (first meaningful token)
        tokens = re.split(r"[\s\./,\-]+", raw.strip().lower())
        for tok in tokens:
            if len(tok) < 2:
                continue
            tok_key = tok.replace(".", "").replace(" ", "")
            canon = self._shortcode_map.get(tok_key) or self._shortcode_map.get(tok)
            if canon:
                return {
                    "canonical_degree": canon,
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

        # Final PhD normalization pass — catch any remaining raw PhD aliases
        if result.get("canonical_degree"):
            phd = self._canonicalize_phd(str(result["canonical_degree"]))
            if phd:
                result["canonical_degree"] = phd

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
    if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
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
        "BEng",
        "b.tech/be",
        # PhD variants that used to fail
        "PHD degree",
        "Ph.D with specialization",
        "DPhil Hons degree",
        # Mixed / ambiguous
        "Graduate from Computer Science department",
        "Undergraduate degree — Electrical Engineering",
        "Some random text with no educational information",
        # Already-structured (should still work)
        "B.Tech (CSE)",
        "Master of Technology in Artificial Intelligence",
        # Compact abbreviated fields
        "BTech ECE 2022",
        "Currently pursuing B.Tech in ECE from IIT",
        "B.Sc in IT from Delhi University",
    ]

    VERSION = "3.6.5"

    while True:
        print()
        print("╔" + "═" * 62 + "╗")
        print("║" + " CV MANAGER · Layer 3 Heuristic Engine".center(62) + "║")
        print("║" + f" Version {VERSION}  ·  standalone CLI ".center(62) + "║")
        print("╚" + "═" * 62 + "╝")
        print()
        print("  1.  Run default test suite (unstructured / conversational)")
        print("  2.  Enter custom text to analyse")
        print("  3.  Exit")

        choice = input("\n  Choice [1/2/3]: ").strip()

        if choice == "1":
            W = {"inp": 42, "canon": 36, "conf": 6}
            div = "  " + "─" * (W["inp"] + W["canon"] + W["conf"] + 3 * 3 + 10)
            print(f"\n  {len(UNSTRUCTURED_CASES)} inputs · L3 Heuristic cascade  (v{VERSION})")
            print()
            print(f"  {'INPUT':<{W['inp']}}  {'CANONICAL DEGREE':<{W['canon']}}  {'CONF':<{W['conf']}}  STRATEGY")
            print(div)
            stats = {"resolved": 0, "field_only": 0, "no_signal": 0}
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
                    if r["canonical_degree"]:
                        stats["resolved"] += 1
                    else:
                        stats["field_only"] += 1
                else:
                    print(f"  {inp:<{W['inp']}}  {'— no signal —':<{W['canon']}}  {'—':<{W['conf']}}  —")
                    stats["no_signal"] += 1
            print(div)
            total = len(UNSTRUCTURED_CASES)
            print()
            print(f"  {'OUTCOME':<16}  {'N':>4}  {'%':>5}")
            print(f"  {'─'*16}  {'─'*4}  {'─'*5}")
            for k, v in stats.items():
                if v:
                    print(f"  {k:<16}  {v:>4}  {v/total*100:>4.0f}%")

        elif choice == "2":
            raw = input("\n  Enter any text containing a degree mention: ").strip()
            if not raw:
                continue
            r = engine.analyze(raw)
            div = "  " + "─" * 60
            print(f"\n{div}")
            print("  ANALYSIS RESULT")
            print(div)
            if r:
                W = 20
                print(f"  {'Strategy':<{W}} : {r['strategy']}")
                print(f"  {'Canonical Degree':<{W}} : {r['canonical_degree'] or 'Not extracted'}")
                print(f"  {'Field Mention':<{W}} : {r['field_mention'] or 'None'}")
                print(f"  {'Extracted Text':<{W}} : {r['extracted_mention'] or '—'}")
                print(f"  {'Confidence':<{W}} : {r['confidence']:.2f}")
                print(f"  {'Layer':<{W}} : {r['layer_used']}")
            else:
                print("  No degree signal detected in the input text.")
            print(div)

        elif choice == "3":
            print("\n  Goodbye.\n")
            sys.exit(0)
        else:
            print("  Invalid choice.")
