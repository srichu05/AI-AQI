"""Unit tests for Phase 2B development modules and improvements."""

import json
import unittest
from pathlib import Path
import tempfile

import numpy as np
import tensorflow as tf

from config.paths import (
    ROOT_DIR,
    DATA_DIR,
    DL_DATA_DIR,
    ML_DATA_DIR,
    LIVE_DATA_DIR,
    SAVED_MODELS_DIR,
    EXPERIMENTS_DIR,
    CLASS_WEIGHTS_PATH,
    DATASET_SUMMARY_PATH,
    FEATURE_GROUPS_PATH,
    ensure_directories_exist,
)
from deep_learning.dataset_loader import load_split_tensors, load_all_tensors
from deep_learning.dataset_validator import (
    validate_split_tensors,
    validate_dataset,
    validate_feature_groups,
    TensorValidationError,
)
from deep_learning.class_weights import (
    compute_dataset_class_weights,
    save_class_weights,
    load_class_weights,
)
from deep_learning.dataset_summary import (
    generate_dataset_summary,
    load_dataset_summary,
)
from deep_learning.tf_dataset import create_tf_dataset, create_all_tf_datasets


class TestPathsConfig(unittest.TestCase):
    """Tests for central paths configuration."""

    def test_paths_exist(self):
        self.assertIsInstance(ROOT_DIR, Path)
        self.assertIsInstance(DATA_DIR, Path)
        self.assertIsInstance(DL_DATA_DIR, Path)
        self.assertIsInstance(ML_DATA_DIR, Path)
        self.assertIsInstance(LIVE_DATA_DIR, Path)
        self.assertIsInstance(SAVED_MODELS_DIR, Path)
        self.assertIsInstance(EXPERIMENTS_DIR, Path)
        self.assertIsInstance(CLASS_WEIGHTS_PATH, Path)
        self.assertIsInstance(DATASET_SUMMARY_PATH, Path)
        self.assertIsInstance(FEATURE_GROUPS_PATH, Path)

    def test_ensure_directories_exist(self):
        ensure_directories_exist()
        self.assertTrue(DL_DATA_DIR.exists())
        self.assertTrue(SAVED_MODELS_DIR.exists())
        self.assertTrue(EXPERIMENTS_DIR.exists())


