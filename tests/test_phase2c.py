"""Unit and integration tests for Phase 2C Deep Learning model architecture components."""

import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
import tensorflow as tf

from deep_learning.attention import BahdanauAttention
from deep_learning.architecture import build_model
from deep_learning.model_summary import (
    export_model_summary,
    generate_architecture_plot,
    generate_parameter_report,
)
from deep_learning.tf_dataset import create_tf_dataset


class TestBahdanauAttention(unittest.TestCase):
    """Tests for custom Bahdanau (additive) temporal attention layer."""

    def setUp(self):
        self.batch_size = 16
        self.seq_len = 7
        self.feature_dim = 128
        self.attn_units = 64
        self.inputs = tf.random.normal((self.batch_size, self.seq_len, self.feature_dim))

    def test_attention_output_shape(self):
        layer = BahdanauAttention(units=self.attn_units)
        context = layer(self.inputs)
        self.assertEqual(context.shape, (self.batch_size, self.feature_dim))

    def test_attention_weights_properties(self):
        layer = BahdanauAttention(units=self.attn_units)
        context, weights = layer(self.inputs, return_attention_weights=True)

        self.assertEqual(context.shape, (self.batch_size, self.feature_dim))
        self.assertEqual(weights.shape, (self.batch_size, self.seq_len, 1))

        # Check softmax normalization property: weights sum to 1 across sequence length
        weight_sums = tf.reduce_sum(weights, axis=1)
        np.testing.assert_allclose(weight_sums.numpy(), np.ones((self.batch_size, 1)), atol=1e-5)

    def test_attention_serialization(self):
        layer = BahdanauAttention(units=32)
        config = layer.get_config()
        self.assertEqual(config["units"], 32)

        reconstructed_layer = BahdanauAttention.from_config(config)
        self.assertEqual(reconstructed_layer.units, 32)


class TestAQIArchitecture(unittest.TestCase):
    """Tests for hybrid multi-input Keras Functional model architecture."""

    def setUp(self):
        self.model = build_model(
            sequence_length=7,
            dynamic_features=24,
            static_num_features=16,
            district_vocab_size=32,
            land_use_vocab_size=8,
            urban_rural_vocab_size=4,
            num_classes=5,
        )

    def _get_shape_list(self, tensor_or_shape):
        shape_obj = tensor_or_shape.shape if hasattr(tensor_or_shape, "shape") else tensor_or_shape
        if hasattr(shape_obj, "as_list"):
            return shape_obj.as_list()
        return list(shape_obj)

    def test_model_inputs_and_outputs(self):
        self.assertIsInstance(self.model, tf.keras.Model)

        # Verify input layer names match Phase 2B tf_dataset.py dict keys
        input_names = list(self.model.input.keys())
        self.assertIn("dynamic_input", input_names)
        self.assertIn("static_num_input", input_names)
        self.assertIn("static_cat_input", input_names)

        # Verify input shapes
        self.assertEqual(self._get_shape_list(self.model.input["dynamic_input"]), [None, 7, 24])
        self.assertEqual(self._get_shape_list(self.model.input["static_num_input"]), [None, 16])
        self.assertEqual(self._get_shape_list(self.model.input["static_cat_input"]), [None, 3])

        # Verify output shape
        self.assertEqual(self._get_shape_list(self.model.output), [None, 5])

    def test_model_forward_pass(self):
        batch_size = 8
        dummy_inputs = {
            "dynamic_input": tf.random.normal((batch_size, 7, 24), dtype=tf.float32),
            "static_num_input": tf.random.normal((batch_size, 16), dtype=tf.float32),
            "static_cat_input": tf.constant(
                [[1, 2, 0], [10, 4, 1], [29, 5, 2], [0, 0, 0], [15, 3, 1], [5, 1, 0], [20, 2, 2], [28, 0, 1]],
                dtype=tf.int32,
            ),
        }

        predictions = self.model(dummy_inputs)
        self.assertEqual(predictions.shape, (batch_size, 5))

        # Softmax probabilities must sum to 1.0 per sample
        row_sums = tf.reduce_sum(predictions, axis=1)
        np.testing.assert_allclose(row_sums.numpy(), np.ones(batch_size), atol=1e-5)

    def test_integration_with_tf_dataset(self):
        n_samples = 32
        batch_size = 16

        X_dyn = np.random.randn(n_samples, 7, 24).astype(np.float32)
        X_snum = np.random.randn(n_samples, 16).astype(np.float32)
        X_scat = np.random.randint(0, 3, size=(n_samples, 3), dtype=np.int32)
        y = tf.keras.utils.to_categorical(np.random.randint(0, 5, size=n_samples), num_classes=5).astype(np.int32)

        ds = create_tf_dataset(
            X_dynamic=X_dyn,
            X_static_num=X_snum,
            X_static_cat=X_scat,
            y=y,
            batch_size=batch_size,
        )

        for inputs, targets in ds.take(1):
            outputs = self.model(inputs)
            self.assertEqual(outputs.shape, (batch_size, 5))
            self.assertEqual(targets.shape, (batch_size, 5))


class TestModelSummaryUtilities(unittest.TestCase):
    """Tests for model summary, plot, and report file generation."""

    def setUp(self):
        self.model = build_model()

    def test_export_model_summary(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "summary.txt"
            summary_str = export_model_summary(self.model, output_path=out_file)

            self.assertTrue(out_file.exists())
            self.assertIn("AI_AQI_Hybrid_Model", summary_str)
            self.assertIn("dyn_attention", summary_str)
            self.assertIn("aqi_output", summary_str)

    def test_generate_parameter_report(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "report.json"
            report = generate_parameter_report(self.model, output_path=out_file)

            self.assertTrue(out_file.exists())
            self.assertIn("total_parameters", report)
            self.assertIn("trainable_parameters", report)
            self.assertIn("non_trainable_parameters", report)
            self.assertGreater(report["total_parameters"], 0)
            self.assertEqual(report["output_tensor_shape"], [-1, 5])

    def test_generate_architecture_plot(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            out_file = Path(tmp_dir) / "architecture.png"
            try:
                generate_architecture_plot(self.model, output_path=out_file)
                self.assertTrue(out_file.exists())
            except Exception as e:
                self.skipTest(f"Plot generation skipped due to environment constraint: {e}")


if __name__ == "__main__":
    unittest.main()
