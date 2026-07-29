import unittest

from utils.trait_engine import predict_blood_type, predict_traits


class TraitEngineTests(unittest.TestCase):
    def test_predict_blood_type_o(self):
        genome = {
            "rs8176719": {"genotype": "D/D"},
            "rs8176746": {"genotype": "G/G"},
        }
        self.assertEqual(predict_blood_type(genome), "Likely type O")

    def test_predict_blood_type_a(self):
        genome = {
            "rs8176719": {"genotype": "D/I"},
            "rs8176746": {"genotype": "G/G"},
        }
        self.assertEqual(predict_blood_type(genome), "Likely type A")

    def test_predict_blood_type_b(self):
        genome = {
            "rs8176719": {"genotype": "D/I"},
            "rs8176746": {"genotype": "G/T"},
        }
        self.assertEqual(predict_blood_type(genome), "Likely type B")

    def test_predict_blood_type_ab(self):
        genome = {
            "rs8176719": {"genotype": "I/I"},
            "rs8176746": {"genotype": "G/T"},
        }
        self.assertEqual(predict_blood_type(genome), "Likely type AB")

    def test_predict_blood_type_unknown_without_required_markers(self):
        genome = {"rs8176719": {"genotype": "D/I"}}
        self.assertEqual(predict_blood_type(genome), "Unknown")

    def test_predict_traits_includes_blood_type(self):
        genome = {
            "rs8176719": {"genotype": "D/I"},
            "rs8176746": {"genotype": "G/G"},
        }
        traits = predict_traits(genome)
        self.assertIn("blood_type", traits)
        self.assertEqual(traits["blood_type"], "Likely type A")


if __name__ == "__main__":
    unittest.main()
