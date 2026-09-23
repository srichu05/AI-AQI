"""Dataset validator module for Phase 2A exported NumPy tensors."""

import json
from pathlib import Path
from typing import Dict, Optional, Union

import numpy as np

from config.paths import FEATURE_GROUPS_PATH


class TensorValidationError(ValueError):
    """Custom exception raised when tensor validation fails."""
    pass


def validate_feature_groups(
    split_tensors: Dict[str, np.ndarray],
    split_name: str = "train",
    metadata_path: Union[Path, str] = FEATURE_GROUPS_PATH,
) -> bool:
    """Validates that tensor feature dimensions match feature_groups.json metadata.

    Args:
        split_tensors: Dictionary containing tensors for a split.
        split_name: Name of the dataset split. Defaults to 'train'.
        metadata_path: Path to feature_groups.json. Defaults to FEATURE_GROUPS_PATH.

    Returns:
        bool: True if feature metadata is verified or if file is not present.

    Raises:
        TensorValidationError: If feature count defined in metadata mismatches tensor shape.
    """
    path = Path(metadata_path)
    if not path.exists():
        return True  # Optional check if metadata file does not exist

    with open(path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    if "dynamic_features" in meta:
        expected = len(meta["dynamic_features"])
        actual = split_tensors["X_dynamic"].shape[2]
        if actual != expected:
            raise TensorValidationError(
                f"Dynamic feature dimension mismatch in split '{split_name}': "
                f"feature_groups.json defines {expected} features, but X_dynamic has shape {split_tensors['X_dynamic'].shape} (features={actual})."
            )

    if "static_num_features" in meta:
        expected = len(meta["static_num_features"])
        actual = split_tensors["X_static_num"].shape[1]
        if actual != expected:
            raise TensorValidationError(
                f"Static numerical feature dimension mismatch in split '{split_name}': "
                f"feature_groups.json defines {expected} features, but X_static_num has shape {split_tensors['X_static_num'].shape} (features={actual})."
            )

    if "static_cat_features" in meta:
        expected = len(meta["static_cat_features"])
        actual = split_tensors["X_static_cat"].shape[1]
        if actual != expected:
            raise TensorValidationError(
                f"Static categorical feature dimension mismatch in split '{split_name}': "
                f"feature_groups.json defines {expected} features, but X_static_cat has shape {split_tensors['X_static_cat'].shape} (features={actual})."
            )

    return True


def validate_split_tensors(
    split_tensors: Dict[str, np.ndarray],
    split_name: str = "train",
    sequence_length: int = 7,
    num_classes: int = 5,
    metadata_path: Optional[Union[Path, str]] = FEATURE_GROUPS_PATH,
) -> bool:
    """Validates tensor properties for a single dataset split.

    Args:
        split_tensors: Dictionary containing tensors for a split.
        split_name: Name of the dataset split (e.g., 'train', 'validation', 'test').
        sequence_length: Expected sequence length for dynamic inputs. Defaults to 7.
        num_classes: Expected number of target classes. Defaults to 5.
        metadata_path: Optional path to feature_groups.json for feature ordering/count verification.

    Returns:
        bool: True if validation succeeds.

    Raises:
        TensorValidationError: If any validation rule is violated.
        TypeError: If tensor input types are invalid.
    """
    required_keys = ["X_dynamic", "X_static_num", "X_static_cat", "y"]
    
    # 1. Existence and Type Checks
    for key in required_keys:
        if key not in split_tensors:
            raise TensorValidationError(
                f"Missing required tensor key '{key}' in split '{split_name}'."
            )
        tensor = split_tensors[key]
        if not isinstance(tensor, np.ndarray):
            raise TypeError(
                f"Tensor '{key}' in split '{split_name}' must be a numpy.ndarray, got {type(tensor)}."
            )

    x_dyn = split_tensors["X_dynamic"]
    x_snum = split_tensors["X_static_num"]
    x_scat = split_tensors["X_static_cat"]
    y = split_tensors["y"]

    # 2. Tensor Ranks
    if x_dyn.ndim != 3:
        raise TensorValidationError(
            f"Split '{split_name}' X_dynamic must be rank 3 (samples, timesteps, features), got rank {x_dyn.ndim} with shape {x_dyn.shape}."
        )
    if x_snum.ndim != 2:
        raise TensorValidationError(
            f"Split '{split_name}' X_static_num must be rank 2 (samples, features), got rank {x_snum.ndim} with shape {x_snum.shape}."
        )
    if x_scat.ndim != 2:
        raise TensorValidationError(
            f"Split '{split_name}' X_static_cat must be rank 2 (samples, categories), got rank {x_scat.ndim} with shape {x_scat.shape}."
        )
    if y.ndim != 2:
        raise TensorValidationError(
            f"Split '{split_name}' y must be rank 2 (samples, classes), got rank {y.ndim} with shape {y.shape}."
        )

    # 3. Sample Count Consistency
    n_dyn, n_snum, n_scat, n_y = x_dyn.shape[0], x_snum.shape[0], x_scat.shape[0], y.shape[0]
    if not (n_dyn == n_snum == n_scat == n_y):
        raise TensorValidationError(
            f"Sample count mismatch in split '{split_name}': "
            f"X_dynamic={n_dyn}, X_static_num={n_snum}, X_static_cat={n_scat}, y={n_y}."
        )

    # 4. Sequence Length Check
    if x_dyn.shape[1] != sequence_length:
        raise TensorValidationError(
            f"Sequence length mismatch for X_dynamic in split '{split_name}': "
            f"expected {sequence_length}, got {x_dyn.shape[1]}."
        )

    # 5. Data Types
    if not np.issubdtype(x_dyn.dtype, np.floating):
        raise TypeError(
            f"X_dynamic dtype in split '{split_name}' must be floating point, got {x_dyn.dtype}."
        )
    if not np.issubdtype(x_snum.dtype, np.floating):
        raise TypeError(
            f"X_static_num dtype in split '{split_name}' must be floating point, got {x_snum.dtype}."
        )
    if not np.issubdtype(x_scat.dtype, np.integer):
        raise TypeError(
            f"X_static_cat dtype in split '{split_name}' must be integer, got {x_scat.dtype}."
        )
    if not np.issubdtype(y.dtype, np.number):
        raise TypeError(
            f"Target y dtype in split '{split_name}' must be numeric (int32, float32, etc.), got {y.dtype}."
        )

    # 6. NaN and Inf checks
    for key, tensor in split_tensors.items():
        if np.isnan(tensor).any():
            raise TensorValidationError(
                f"NaN values detected in tensor '{key}' for split '{split_name}'."
            )
        if np.isinf(tensor).any():
            raise TensorValidationError(
                f"Inf values detected in tensor '{key}' for split '{split_name}'."
            )

    # 7. One-Hot Target Check
    if y.shape[1] != num_classes:
        raise TensorValidationError(
            f"Target y class dimension mismatch in split '{split_name}': "
            f"expected {num_classes}, got {y.shape[1]}."
        )
    if (y < 0).any() or (y > 1).any():
        raise TensorValidationError(
            f"Target y values in split '{split_name}' must be within range [0, 1]."
        )
    row_sums = np.sum(y, axis=1)
    if not np.allclose(row_sums, 1.0):
        raise TensorValidationError(
            f"Target y in split '{split_name}' is not valid one-hot encoded (row sums do not equal 1)."
        )

    # 8. Categorical Index Range Check
    if (x_scat < 0).any():
        raise TensorValidationError(
            f"Negative category indices found in X_static_cat for split '{split_name}'."
        )

    # 9. Feature Group Metadata Verification
    if metadata_path is not None:
        validate_feature_groups(split_tensors, split_name=split_name, metadata_path=metadata_path)

    return True


def validate_dataset(
    data: Dict[str, Dict[str, np.ndarray]],
    sequence_length: int = 7,
    num_classes: int = 5,
    metadata_path: Optional[Union[Path, str]] = FEATURE_GROUPS_PATH,
) -> bool:
    """Validates tensor properties across all dataset splits.

    Args:
        data: Nested dictionary structured by split ('train', 'validation', 'test').
        sequence_length: Expected sequence length for dynamic inputs. Defaults to 7.
        num_classes: Expected number of target classes. Defaults to 5.
        metadata_path: Optional path to feature_groups.json for feature count verification.

    Returns:
        bool: True if validation succeeds for all splits.

    Raises:
        TensorValidationError: If any validation check fails.
    """
    for split_name, split_tensors in data.items():
        validate_split_tensors(
            split_tensors=split_tensors,
            split_name=split_name,
            sequence_length=sequence_length,
            num_classes=num_classes,
            metadata_path=metadata_path,
        )
    return True
