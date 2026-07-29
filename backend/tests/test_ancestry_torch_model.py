import unittest


class TorchDependencyGuardTests(unittest.TestCase):
    def test_predict_requires_torch_when_module_missing(self):
        try:
            import torch  # noqa: F401
        except Exception:
            from utils.ancestry_inference.torch_model import predict_ancestry_from_pcs_torch

            with self.assertRaises(RuntimeError):
                predict_ancestry_from_pcs_torch([0.0] * 20, model_path="missing.pt")


if __name__ == "__main__":
    unittest.main()
