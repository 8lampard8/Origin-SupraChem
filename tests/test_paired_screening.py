from math import isnan
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from paired_screening import linear_limits, load_conditions, response, stage_columns


class PairedScreeningTests(unittest.TestCase):
    def test_condition_blank_and_per_row_blank(self):
        conditions = load_conditions({'conditions': [
            {'name': 'System A', 'blank': 100, 'rows': [['Guest', 145, 85]]},
            {'name': 'System B', 'rows': [['Guest', 130, 160, 190]]},
        ]})
        first, second = map(stage_columns, conditions)
        self.assertEqual((first[4][0], first[5][0], first[8][0]), (45, -15, 3))
        self.assertEqual((second[4][0], second[5][0], second[8][0]), (30, 60, 2))
        self.assertEqual((first[12][0], first[13][0], first[14][0], first[15][0]), (45, 0, 0, 15))

    def test_zero_and_missing_responses_leave_ef_undefined(self):
        self.assertTrue(isnan(response(100, 100, 160)[-1]))
        condition, = load_conditions({'conditions': [
            {'name': 'System A', 'blank': 100, 'rows': [['Guest', None, 150]]},
        ]})
        values = stage_columns(condition)
        self.assertTrue(isnan(values[4][0]))
        self.assertEqual(values[5][0], 50)
        self.assertTrue(isnan(values[8][0]))

    def test_common_linear_limits_cover_both_conditions(self):
        columns = [stage_columns(condition) for condition in load_conditions({'conditions': [
            {'name': 'System A', 'blank': 100, 'rows': [['Guest', 109, 160]]},
            {'name': 'System B', 'blank': 100, 'rows': [['Guest', 180, 240]]},
        ]})]
        limit, step, ticks = linear_limits(columns, (6, 7))
        self.assertGreater(limit, 140)
        self.assertEqual(ticks[0], 0)
        self.assertEqual(ticks[-1], limit)
        for before, after in zip(ticks, ticks[1:]):
            self.assertAlmostEqual(after - before, step)
