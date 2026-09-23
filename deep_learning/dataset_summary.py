"""Dataset summary generation and persistence module."""

import json
from pathlib import Path
from typing import Any, Dict, Union

import numpy as np

from config.paths import DATASET_SUMMARY_PATH, EXPERIMENTS_DIR


def generate_dataset_summary(
    data: Dict[str, Dict[str, np.ndarray]],
    output_path: Union[Path, str] = DATASET_SUMMARY_PATH,
) -> Dict[str, Any]:
    """Generates and persists a summary record of dataset split shapes and counts.

    Structure matches experiment tracking standards:
    {
      "train_samples": 43620,
      "validation_samples": 10770,
      "test_samples": 10740,
      "dynamic_shape": [7, 24],
      "static_num_features": 16,
      "static_cat_features": 3,
      "classes": 5
    }

    Args:
        data: Nested dictionary containing tensors for 'train', 'validation', and 'test'.
        output_path: Destination path for dataset_summary.json. Defaults to DATASET_SUMMARY_PATH.

    Returns:
        Dict[str, Any]: Generated summary dictionary.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    summary: Dict[str, Any] = {
        "train_samples": int(data["train"]["X_dynamic"].shape[0]),
        "validation_samples": int(data["validation"]["X_dynamic"].shape[0]),
        "test_samples": int(data["test"]["X_dynamic"].shape[0]),
        "dynamic_shape": [
            int(data["train"]["X_dynamic"].shape[1]),
            int(data["train"]["X_dynamic"].shape[2]),
        ],
        "static_num_features": int(data["train"]["X_static_num"].shape[1]),
        "static_cat_features": int(data["train"]["X_static_cat"].shape[1]),
        "classes": int(data["train"]["y"].shape[1]),
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


def load_dataset_summary(
    filepath: Union[Path, str] = DATASET_SUMMARY_PATH,
) -> Dict[str, Any]:
    """Loads dataset summary from a JSON file.

    Args:
        filepath: Source path for dataset_summary.json. Defaults to DATASET_SUMMARY_PATH.

    Returns:
        Dict[str, Any]: Loaded dataset summary dictionary.

    Raises:
        FileNotFoundError: If dataset summary JSON file does not exist.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Dataset summary file not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
