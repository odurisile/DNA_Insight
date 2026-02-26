import csv
import os
import unittest

from utils.height_pgs import compute_height_pgs


class HeightPipelineTests(unittest.TestCase):
    def setUp(self):
        self.weights_path = os.path.join(os.path.dirname(__file__), "..", "nih", "height_demo_weights.csv")

    def _simulate_admixed_genome(self, n_snps=10):
        genome = {}
        with open(self.weights_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for idx, row in enumerate(reader):
                if idx >= n_snps:
                    break
                rsid = row["rsid"]
                effect = row["effect_allele"]
                other = row["other_allele"]
                if not rsid or not effect or not other:
                    continue
                seed = sum(ord(c) for c in rsid) % 3
                if seed == 0:
                    geno = effect + effect
                elif seed == 1:
                    geno = effect + other
                else:
                    geno = other + other
                genome[rsid] = {"genotype": geno}
        return genome

    def test_pipeline_outputs(self):
        genome = self._simulate_admixed_genome()
        ancestry = {"AFR": 0.6, "EUR": 0.4}
        result = compute_height_pgs(genome, weights_path=self.weights_path, sex="male", global_ancestry=ancestry)
        self.assertIn("predicted_height_cm_mean", result)
        self.assertIn("ancestry_breakdown", result)
        self.assertIn("ancestry_height_components", result)
        self.assertIn("qc_report", result)
        self.assertIn("confidence_intervals", result)


if __name__ == "__main__":
    unittest.main()
