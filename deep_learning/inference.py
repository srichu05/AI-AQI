"""Official Inference Pipeline for the Canonical Deep Learning AQI Risk Model.

Loads the frozen final Keras model (experiments/final_model/best_dl_model.keras)
and applies validation-derived calibrated thresholds ([0.8, 1.0, 0.9, 0.75, 0.05])
via argmax(P_k / tau_k).
"""

from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import tensorflow as tf

import sys
import tempfile
import zipfile

from config.paths import EXPERIMENTS_DIR, SAVED_MODELS_DIR
from deep_learning.architecture import BahdanauAttention, build_model
from deep_learning.threshold_calibration import apply_thresholds

# Alias module for Keras compatibility if needed
try:
    import keras.src.models
    sys.modules["keras.src.models.functional"] = keras.src.models
except Exception:
    pass

logger = logging.getLogger(__name__)

# Default canonical paths and threshold constants
DEFAULT_MODEL_PATH = EXPERIMENTS_DIR / "final_model" / "best_dl_model.keras"
FALLBACK_MODEL_PATH = SAVED_MODELS_DIR / "best_dl_model.keras"
FROZEN_THRESHOLDS = [0.8, 1.0, 0.9, 0.75, 0.05]
CLASS_LABELS = {
    0: "Low",
    1: "Moderate",
    2: "Unhealthy",
    3: "Very Unhealthy",
    4: "Severe",
}

VOCAB_BOUNDS = {
    "district_id": (0, 29),
    "land_use_id": (0, 5),
    "urban_rural_id": (0, 2),
}


