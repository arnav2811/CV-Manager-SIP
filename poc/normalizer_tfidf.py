"""
CV Manager Normalizer — TF-IDF Character N-Gram Engine  (Layer 2 · Engine B-2)
===============================================================================
Uses scikit-learn's TfidfVectorizer with character 3–5-grams to build a sparse
vector index of all known degree aliases. Input strings are vectorized and
matched via cosine similarity.

Bug-fixes vs v2.3.0
  • Replaced \\bin\\b with \\s+in\\s+ in clean() — prevents false splits on
    words containing "in" (Admin, Administration, Engineering …).
  • Consistent _clean_token() helper shared with other engines.
  • Structured result dict now always includes the 'engine' key.

Run:  python normalizer_tfidf.py
"""

import csv
import json
import os
import re
import sys

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class NormalizerTFIDF:
    """TF-IDF character n-gram 3-layer degree normalizer."""

    ENGINE_ID = "B-2_TFIDF"

    def __init__(self, data_dir: str = "../data"):
        self.data_dir        = data_dir
        self.degree_aliases: dict[str, str] = {}
        self.field_aliases:  dict[str, str] = {}
        self.canonical_degrees: set[str]    = set()

        self.vectorizer: TfidfVectorizer | None = None
        self.ref_matrix  = None
        self.ref_choices: list[str] = []

        self._load_aliases()
        self._build_index()

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_aliases(self) -> None:
        degree_csv  = os.path.join(self.data_dir, "degree_aliases.csv")
        degree_json = os.path.join(self.data_dir, "degree_dictionary.json")
        field_csv   = os.path.join(self.data_dir, "field_of_study_aliases.csv")

        if not os.path.exists(degree_csv) or not os.path.exists(field_csv):
            print("[TF-IDF] ERROR: Alias files not found.")
            return

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

        print(f"[TF-IDF] Loaded {len(self.degree_aliases):,} degree aliases  |  "
              f"{len(self.field_aliases):,} field aliases")

    def _build_index(self) -> None:
        self.ref_choices = list(self.degree_aliases.keys())
        if not self.ref_choices:
            return
        self.vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(3, 5))
        self.ref_matrix = self.vectorizer.fit_transform(self.ref_choices)
        print(f"[TF-IDF] Index built — {len(self.ref_choices):,} alias vectors")

    # ------------------------------------------------------------------
    # String helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _clean_token(raw: str) -> str:
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
        return " ".join(w for w in norm.split() if w != "in")

    def clean(self, raw_string: str) -> tuple[str, str | None]:
        """Split raw education string into (degree_part, field_part)."""
        raw_string = str(raw_string).strip()
        field_part = None

        m = re.split(r"\s+-\s+|\s+/\s+|\s+in\s+", raw_string, maxsplit=1,
                     flags=re.IGNORECASE)
        if len(m) == 2:
            raw_string = m[0].strip()
            field_part = m[1].strip()
        else:
            paren = re.search(r"\((.*?)\)", raw_string)
            if paren:
                field_part = paren.group(1).strip()
                raw_string = re.sub(r"\(.*?\)", "", raw_string).strip()
            else:
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
    # Layer 2 — TF-IDF cosine similarity
    # ------------------------------------------------------------------

    def layer2_fuzzy(self, cleaned: str,
                     threshold_auto: float = 0.80,
                     threshold_flag: float = 0.60) -> dict | None:
        if not self.ref_choices or self.vectorizer is None:
            return None

        try:
            query_vec    = self.vectorizer.transform([cleaned])
            similarities = cosine_similarity(query_vec, self.ref_matrix).flatten()
        except Exception as exc:
            print(f"[TF-IDF] layer2 error: {exc}")
            return None

        top_idxs = np.argsort(similarities)[::-1][:8]
        if len(top_idxs) == 0:
            return None

        best_idx       = int(top_idxs[0])
        score          = float(similarities[best_idx])
        best_canonical = self.degree_aliases[self.ref_choices[best_idx]]

        seen     = {best_canonical}
        alt_list = []
        for idx in top_idxs:
            canon = self.degree_aliases[self.ref_choices[int(idx)]]
            if canon not in seen:
                seen.add(canon)
                alt_list.append((canon, round(float(similarities[int(idx)]), 3)))
            if len(alt_list) >= 3:
                break

        base = {
            "canonical_degree": best_canonical,
            "confidence":       round(score, 4),
            "fuzzy_score":      round(score * 100, 1),
            "alternatives":     alt_list,
            "engine":           self.ENGINE_ID,
        }

        if score >= threshold_auto:
            return {**base, "status": "fuzzy_matched",  "layer_used": "L2_TFIDF"}
        if score >= threshold_flag:
            return {**base, "status": "review_needed",  "layer_used": "L2_TFIDF"}
        return None

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def normalize(self, raw_string: str) -> dict:
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

        l1 = self.layer1_lookup(cleaned)
        if l1:
            result.update(l1)
            return result

        l2 = self.layer2_fuzzy(cleaned)
        if l2:
            result.update(l2)

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
    n = NormalizerTFIDF(data_dir)

    TEST_CASES = [
        "B.Tech", "BTech", "Bachelor of Technology", "Bacheler of Technology",
        "B. Tech in CSE", "M.Tech (Computer Science)", "MBA",
        "Bachellor of Technolgy in CSE", "BE Hons", "12th", "B.Pharma",
        "Bachelor of Business Administration", "Bachelor of Business Admin",
        "BBA", "Kuchh bhi degree",
    ]

    VERSION = "3.6.5"

    while True:
        print()
        print("╔" + "═" * 64 + "╗")
        print("║" + " CV MANAGER · TF-IDF Engine (B-2) · Standalone CLI ".center(64) + "║")
        print("║" + f" Version {VERSION}  ·  char n-gram cosine similarity ".center(64) + "║")
        print("╚" + "═" * 64 + "╝")
        print()
        print("    1.  Run default test suite")
        print("    2.  Enter custom degree string")
        print("    3.  Exit")
        print("─" * 68)

        choice = input("\n  Choice [1/2/3]: ").strip()

        if choice == "1":
            results = n.batch_normalize(TEST_CASES)
            W = {"inp": 33, "canon": 32, "layer": 12, "conf": 6}
            div = "  " + "─" * (W["inp"] + W["canon"] + W["layer"] + W["conf"] + 4 * 2 + 6)
            print(f"\n  {len(TEST_CASES)} inputs · TF-IDF char n-gram engine")
            print()
            print(f"  {'INPUT':<{W['inp']}}  {'CANONICAL':<{W['canon']}}  "
                  f"{'LAYER':<{W['layer']}}  {'CONF':<{W['conf']}}  STATUS")
            print(div)
            stats = {"L1": 0, "L2": 0, "review": 0, "unresolved": 0}
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
                if   layer.startswith("L1"):   stats["L1"]         += 1
                elif "L2" in layer:            stats["L2"]         += 1
                elif status == "review_needed": stats["review"]    += 1
                else:                           stats["unresolved"] += 1
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
            print("  NORMALISATION RESULT  (TF-IDF Engine B-2)")
            print(div)
            print(f"  {'Input':<{W}}: {r['input']}")
            print(f"  {'Canonical Degree':<{W}}: {r.get('canonical_degree') or '—'}")
            print(f"  {'Canonical Field':<{W}}: {r.get('canonical_field') or '—'}")
            print(f"  {'Layer Used':<{W}}: {r.get('layer_used')}")
            conf = r.get('confidence', 0)
            bar  = "█" * int(conf * 20) + "░" * (20 - int(conf * 20))
            print(f"  {'Confidence':<{W}}: {conf:.4f}  [{bar}]")
            print(f"  {'Status':<{W}}: {r.get('status')}")
            if r.get("alternatives"):
                print(f"\n  {'Alternatives':<{W}}:")
                for alt, sc in r["alternatives"]:
                    print(f"  {'':{W}}  • {alt:<38}  score: {sc:.3f}")
            print(div)

        elif choice == "3":
            print("\n  Goodbye.\n")
            import sys; sys.exit(0)
        else:
            print("  Invalid choice.")