class TestDatasetLoader(unittest.TestCase):
    """Tests for Phase 2A NumPy tensor loader."""

    def test_load_all_tensors_real_data(self):
        if not DL_DATA_DIR.exists() or not (DL_DATA_DIR / "X_dynamic_train.npy").exists():
            self.skipTest("DL data directory or files not found.")

        data = load_all_tensors(data_dir=DL_DATA_DIR)
        self.assertIn("train", data)
        self.assertIn("validation", data)
        self.assertIn("test", data)

        for split in ["train", "validation", "test"]:
            split_dict = data[split]
            self.assertIn("X_dynamic", split_dict)
            self.assertIn("X_static_num", split_dict)
            self.assertIn("X_static_cat", split_dict)
            self.assertIn("y", split_dict)
            self.assertEqual(split_dict["X_dynamic"].ndim, 3)
            self.assertEqual(split_dict["X_static_num"].ndim, 2)
            self.assertEqual(split_dict["X_static_cat"].ndim, 2)
            self.assertEqual(split_dict["y"].ndim, 2)

    def test_missing_file_raises_error(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            with self.assertRaises(FileNotFoundError):
                load_split_tensors(split="train", data_dir=tmp_dir)


class TestDatasetValidator(unittest.TestCase):
    """Tests for dataset validator rules and exception handling."""

    def setUp(self):
        self.n_samples = 50
        self.seq_len = 7
        self.dyn_feats = 24
        self.snum_feats = 16
        self.scat_feats = 3
        self.num_classes = 5

        rng = np.random.default_rng(42)
        self.valid_tensors = {
            "X_dynamic": rng.normal(size=(self.n_samples, self.seq_len, self.dyn_feats)).astype(np.float32),
            "X_static_num": rng.normal(size=(self.n_samples, self.snum_feats)).astype(np.float32),
            "X_static_cat": rng.integers(0, 10, size=(self.n_samples, self.scat_feats), dtype=np.int32),
            "y": tf.keras.utils.to_categorical(
                rng.integers(0, self.num_classes, size=self.n_samples), num_classes=self.num_classes
            ).astype(np.int32),
        }

    def test_valid_tensors_pass(self):
        self.assertTrue(validate_split_tensors(self.valid_tensors, split_name="train", metadata_path=None))

    def test_feature_groups_verification(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            meta_path = Path(tmp_dir) / "feature_groups.json"
            meta_content = {
                "dynamic_features": [f"f_{i}" for i in range(self.dyn_feats)],
                "static_num_features": [f"s_{i}" for i in range(self.snum_feats)],
                "static_cat_features": [f"c_{i}" for i in range(self.scat_feats)],
            }
            with open(meta_path, "w") as f:
                json.dump(meta_content, f)

            self.assertTrue(validate_feature_groups(self.valid_tensors, metadata_path=meta_path))

            # Introduce dimension mismatch
            bad_meta = dict(meta_content)
            bad_meta["dynamic_features"] = bad_meta["dynamic_features"][:10]
            with open(meta_path, "w") as f:
                json.dump(bad_meta, f)

            with self.assertRaises(TensorValidationError):
                validate_feature_groups(self.valid_tensors, metadata_path=meta_path)

    def test_rank_mismatch_raises_error(self):
        corrupted = dict(self.valid_tensors)
        corrupted["X_dynamic"] = corrupted["X_dynamic"].reshape(-1, self.dyn_feats)
        with self.assertRaises(TensorValidationError):
            validate_split_tensors(corrupted, split_name="train", metadata_path=None)

    def test_sample_count_mismatch_raises_error(self):
        corrupted = dict(self.valid_tensors)
        corrupted["y"] = corrupted["y"][:30]
        with self.assertRaises(TensorValidationError):
            validate_split_tensors(corrupted, split_name="train", metadata_path=None)

    def test_sequence_length_mismatch_raises_error(self):
        corrupted = dict(self.valid_tensors)
        corrupted["X_dynamic"] = np.random.randn(self.n_samples, 5, self.dyn_feats).astype(np.float32)
        with self.assertRaises(TensorValidationError):
            validate_split_tensors(corrupted, split_name="train", sequence_length=7, metadata_path=None)

    def test_nan_values_raise_error(self):
        corrupted = dict(self.valid_tensors)
        corrupted["X_dynamic"] = corrupted["X_dynamic"].copy()
        corrupted["X_dynamic"][0, 0, 0] = np.nan
        with self.assertRaises(TensorValidationError):
            validate_split_tensors(corrupted, split_name="train", metadata_path=None)

    def test_inf_values_raise_error(self):
        corrupted = dict(self.valid_tensors)
        corrupted["X_static_num"] = corrupted["X_static_num"].copy()
        corrupted["X_static_num"][0, 0] = np.inf
        with self.assertRaises(TensorValidationError):
            validate_split_tensors(corrupted, split_name="train", metadata_path=None)

    def test_invalid_one_hot_raises_error(self):
        corrupted = dict(self.valid_tensors)
        corrupted["y"] = corrupted["y"].copy()
        corrupted["y"][0, :] = 0  # Sum != 1
        with self.assertRaises(TensorValidationError):
            validate_split_tensors(corrupted, split_name="train", metadata_path=None)

    def test_negative_cat_index_raises_error(self):
        corrupted = dict(self.valid_tensors)
        corrupted["X_static_cat"] = corrupted["X_static_cat"].copy()
        corrupted["X_static_cat"][0, 0] = -1
        with self.assertRaises(TensorValidationError):
            validate_split_tensors(corrupted, split_name="train", metadata_path=None)


class TestClassWeights(unittest.TestCase):
    """Tests for balanced class weight computation and JSON persistence."""

    def test_class_weights_computation_and_saving(self):
        y_labels = np.array([0, 0, 0, 0, 1, 1, 2, 3, 4, 4])
        y_one_hot = tf.keras.utils.to_categorical(y_labels, num_classes=5)

        with tempfile.TemporaryDirectory() as tmp_dir:
            save_file = Path(tmp_dir) / "class_weights.json"
            weights = compute_dataset_class_weights(y_one_hot, num_classes=5, save_path=save_file)
            self.assertTrue(save_file.exists())

            loaded_weights = load_class_weights(save_file)
            self.assertEqual(weights, loaded_weights)


class TestDatasetSummary(unittest.TestCase):
    """Tests for dataset summary JSON generation and persistence."""

    def test_generate_dataset_summary(self):
        rng = np.random.default_rng(10)
        mock_data = {
            "train": {
                "X_dynamic": np.zeros((100, 7, 24)),
                "X_static_num": np.zeros((100, 16)),
                "X_static_cat": np.zeros((100, 3)),
                "y": np.zeros((100, 5)),
            },
            "validation": {
                "X_dynamic": np.zeros((20, 7, 24)),
                "X_static_num": np.zeros((20, 16)),
                "X_static_cat": np.zeros((20, 3)),
                "y": np.zeros((20, 5)),
            },
            "test": {
                "X_dynamic": np.zeros((15, 7, 24)),
                "X_static_num": np.zeros((15, 16)),
                "X_static_cat": np.zeros((15, 3)),
                "y": np.zeros((15, 5)),
            },
        }

        with tempfile.TemporaryDirectory() as tmp_dir:
            summary_path = Path(tmp_dir) / "dataset_summary.json"
            summary = generate_dataset_summary(mock_data, output_path=summary_path)
            self.assertTrue(summary_path.exists())

            self.assertEqual(summary["train_samples"], 100)
            self.assertEqual(summary["validation_samples"], 20)
            self.assertEqual(summary["test_samples"], 15)
            self.assertEqual(summary["dynamic_shape"], [7, 24])
            self.assertEqual(summary["static_num_features"], 16)
            self.assertEqual(summary["static_cat_features"], 3)
            self.assertEqual(summary["classes"], 5)

            loaded = load_dataset_summary(summary_path)
            self.assertEqual(summary, loaded)


class TestTFDataset(unittest.TestCase):
    """Tests for tf.data.Dataset input pipeline construction."""

    def setUp(self):
        self.n_samples = 64
        self.batch_size = 16
        rng = np.random.default_rng(123)

        self.X_dyn = rng.normal(size=(self.n_samples, 7, 24)).astype(np.float32)
        self.X_snum = rng.normal(size=(self.n_samples, 16)).astype(np.float32)
        self.X_scat = rng.integers(0, 5, size=(self.n_samples, 3), dtype=np.int32)
        self.y = tf.keras.utils.to_categorical(
            rng.integers(0, 5, size=self.n_samples), num_classes=5
        ).astype(np.int32)

    def test_tf_dataset_structure_and_batching(self):
        ds = create_tf_dataset(
            X_dynamic=self.X_dyn,
            X_static_num=self.X_snum,
            X_static_cat=self.X_scat,
            y=self.y,
            batch_size=self.batch_size,
            is_training=False,
        )

        for inputs, targets in ds.take(1):
            self.assertIn("dynamic_input", inputs)
            self.assertIn("static_num_input", inputs)
            self.assertIn("static_cat_input", inputs)

            self.assertEqual(inputs["dynamic_input"].shape, (self.batch_size, 7, 24))
            self.assertEqual(inputs["static_num_input"].shape, (self.batch_size, 16))
            self.assertEqual(inputs["static_cat_input"].shape, (self.batch_size, 3))
            self.assertEqual(targets.shape, (self.batch_size, 5))


if __name__ == "__main__":
    unittest.main()
