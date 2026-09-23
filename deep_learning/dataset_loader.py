"""Dataset loader module for Phase 2A exported NumPy tensors."""

from pathlib import Path
from typing import Dict, Union

import numpy as np

from config.paths import DL_DATA_DIR


def load_split_tensors(
    split: str,
    data_dir: Union[Path, str] = DL_DATA_DIR,
    suffix: str = "",
) -> Dict[str, np.ndarray]:
    """Loads Phase 2A NumPy tensors for a specific dataset split.

    Args:
        split: The dataset split name ('train', 'validation', or 'test').
        data_dir: Directory containing the .npy tensor files. Defaults to DL_DATA_DIR.
        suffix: Optional filename suffix (e.g., '_v2'). Defaults to empty string.

    Returns:
        Dict[str, np.ndarray]: A dictionary containing loaded tensors with keys:
            - 'X_dynamic'
            - 'X_static_num'
            - 'X_static_cat'
            - 'y'

    Raises:
        FileNotFoundError: If any expected tensor file does not exist.
    """
    path_dir = Path(data_dir)
    
    files = {
        "X_dynamic": path_dir / f"X_dynamic_{split}{suffix}.npy",
        "X_static_num": path_dir / f"X_static_num_{split}{suffix}.npy",
        "X_static_cat": path_dir / f"X_static_cat_{split}{suffix}.npy",
        "y": path_dir / f"y_{split}{suffix}.npy",
    }
    
    tensors: Dict[str, np.ndarray] = {}
    for key, filepath in files.items():
        if not filepath.exists():
            raise FileNotFoundError(f"Tensor file not found at: {filepath}")
        tensors[key] = np.load(filepath)

    return tensors


def load_all_tensors(
    data_dir: Union[Path, str] = DL_DATA_DIR,
    suffix: str = "",
) -> Dict[str, Dict[str, np.ndarray]]:
    """Loads Phase 2A NumPy tensors across all dataset splits.

    Args:
        data_dir: Directory containing the .npy tensor files. Defaults to DL_DATA_DIR.
        suffix: Optional filename suffix (e.g., '_v2'). Defaults to empty string.

    Returns:
        Dict[str, Dict[str, np.ndarray]]: Nested dictionary structured by split:
            {
                'train': {'X_dynamic': ..., 'X_static_num': ..., 'X_static_cat': ..., 'y': ...},
                'validation': {...},
                'test': {...}
            }
    """
    splits = ["train", "validation", "test"]
    return {
        split: load_split_tensors(split=split, data_dir=data_dir, suffix=suffix)
        for split in splits
    }
