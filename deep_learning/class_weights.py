"""Class weights computation and persistence module."""

import json
from pathlib import Path
from typing import Dict, Optional, Union

import numpy as np
from sklearn.utils.class_weight import compute_class_weight

from config.paths import CLASS_WEIGHTS_PATH, EXPERIMENTS_DIR


def save_class_weights(
    class_weights: Dict[int, float],
    output_path: Union[Path, str] = CLASS_WEIGHTS_PATH,
) -> Path:
    """Saves computed class weights to a JSON file.

    Args:
        class_weights: Dictionary mapping integer class indices to weight floats.
        output_path: Destination JSON file path. Defaults to CLASS_WEIGHTS_PATH.

    Returns:
        Path: Path object pointing to the saved JSON file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Ensure keys are string-formatted for clean JSON serialization
    serializable_weights = {str(k): float(v) for k, v in class_weights.items()}

    with open(path, "w", encoding="utf-8") as f:
        json.dump(serializable_weights, f, indent=2)

    return path


def load_class_weights(
    filepath: Union[Path, str] = CLASS_WEIGHTS_PATH,
) -> Dict[int, float]:
    """Loads class weights from a JSON file.

    Args:
        filepath: Source JSON file path. Defaults to CLASS_WEIGHTS_PATH.

    Returns:
        Dict[int, float]: Loaded class weights mapping integer class indices to floats.

    Raises:
        FileNotFoundError: If the class weights JSON file does not exist.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Class weights file not found at: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {int(k): float(v) for k, v in data.items()}


def compute_dataset_class_weights(
    y_train: np.ndarray,
    num_classes: int = 5,
    save_path: Optional[Union[Path, str]] = None,
) -> Dict[int, float]:
    """Computes balanced class weights from one-hot encoded training targets.

    Converts one-hot targets into integer class labels and calculates balanced
    class weights using sklearn.utils.class_weight.compute_class_weight. Optionally
    persists the result to a JSON file.

    Args:
        y_train: One-hot encoded training target array of shape (samples, num_classes).
        num_classes: Number of target risk classes. Defaults to 5.
        save_path: Optional path to save the JSON output. If provided, saves class weights.

    Returns:
        Dict[int, float]: Dictionary mapping integer class index (0..num_classes-1)
            to its calculated balanced class weight. Suitable for Keras model.fit().

    Raises:
        ValueError: If y_train shape does not match num_classes or is empty.
    """
    if y_train.ndim != 2 or y_train.shape[1] != num_classes:
        raise ValueError(
            f"Expected y_train shape (samples, {num_classes}), got {y_train.shape}."
        )

    # Convert one-hot vectors to integer class labels
    y_labels = np.argmax(y_train, axis=1)

    classes = np.arange(num_classes)
    weights = compute_class_weight(
        class_weight="balanced",
        classes=classes,
        y=y_labels,
    )

    class_weights_dict: Dict[int, float] = {
        int(cls): float(weight) for cls, weight in zip(classes, weights)
    }

    if save_path is not None:
        save_class_weights(class_weights_dict, output_path=save_path)

    return class_weights_dict
