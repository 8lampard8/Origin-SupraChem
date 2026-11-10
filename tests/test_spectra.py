import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from spectra import highest_peak, variance_summary, verify_sg_interior, validate_xy

class SpectraTests(unittest.TestCase):
    def test_cutoff_is_strict(self):
        self.assertIsNone(highest_peak([419,420,421,422],[1,8,3,1]))
    def test_boundary_is_not_peak(self):
        self.assertIsNone(highest_peak([421,422,423],[9,8,7]))
    def test_local_peak_after_high_boundary(self):
        self.assertEqual(highest_peak([419,420,421,422,423,424],[9,8,7,3,5,1]),
                         dict(intensity=5,wavelength=423,row=5))
    def test_flat_peak(self):
        self.assertEqual(highest_peak([420,421,422,423,424],[1,3,3,3,1])["row"],2)
    def test_no_peak_at_flat_endpoint(self):
        self.assertIsNone(highest_peak([420,421,422,423],[1,3,3,3]))
    def test_missing_and_unsorted_rejected(self):
        for x,y in [([1,2,3],[1,float("nan"),2]),([1,3,2],[1,2,3])]:
            with self.assertRaises(ValueError):validate_xy(x,y)
    def test_variance_denominators(self):
        result=variance_summary([1,2,3])
        self.assertEqual(result["sample_variance"],1)
        self.assertAlmostEqual(result["population_variance"],2/3)
    def test_variance_missing_rejected(self):
        with self.assertRaises(ValueError):variance_summary([1,None])
    def test_quadratic_preserved(self):
        y=[i*i+3*i+8 for i in range(80)]
        self.assertLess(verify_sg_interior(y,y),1e-8)
    def test_corruption_detected(self):
        y=[i*i for i in range(80)]
        with self.assertRaises(ArithmeticError):verify_sg_interior(y,[v+1 for v in y])

if __name__ == "__main__": unittest.main()
