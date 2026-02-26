import os
import unittest

from utils.height_pgs import harmonize_and_dosage, compute_height_pgs


class HeightPgsTests(unittest.TestCase):
    def setUp(self):
        self.weights_path = os.path.join(os.path.dirname(__file__), "..", "nih", "height_demo_weights.csv")

    def test_harmonize_direct_match(self):
        status, dosage = harmonize_and_dosage("AC", "A", "C")
        self.assertEqual(status, "ok")
        self.assertEqual(dosage, 1.0)

    def test_harmonize_flip(self):
        status, dosage = harmonize_and_dosage("TG", "C", "A")
        self.assertEqual(status, "ok")
        self.assertEqual(dosage, 1.0)

    def test_harmonize_ambiguous(self):
        status, dosage = harmonize_and_dosage("AT", "A", "T")
        self.assertEqual(status, "ambiguous")
        self.assertIsNone(dosage)

    def test_compute_height_pgs_basic(self):
        genome = {
            "rs1426654": {"genotype": "AA"},
            "rs16891982": {"genotype": "CC"},
            "rs1042602": {"genotype": "CA"},
            "rs12913832": {"genotype": "GA"},
            "rs1805007": {"genotype": "CC"},
            "rs1805008": {"genotype": "CT"},
        }
        result = compute_height_pgs(genome, weights_path=self.weights_path)
        self.assertIn("pgs_raw", result)
        self.assertIn("pgs_z", result)
        self.assertGreater(result["coverage"]["snps_used"], 0)
        self.assertLess(result["coverage"]["missing_rate"], 1)
        self.assertIn("predicted_height_cm_mean", result)


if __name__ == "__main__":
    unittest.main()
