import os
import unittest

from utils.height_pipeline.ancestry import infer_global_ancestry


class HeightAncestryInferenceTests(unittest.TestCase):
    def test_infer_global_ancestry(self):
        fixture = os.path.join(os.path.dirname(__file__), "fixtures", "height_aims_small.csv")
        genotype_map = {
            "rs1426654": "GG",
            "rs16891982": "GG",
        }
        proportions, info = infer_global_ancestry(genotype_map, aims_path=fixture, min_snps=1)
        self.assertEqual(info["status"], "ok")
        self.assertGreater(proportions.get("EUR", 0.0), proportions.get("AFR", 0.0))


if __name__ == "__main__":
    unittest.main()
