"""Unit tests for Validation-Only Decision Threshold Calibration module."""

import unittest
import numpy as np

from deep_learning.threshold_calibration import (
    apply_thresholds,
    compute_evaluation_metrics,
    optimize_thresholds_validation,
)


class TestThresholdCalibration(unittest.TestCase):
    """Tests for threshold application, metric calculations, and optimization logic."""

    def setUp(self):
        self.n_samples = 100
        self.num_classes = 5
        rng = np.random.default_rng(42)

        raw = rng.uniform(size=(self.n_samples, self.num_classes)).astype(np.float64)
        self.probs = raw / raw.sum(axis=1, keepdims=True)

        self.y_true_cls = rng.integers(0, self.num_classes, size=self.n_samples)
        self.y_true_onehot = np.zeros((self.n_samples, self.num_classes), dtype=np.float32)
        self.y_true_onehot[np.arange(self.n_samples), self.y_true_cls] = 1.0

    def test_baseline_thresholds_reproduce_argmax(self):
        """Verifies that thresholds=[1,1,1,1,1] produces identical predictions to np.argmax."""
        baseline_thresh = [1.0, 1.0, 1.0, 1.0, 1.0]
        preds_thresh = apply_thresholds(self.probs, baseline_thresh)
        preds_argmax = np.argmax(self.probs, axis=1)

        np.testing.assert_array_equal(preds_thresh, preds_argmax)

    def test_apply_thresholds_output_shapes_and_types(self):
        """Verifies return types, shapes, and integer bounds for threshold predictions."""
        thresh = [0.9, 1.0, 1.0, 1.05, 0.05]
        preds = apply_thresholds(self.probs, thresh)

        self.assertIsInstance(preds, np.ndarray)
        self.assertEqual(preds.shape, (self.n_samples,))
        self.assertTrue(np.issubdtype(preds.dtype, np.integer))
        self.assertTrue(np.all(preds >= 0))
        self.assertTrue(np.all(preds < self.num_classes))

    def test_invalid_thresholds_raises_value_error(self):
        """Verifies that invalid threshold dimensions or non-positive values raise ValueError."""
        with self.assertRaises(ValueError):
            apply_thresholds(self.probs, [1.0, 1.0, 1.0])  # WRONG LENGTH

        with self.assertRaises(ValueError):
            apply_thresholds(self.probs, [1.0, 0.0, 1.0, 1.0, 1.0])  # ZERO THRESHOLD

        with self.assertRaises(ValueError):
            apply_thresholds(self.probs, [1.0, -0.5, 1.0, 1.0, 1.0])  # NEGATIVE THRESHOLD

    def test_compute_evaluation_metrics_structure(self):
        """Verifies keys and metric bounds returned by compute_evaluation_metrics."""
        preds = np.argmax(self.probs, axis=1)
        m = compute_evaluation_metrics(self.y_true_cls, preds, self.num_classes)

        self.assertIn("overall_metrics", m)
        self.assertIn("per_class_metrics", m)
        self.assertIn("confusion_matrix", m)

        overall = m["overall_metrics"]
        self.assertGreaterEqual(overall["accuracy"], 0.0)
        self.assertLessEqual(overall["accuracy"], 1.0)
        self.assertGreaterEqual(overall["macro_f1"], 0.0)
        self.assertLessEqual(overall["macro_f1"], 1.0)

        for k in range(self.num_classes):
            self.assertIn(str(k), m["per_class_metrics"])

    def test_optimization_reproducibility(self):
        """Verifies deterministic optimization output for fixed validation inputs."""
        t1, m1, _ = optimize_thresholds_validation(self.probs, self.y_true_onehot, seed=42)
        t2, m2, _ = optimize_thresholds_validation(self.probs, self.y_true_onehot, seed=42)

        np.testing.assert_array_almost_equal(t1, t2)
        self.assertEqual(m1["overall_metrics"]["macro_f1"], m2["overall_metrics"]["macro_f1"])


if __name__ == "__main__":
    unittest.main()
