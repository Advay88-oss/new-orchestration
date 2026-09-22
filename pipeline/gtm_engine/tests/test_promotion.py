"""
Unit tests for derive_pattern_type (Law L5 deterministic promotion).
"""

import unittest
from pipeline.gtm_engine.interceptors.promotion import (
    derive_pattern_type,
    VALID_PATTERN_TYPES,
)


class TestDerivePatternType(unittest.TestCase):
    def test_required_matrix(self):
        test_cases = [
            (
                (1, True, True, False, ["blog"], 1, True),
                "ONE_OFF",
                "Single instance is ONE_OFF regardless of cadence/name",
            ),
            (
                (3, True, True, False, ["blog"], 1, True),
                "REPEATED_PATTERN",
                "2-3 instances is REPEATED_PATTERN",
            ),
            (
                (6, True, False, False, ["blog"], 1, True),
                "REPEATED_PATTERN_HIGH_COUNT",
                "6 instances without name must not collapse into 2-3 bucket",
            ),
            (
                (6, False, True, False, ["blog"], 1, True),
                "REPEATED_PATTERN_HIGH_COUNT",
                "6 instances without cadence must not collapse into 2-3 bucket",
            ),
            (
                (6, True, True, False, ["blog"], 1, True),
                "RECURRING_SERIES",
                "6 instances with cadence, name, single format is RECURRING_SERIES",
            ),
            (
                (8, True, True, False, ["blog", "x"], 3, True),
                "CORE_MARKETING_SYSTEM",
                ">=4 with cadence, name, multi-format, multi-period, strategic purpose",
            ),
            (
                (8, True, True, True, ["blog", "x"], 3, True),
                "CAMPAIGN",
                "Campaign flag overrides counts",
            ),
        ]

        for params, expected, description in test_cases:
            with self.subTest(msg=description, params=params):
                actual = derive_pattern_type(*params)
                self.assertEqual(actual, expected)
                self.assertIn(actual, VALID_PATTERN_TYPES)

    def test_edge_cases(self):
        # 2 instances
        self.assertEqual(
            derive_pattern_type(2, True, True, False, ["x"], 1, False),
            "REPEATED_PATTERN",
        )
        # 4 instances threshold
        self.assertEqual(
            derive_pattern_type(4, True, True, False, ["x"], 1, False),
            "RECURRING_SERIES",
        )
        # Invalid count <= 0
        with self.assertRaises(ValueError):
            derive_pattern_type(0, True, True, False, ["x"], 1, False)


if __name__ == "__main__":
    unittest.main()
