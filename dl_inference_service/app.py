"""Standalone Hugging Face Spaces Inference Service for AI-AQI Deep Learning Risk Forecasting.

Preserves the exact canonical model architecture, input tensor schemas,
feature ordering, data types, and calibrated decision threshold contract.

Security Notice:
    Keras `safe_mode=False` is strictly required to deserialize the three inline
    Lambda layers slicing static categorical features (`x[:, 0]`, `x[:, 1]`, `x[:, 2]`).
    This service only loads the trusted, verified internal artifact `best_dl_model.keras`.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import numpy as np
from pydantic import BaseModel, Field

# Ensure standalone custom layer is registered before model deserialization
try:
    from attention import BahdanauAttention
except ImportError:
    from .attention import BahdanauAttention

import keras

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("hf_inference_service")

# Model configuration constants
MODEL_VERSION = "FINAL_OFFICIAL_DL_MODEL_v1.0"
FROZEN_THRESHOLDS = [0.8, 1.0, 0.9, 0.75, 0.05]
CLASS_LABELS: Dict[int, str] = {
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

# Resolve model path
BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "best_dl_model.keras"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup and shutdown events.
    Loads the Keras deep learning model once at application startup.
    """
    logger.info("Initializing Hugging Face Inference Service...")
    logger.info("Keras version: %s", keras.__version__)

    if not MODEL_PATH.exists():
        err_msg = f"Model artifact not found at {MODEL_PATH}."
        logger.error(err_msg)
        app.state.model = None
        app.state.model_loaded = False
        app.state.load_error = err_msg
    else:
        try:
            logger.info("Loading model artifact from: %s", MODEL_PATH)
            # safe_mode=False is mandatory due to Lambda layer slicing on static_cat_input.
            # compile=False disables deserializing optimizers/loss since this is pure inference.
            loaded_model = keras.models.load_model(
                str(MODEL_PATH),
                custom_objects={"BahdanauAttention": BahdanauAttention},
                safe_mode=False,
                compile=False,
            )
            app.state.model = loaded_model
            app.state.model_loaded = True
            app.state.load_error = None
            logger.info("Model loaded successfully into memory. Ready for inference.")
        except Exception as exc:
            err_msg = f"Failed to deserialize model: {exc}"
            logger.critical(err_msg, exc_info=True)
            app.state.model = None
            app.state.model_loaded = False
            app.state.load_error = str(exc)

    yield

    logger.info("Shutting down Hugging Face Inference Service.")
    app.state.model = None
    app.state.model_loaded = False


