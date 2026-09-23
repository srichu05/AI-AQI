"""Unit and integration tests for Phase 2D training, metrics, callbacks, and evaluation functions."""

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import tensorflow as tf

from deep_learning.architecture import build_model
from deep_learning.train_phase2d import (
    MacroF1Callback,
    compute_bootstrap_cis,
    compute_pr_auc_macro,
)


class TestPhase2DMetricsAndCallbacks(unittest.TestCase):
    """Tests for custom Macro F1 callback and metric computation utilities."""

    def setUp(self):
        self.n_samples = 32
        self.num_classes = 5

        rng = np.random.default_rng(42)
        self.y_true = tf.keras.utils.to_categorical(
            rng.integers(0, self.num_classes, size=self.n_samples), num_classes=self.num_classes
        ).astype(np.float32)

        raw_probs = rng.uniform(size=(self.n_samples, self.num_classes)).astype(np.float32)
        self.y_pred_prob = raw_probs / raw_probs.sum(axis=1, keepdims=True)

    def test_compute_pr_auc_macro(self):
        pr_auc = compute_pr_auc_macro(self.y_true, self.y_pred_prob)
        self.assertIsInstance(pr_auc, float)
        self.assertGreaterEqual(pr_auc, 0.0)
        self.assertLessEqual(pr_auc, 1.0)

    def test_compute_bootstrap_cis(self):
        cis = compute_bootstrap_cis(self.y_true, self.y_pred_prob, n_bootstraps=50, seed=42)
        self.assertIn("macro_f1", cis)
        self.assertIn("balanced_accuracy", cis)
        self.assertIn("class_3_recall", cis)
        self.assertIn("class_4_recall", cis)

        for key in ["macro_f1", "balanced_accuracy", "class_3_recall", "class_4_recall"]:
            stats = cis[key]
            self.assertIn("mean", stats)
            self.assertIn("ci_lower", stats)
            self.assertIn("ci_upper", stats)
            self.assertLessEqual(stats["ci_lower"], stats["ci_upper"])

    def test_macro_f1_callback_log_injection(self):
        # Create dummy tf.data.Dataset
        dummy_inputs = {
            "dynamic_input": np.random.randn(self.n_samples, 7, 24).astype(np.float32),
            "static_num_input": np.random.randn(self.n_samples, 16).astype(np.float32),
            "static_cat_input": np.random.randint(0, 3, size=(self.n_samples, 3), dtype=np.int32),
        }
        ds = tf.data.Dataset.from_tensor_slices((dummy_inputs, self.y_true)).batch(16)

        model = build_model()
        model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])

        callback = MacroF1Callback(
            train_dataset=ds,
            val_dataset=ds,
            y_val_true=self.y_true,
            y_train_true=self.y_true,
            num_classes=5,
        )
        callback._model = model

        logs = {"loss": 1.5, "val_loss": 1.6}
        callback.on_epoch_end(epoch=0, logs=logs)

        self.assertIn("val_macro_f1", logs)
        self.assertIn("train_macro_f1", logs)
        self.assertIsInstance(logs["val_macro_f1"], float)
        self.assertEqual(len(callback.history_records), 1)
        self.assertEqual(callback.history_records[0]["epoch"], 1)


class TestPhase2DPipelineExecution(unittest.TestCase):
    """Integration test for training loop execution and checkpoint generation on small datasets."""

    def test_training_short_fit(self):
        n_samples = 32
        rng = np.random.default_rng(123)

        dummy_inputs = {
            "dynamic_input": rng.normal(size=(n_samples, 7, 24)).astype(np.float32),
            "static_num_input": rng.normal(size=(n_samples, 16)).astype(np.float32),
            "static_cat_input": rng.integers(0, 3, size=(n_samples, 3), dtype=np.int32),
        }
        y = tf.keras.utils.to_categorical(rng.integers(0, 5, size=n_samples), num_classes=5).astype(np.float32)

        ds = tf.data.Dataset.from_tensor_slices((dummy_inputs, y)).batch(16)

        with tempfile.TemporaryDirectory() as tmp_dir:
            model = build_model(model_name="Test_Fit_Model")
            model.compile(optimizer="adam", loss="categorical_crossentropy", metrics=["accuracy"])

            ckpt_path = Path(tmp_dir) / "test_best.keras"
            cb_f1 = MacroF1Callback(
                train_dataset=ds,
                val_dataset=ds,
                y_val_true=y,
                y_train_true=y,
                num_classes=5,
            )
            cb_ckpt = tf.keras.callbacks.ModelCheckpoint(
                filepath=str(ckpt_path), monitor="val_macro_f1", mode="max", save_best_only=True
            )

            model.fit(ds, validation_data=ds, epochs=2, callbacks=[cb_f1, cb_ckpt], verbose=0)

            self.assertTrue(ckpt_path.exists())
            self.assertEqual(len(cb_f1.history_records), 2)


if __name__ == "__main__":
    unittest.main()
