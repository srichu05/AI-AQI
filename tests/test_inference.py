"""Unit tests for the official Deep Learning AQI Inference Engine."""

import unittest
import numpy as np

from deep_learning.inference import AQIInferenceEngine, FROZEN_THRESHOLDS, CLASS_LABELS


class TestAQIInferenceEngine(unittest.TestCase):
    """Test suite for AQIInferenceEngine class."""

    @classmethod
    def setUpClass(cls) -> None:
        """Instantiates the global inference engine once for testing."""
        cls.engine = AQIInferenceEngine()

    def test_valid_single_prediction(self) -> None:
        """Tests forward prediction for a valid single input sample."""
        dyn = np.random.normal(45.0, 10.0, size=(7, 24)).astype(np.float32)
        num = np.random.normal(0.0, 1.0, size=(16,)).astype(np.float32)
        cat = np.array([5, 2, 1], dtype=np.int32)

        res = self.engine.predict_single(dyn, num, cat)

        self.assertIn("risk_class", res)
        self.assertIn(res["risk_class"], range(5))
        self.assertIn("risk_label", res)
        self.assertEqual(res["risk_label"], CLASS_LABELS[res["risk_class"]])
        self.assertEqual(len(res["probabilities"]), 5)
        self.assertAlmostEqual(sum(res["probabilities"]), 1.0, places=4)
        self.assertEqual(res["applied_thresholds"], FROZEN_THRESHOLDS)

    def test_shape_mismatch_validation(self) -> None:
        """Tests that invalid input shapes raise a ValueError."""
        invalid_dyn = np.random.normal(0, 1, size=(1, 5, 24)).astype(np.float32)  # 5 timesteps instead of 7
        num = np.random.normal(0, 1, size=(1, 16)).astype(np.float32)
        cat = np.array([[0, 0, 0]], dtype=np.int32)

        with self.assertRaises(ValueError):
            self.engine.predict(invalid_dyn, num, cat)

    def test_nan_validation(self) -> None:
        """Tests that inputs containing NaN values raise a ValueError."""
        dyn = np.random.normal(0, 1, size=(1, 7, 24)).astype(np.float32)
        dyn[0, 0, 0] = np.nan
        num = np.random.normal(0, 1, size=(1, 16)).astype(np.float32)
        cat = np.array([[0, 0, 0]], dtype=np.int32)

        with self.assertRaises(ValueError):
            self.engine.predict(dyn, num, cat)

    def test_categorical_out_of_bounds(self) -> None:
        """Tests that out-of-bounds categorical IDs raise a ValueError."""
        dyn = np.random.normal(0, 1, size=(1, 7, 24)).astype(np.float32)
        num = np.random.normal(0, 1, size=(1, 16)).astype(np.float32)
        invalid_cat = np.array([[35, 0, 0]], dtype=np.int32)  # District ID 35 > 29

        with self.assertRaises(ValueError):
            self.engine.predict(dyn, num, invalid_cat)


if __name__ == "__main__":
    unittest.main()