app = FastAPI(
    title="AI-AQI Hugging Face Inference Service",
    description="Standalone low-latency microservice for multi-input hybrid CNN-BiLSTM-Attention AQI risk inference.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for cross-origin requests from frontend and main backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic Request & Response Schemas
# ---------------------------------------------------------------------------

class DynamicData(BaseModel):
    """7 daily timesteps of 24 dynamic features."""
    data: List[List[float]] = Field(
        ...,
        description="7x24 matrix containing 7 daily timesteps of 24 environmental/meteorological features.",
    )


class StaticNumData(BaseModel):
    """16 continuous static numerical features."""
    data: List[float] = Field(
        ...,
        description="16 continuous static numerical features (coordinates, elevation, emission proxies).",
    )


class StaticCatData(BaseModel):
    """3 categorical indices: [district_id (0-29), land_use_id (0-5), urban_rural_id (0-2)]."""
    data: List[int] = Field(
        ...,
        description="3 categorical indices: [district_id, land_use_id, urban_rural_id].",
    )


class PredictionRequest(BaseModel):
    """Flexible prediction payload supporting both structured objects and raw arrays."""
    dynamic: Union[DynamicData, List[List[float]], List[List[List[float]]]] = Field(
        ...,
        description="Dynamic sequence tensor: either nested {'data': [[...]]}, single (7, 24), or batch (N, 7, 24).",
    )
    static_num: Union[StaticNumData, List[float], List[List[float]]] = Field(
        ...,
        description="Static numerical tensor: either nested {'data': [...]}, single (16,), or batch (N, 16).",
    )
    static_cat: Union[StaticCatData, List[int], List[List[int]]] = Field(
        ...,
        description="Static categorical tensor: either nested {'data': [...]}, single (3,), or batch (N, 3).",
    )
    feature_vector_id: Optional[int] = Field(
        default=None,
        description="Optional upstream database feature vector ID for traceability.",
    )
    device_id: Optional[str] = Field(
        default=None,
        description="Optional device identifier.",
    )


class SinglePredictionResult(BaseModel):
    sample_index: int = Field(default=0, description="Index within the submitted batch.")
    risk_class: int = Field(..., ge=0, le=4, description="Calibrated risk class index (0 to 4).")
    risk_label: str = Field(..., description="Human-readable AQI risk category name.")
    probabilities: List[float] = Field(..., description="Softmax probability distribution over the 5 classes.")
    applied_thresholds: List[float] = Field(..., description="Decision thresholds applied to probability scores.")
    model_version: str = Field(..., description="Model version tag.")
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp of inference execution.")
    feature_vector_id: Optional[int] = None
    device_id: Optional[str] = None


class PredictionResponse(BaseModel):
    success: bool
    prediction: Optional[SinglePredictionResult] = None
    predictions: Optional[List[SinglePredictionResult]] = None


# ---------------------------------------------------------------------------
# Preprocessing and Validation Helpers
# ---------------------------------------------------------------------------

def extract_and_validate_tensors(payload: PredictionRequest) -> Dict[str, np.ndarray]:
    """Extracts, casts, and thoroughly validates input tensors.

    Returns:
        Dict with keys 'dynamic_input', 'static_num_input', 'static_cat_input'.

    Raises:
        ValueError with clear explanatory message on validation failures.
    """
    # 1. Extract dynamic array
    if isinstance(payload.dynamic, DynamicData):
        dyn_raw = payload.dynamic.data
    elif isinstance(payload.dynamic, dict):
        dyn_raw = payload.dynamic.get("data", payload.dynamic)
    else:
        dyn_raw = payload.dynamic

    try:
        dyn_arr = np.array(dyn_raw, dtype=np.float32)
    except Exception as e:
        raise ValueError(f"Could not convert dynamic input to float32 array: {e}")

    if dyn_arr.ndim == 2:
        if dyn_arr.shape != (7, 24):
            raise ValueError(f"Dynamic input must have shape (7, 24) for single sample, got {dyn_arr.shape}")
        dyn_arr = np.expand_dims(dyn_arr, axis=0)
    elif dyn_arr.ndim == 3:
        if dyn_arr.shape[1:] != (7, 24):
            raise ValueError(f"Dynamic input must have shape (N, 7, 24) for batch sample, got {dyn_arr.shape}")
    else:
        raise ValueError(f"Dynamic input must be 2D (7, 24) or 3D (N, 7, 24), got {dyn_arr.ndim}D")

    batch_size = dyn_arr.shape[0]

    # 2. Extract static_num array
    if isinstance(payload.static_num, StaticNumData):
        num_raw = payload.static_num.data
    elif isinstance(payload.static_num, dict):
        num_raw = payload.static_num.get("data", payload.static_num)
    else:
        num_raw = payload.static_num

    try:
        num_arr = np.array(num_raw, dtype=np.float32)
    except Exception as e:
        raise ValueError(f"Could not convert static_num input to float32 array: {e}")

    if num_arr.ndim == 1:
        if num_arr.shape != (16,):
            raise ValueError(f"Static numerical input must have length 16, got length {num_arr.shape[0]}")
        num_arr = np.expand_dims(num_arr, axis=0)
    elif num_arr.ndim == 2:
        if num_arr.shape[1] != 16:
            raise ValueError(f"Static numerical input must have shape (N, 16), got {num_arr.shape}")
    else:
        raise ValueError(f"Static numerical input must be 1D (16,) or 2D (N, 16), got {num_arr.ndim}D")

    if num_arr.shape[0] != batch_size:
        raise ValueError(f"Batch size mismatch: dynamic has {batch_size} samples, static_num has {num_arr.shape[0]}")

    # 3. Extract static_cat array
    if isinstance(payload.static_cat, StaticCatData):
        cat_raw = payload.static_cat.data
    elif isinstance(payload.static_cat, dict):
        cat_raw = payload.static_cat.get("data", payload.static_cat)
    else:
        cat_raw = payload.static_cat

    try:
        cat_arr = np.array(cat_raw, dtype=np.int32)
    except Exception as e:
        raise ValueError(f"Could not convert static_cat input to int32 array: {e}")

    if cat_arr.ndim == 1:
        if cat_arr.shape != (3,):
            raise ValueError(f"Static categorical input must have length 3 [district_id, land_use_id, urban_rural_id], got length {cat_arr.shape[0]}")
        cat_arr = np.expand_dims(cat_arr, axis=0)
    elif cat_arr.ndim == 2:
        if cat_arr.shape[1] != 3:
            raise ValueError(f"Static categorical input must have shape (N, 3), got {cat_arr.shape}")
    else:
        raise ValueError(f"Static categorical input must be 1D (3,) or 2D (N, 3), got {cat_arr.ndim}D")

    if cat_arr.shape[0] != batch_size:
        raise ValueError(f"Batch size mismatch: dynamic has {batch_size} samples, static_cat has {cat_arr.shape[0]}")

    # 4. Check finite numbers (No NaN or Inf)
    if not np.all(np.isfinite(dyn_arr)):
        raise ValueError("Dynamic input contains non-finite values (NaN or Inf).")
    if not np.all(np.isfinite(num_arr)):
        raise ValueError("Static numerical input contains non-finite values (NaN or Inf).")

    # 5. Check categorical vocabulary bounds
    district_ids = cat_arr[:, 0]
    land_use_ids = cat_arr[:, 1]
    urban_rural_ids = cat_arr[:, 2]

    if np.any(district_ids < VOCAB_BOUNDS["district_id"][0]) or np.any(district_ids > VOCAB_BOUNDS["district_id"][1]):
        raise ValueError(
            f"district_id out of bounds [{VOCAB_BOUNDS['district_id'][0]}, {VOCAB_BOUNDS['district_id'][1]}]: {np.unique(district_ids).tolist()}"
        )
    if np.any(land_use_ids < VOCAB_BOUNDS["land_use_id"][0]) or np.any(land_use_ids > VOCAB_BOUNDS["land_use_id"][1]):
        raise ValueError(
            f"land_use_id out of bounds [{VOCAB_BOUNDS['land_use_id'][0]}, {VOCAB_BOUNDS['land_use_id'][1]}]: {np.unique(land_use_ids).tolist()}"
        )
    if np.any(urban_rural_ids < VOCAB_BOUNDS["urban_rural_id"][0]) or np.any(urban_rural_ids > VOCAB_BOUNDS["urban_rural_id"][1]):
        raise ValueError(
            f"urban_rural_id out of bounds [{VOCAB_BOUNDS['urban_rural_id'][0]}, {VOCAB_BOUNDS['urban_rural_id'][1]}]: {np.unique(urban_rural_ids).tolist()}"
        )

    return {
        "dynamic_input": dyn_arr,
        "static_num_input": num_arr,
        "static_cat_input": cat_arr,
    }


def apply_decision_thresholds(probabilities: np.ndarray, thresholds: List[float]) -> np.ndarray:
    """Applies validation-calibrated class decision thresholds.

    Formula:
        adjusted_score_k = P_k / tau_k
        predicted_class = argmax_k(adjusted_score_k)
    """
    thresh_arr = np.asarray(thresholds, dtype=np.float64)
    adjusted_scores = probabilities / thresh_arr
    return np.argmax(adjusted_scores, axis=1)


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------

@app.get("/", status_code=status.HTTP_200_OK)
def root() -> Dict[str, Any]:
    """Root metadata endpoint."""
    return {
        "service": "AI-AQI Hugging Face Inference Service",
        "version": "1.0.0",
        "model_version": MODEL_VERSION,
        "status": "online",
        "endpoints": {
            "health": "/health",
            "predict": "/predict",
            "docs": "/docs",
        },
    }


@app.get("/health", status_code=status.HTTP_200_OK)
def health(request: Request) -> Dict[str, Any]:
    """Health check endpoint confirming model status, readiness, and configuration."""
    model_loaded = getattr(request.app.state, "model_loaded", False)
    load_error = getattr(request.app.state, "load_error", None)

    if not model_loaded:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "status": "unhealthy",
                "model_loaded": False,
                "error": load_error or "Model is not loaded into memory.",
            },
        )

    return {
        "status": "healthy",
        "model_loaded": True,
        "model_version": MODEL_VERSION,
        "device": "CPU",
        "thresholds": FROZEN_THRESHOLDS,
        "class_labels": CLASS_LABELS,
        "contract": {
            "input_shapes": {
                "dynamic_input": "(batch, 7, 24) float32",
                "static_num_input": "(batch, 16) float32",
                "static_cat_input": "(batch, 3) int32",
            },
            "vocab_bounds": VOCAB_BOUNDS,
            "decision_rule": "argmax_k(P_k / tau_k)",
        },
    }


