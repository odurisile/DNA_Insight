import os
import unittest

from utils.height_calibration.calibrator import HeightCalibrator


class HeightCalibrationTests(unittest.TestCase):
    def setUp(self):
        self.config_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "height_calibration_config.yaml"
        )

    def test_synthetic_underprediction_fix(self):
        calibrator = HeightCalibrator(config_path=self.config_path)
        raw_pgs = (170.0 - 170.0) / 6.0  # z = 0
        result = calibrator.calibrate(
            raw_pgs=raw_pgs,
            sex="male",
            global_ancestry={"AFR": 1.0, "EUR": 0.0, "NAT": 0.0, "EAS": 0.0, "SAS": 0.0},
        )
        self.assertAlmostEqual(result.predicted_height_cm, 185.0, delta=0.5)
        self.assertNotIn("afr_under_correction", result.bias_flags)


if __name__ == "__main__":
    unittest.main()
