"""
CV Manager — Layer 3 Contract Tests
=====================================
Guards the canonical_degree contract so raw free text cannot
be returned as a canonical degree.

Run:  python -m unittest discover -s tests -v
"""

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "poc"))

from engine_l3 import L3HeuristicEngine


class TestL3Contract(unittest.TestCase):
    """Ensure canonical_degree only contains trusted canonical values or None."""

    def setUp(self):
        self.engine = L3HeuristicEngine()

    # ── Core contract tests ───────────────────────────────────────────

    def test_garbage_degree_does_not_become_canonical(self):
        """Raw nonsense text must never leak into canonical_degree."""
        result = self.engine.normalize("Kuchh bhi degree")
        self.assertIsNone(
            result["canonical_degree"],
            f"Expected None, got '{result['canonical_degree']}' — "
            "raw text leaked into canonical_degree",
        )

    def test_masters_sentence_falls_back_to_level_keyword(self):
        """'Masters' is not in shortcode map; S3 should resolve it to
        'Master of Science' and extract 'Data Science' as the field."""
        result = self.engine.normalize(
            "I completed my Masters in Data Science from IIT"
        )
        self.assertEqual(result["canonical_degree"], "Master of Science")
        self.assertEqual(result["canonical_field"], "Data Science")

    # ── Positive resolution tests ─────────────────────────────────────

    def test_btech_shortcode_resolves(self):
        """B.Tech should resolve via S2 shortcode to Bachelor of Technology."""
        result = self.engine.normalize("B.Tech in CSE from IIT Delhi")
        self.assertEqual(result["canonical_degree"], "Bachelor of Technology")

    def test_phd_resolves_to_doctor_of_philosophy(self):
        """PhD variants must always become Doctor of Philosophy."""
        result = self.engine.normalize("PhD in Machine Learning")
        self.assertEqual(result["canonical_degree"], "Doctor of Philosophy")

    # ── Negative / no-signal test ─────────────────────────────────────

    def test_no_educational_info_returns_none(self):
        """Text with no educational content should yield canonical_degree=None."""
        result = self.engine.normalize(
            "Some random text with no educational information"
        )
        self.assertIsNone(result["canonical_degree"])


if __name__ == "__main__":
    unittest.main()