@app.post("/predict", status_code=status.HTTP_200_OK, response_model=PredictionResponse)
def predict(payload: PredictionRequest, request: Request) -> Dict[str, Any]:
    """Executes DL model inference and returns calibrated AQI risk predictions.

    Supports both single-sample and batch prediction payloads.
    """
    model = getattr(request.app.state, "model", None)
    if model is None:
        load_error = getattr(request.app.state, "load_error", "Model unavailable.")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Inference model is not loaded: {load_error}",
        )

    # 1. Parse and validate inputs
    try:
        tensors = extract_and_validate_tensors(payload)
    except ValueError as val_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(val_err),
        )
    except Exception as exc:
        logger.error("Failed to parse request tensors: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Malformed input schema: {exc}",
        )

    # 2. Execute forward pass
    try:
        raw_probabilities = model.predict(tensors, verbose=0)
    except Exception as inf_err:
        logger.error("Model forward execution failed: %s", inf_err, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Model forward pass execution error: {inf_err}",
        )

    # 3. Apply decision thresholds
    calibrated_classes = apply_decision_thresholds(raw_probabilities, FROZEN_THRESHOLDS)

    # 4. Format response
    now_iso = datetime.now(timezone.utc).isoformat()
    results: List[Dict[str, Any]] = []

    for i in range(len(calibrated_classes)):
        cls_idx = int(calibrated_classes[i])
        probs = [float(p) for p in raw_probabilities[i]]
        results.append({
            "sample_index": i,
            "risk_class": cls_idx,
            "risk_label": CLASS_LABELS[cls_idx],
            "probabilities": probs,
            "applied_thresholds": FROZEN_THRESHOLDS,
            "model_version": MODEL_VERSION,
            "timestamp": now_iso,
            "feature_vector_id": payload.feature_vector_id,
            "device_id": payload.device_id,
        })

    # Return prediction for single sample and predictions list for batch
    if len(results) == 1:
        return {
            "success": True,
            "prediction": results[0],
            "predictions": results,
        }
    else:
        return {
            "success": True,
            "prediction": results[0],
            "predictions": results,
        }