class AQIInferenceEngine:
    """Production-ready inference engine for multi-input AQI risk forecasting."""

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        thresholds: Optional[List[float]] = None,
        model_version: str = "FINAL_OFFICIAL_DL_MODEL_v1.0",
    ) -> None:
        """Initializes inference engine and loads the frozen DL checkpoint.

        Args:
            model_path: Optional custom path to best_dl_model.keras. Defaults to canonical location.
            thresholds: Optional custom decision threshold vector. Defaults to FROZEN_THRESHOLDS.
            model_version: Descriptive string identifier for the model.
        """
        self.model_version = model_version
        self.thresholds = thresholds or FROZEN_THRESHOLDS

        target_path = Path(model_path) if model_path else DEFAULT_MODEL_PATH
        if not target_path.exists():
            if FALLBACK_MODEL_PATH.exists():
                target_path = FALLBACK_MODEL_PATH
            else:
                raise FileNotFoundError(f"Canonical DL model checkpoint not found at: {target_path}")

        logger.info(f"Loading official frozen DL model from: {target_path}")
        try:
            self.model = tf.keras.models.load_model(
                target_path,
                custom_objects={"BahdanauAttention": BahdanauAttention},
                safe_mode=False,
                compile=False,
            )
        except Exception as e:
            logger.warning(f"tf.keras.models.load_model direct load note ({e}). Rebuilding architecture & loading weights...")
            self.model = build_model()
            if zipfile.is_zipfile(target_path):
                with zipfile.ZipFile(target_path, "r") as z:
                    if "model.weights.h5" in z.namelist():
                        with tempfile.NamedTemporaryFile(suffix=".weights.h5") as tmp:
                            tmp.write(z.read("model.weights.h5"))
                            tmp.flush()
                            self.model.load_weights(tmp.name)
            else:
                self.model.load_weights(target_path)
        self.model_path = target_path


    def validate_inputs(
        self,
        X_dynamic: np.ndarray,
        X_static_num: np.ndarray,
        X_static_cat: np.ndarray,
    ) -> None:
        """Enforces strict shape, boundary, and data integrity checks on input arrays.

        Args:
            X_dynamic: Dynamic temporal array of shape (batch_size, 7, 24).
            X_static_num: Static numerical array of shape (batch_size, 16).
            X_static_cat: Static categorical array of shape (batch_size, 3).

        Raises:
            ValueError: If shapes, value bounds, or finite data integrity constraints fail.
        """
        # Shape validations
        if X_dynamic.ndim != 3 or X_dynamic.shape[1:] != (7, 24):
            raise ValueError(f"X_dynamic must have shape (N, 7, 24), got {X_dynamic.shape}")

        if X_static_num.ndim != 2 or X_static_num.shape[1] != 16:
            raise ValueError(f"X_static_num must have shape (N, 16), got {X_static_num.shape}")

        if X_static_cat.ndim != 2 or X_static_cat.shape[1] != 3:
            raise ValueError(f"X_static_cat must have shape (N, 3), got {X_static_cat.shape}")

        # Batch size alignment check
        batch_size = X_dynamic.shape[0]
        if X_static_num.shape[0] != batch_size or X_static_cat.shape[0] != batch_size:
            raise ValueError(
                f"Batch size mismatch: X_dynamic ({batch_size}), X_static_num ({X_static_num.shape[0]}), X_static_cat ({X_static_cat.shape[0]})"
            )

        # Finite value checks (No NaN / Inf)
        if not np.all(np.isfinite(X_dynamic)):
            raise ValueError("X_dynamic contains NaN or Inf values.")
        if not np.all(np.isfinite(X_static_num)):
            raise ValueError("X_static_num contains NaN or Inf values.")

        # Categorical ID bounds check
        district_ids = X_static_cat[:, 0]
        land_use_ids = X_static_cat[:, 1]
        urban_rural_ids = X_static_cat[:, 2]

        if np.any(district_ids < 0) or np.any(district_ids > 29):
            raise ValueError(f"district_id out of bounds [0, 29]: {np.unique(district_ids)}")
        if np.any(land_use_ids < 0) or np.any(land_use_ids > 5):
            raise ValueError(f"land_use_id out of bounds [0, 5]: {np.unique(land_use_ids)}")
        if np.any(urban_rural_ids < 0) or np.any(urban_rural_ids > 2):
            raise ValueError(f"urban_rural_id out of bounds [0, 2]: {np.unique(urban_rural_ids)}")

    def predict(
        self,
        X_dynamic: np.ndarray,
        X_static_num: np.ndarray,
        X_static_cat: np.ndarray,
    ) -> List[Dict[str, Any]]:
        """Executes forward prediction and returns calibrated risk forecasts.

        Args:
            X_dynamic: Dynamic array of shape (N, 7, 24).
            X_static_num: Static numerical array of shape (N, 16).
            X_static_cat: Static categorical array of shape (N, 3).

        Returns:
            List[Dict[str, Any]]: Structured list of prediction records for each sample:
                {
                    "risk_class": int (0-4),
                    "risk_label": str ("Low", "Moderate", ...),
                    "probabilities": List[float],
                    "applied_thresholds": List[float],
                    "model_version": str,
                    "timestamp": str (ISO 8601 UTC)
                }
        """
        self.validate_inputs(X_dynamic, X_static_num, X_static_cat)

        model_inputs = {
            "dynamic_input": X_dynamic.astype(np.float32),
            "static_num_input": X_static_num.astype(np.float32),
            "static_cat_input": X_static_cat.astype(np.int32),
        }

        probabilities = self.model.predict(model_inputs, verbose=0)
        calibrated_preds = apply_thresholds(probabilities, self.thresholds)

        results: List[Dict[str, Any]] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        for i in range(len(calibrated_preds)):
            pred_class = int(calibrated_preds[i])
            prob_list = [float(p) for p in probabilities[i]]

            results.append({
                "sample_index": i,
                "risk_class": pred_class,
                "risk_label": CLASS_LABELS[pred_class],
                "probabilities": prob_list,
                "applied_thresholds": list(self.thresholds),
                "model_version": self.model_version,
                "timestamp": now_iso,
            })

        return results

    def predict_single(
        self,
        X_dynamic_single: np.ndarray,
        X_static_num_single: np.ndarray,
        X_static_cat_single: np.ndarray,
    ) -> Dict[str, Any]:
        """Convenience method for predicting a single sample.

        Args:
            X_dynamic_single: (7, 24) or (1, 7, 24) array.
            X_static_num_single: (16,) or (1, 16) array.
            X_static_cat_single: (3,) or (1, 3) array.

        Returns:
            Dict[str, Any]: Single prediction result dictionary.
        """
        dyn = np.expand_dims(X_dynamic_single, axis=0) if X_dynamic_single.ndim == 2 else X_dynamic_single
        num = np.expand_dims(X_static_num_single, axis=0) if X_static_num_single.ndim == 1 else X_static_num_single
        cat = np.expand_dims(X_static_cat_single, axis=0) if X_static_cat_single.ndim == 1 else X_static_cat_single

        return self.predict(dyn, num, cat)[0]
