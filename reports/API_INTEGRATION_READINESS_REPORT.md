# AI-AQI REST API & CDSS Integration-Readiness Report

**Document Version:** 1.0.0  
**Phase:** Pre-API Integration Audit  
**Status:** Readiness Confirmed — Code Changes Pending User Authorization  

---

## Executive Summary

An audit of [`deployment/api.py`](file:///Users/jeevithal/Downloads/AI-AQI-Models%202/deployment/api.py) confirms that the existing FastAPI web service is production-ready, modular, and fully compatible with the newly validated CDSS engine (`CDSSService`).

The API currently serves DL AQI model forecasts via `POST /predict` and spatial predictions via `GET /map_data`. The CDSS service can be cleanly exposed through a dedicated, non-breaking endpoint `POST /cdss/assess`.

> [!IMPORTANT]
> **Zero Code Modifications Made**: No API routes, models, CDSS rules, or tests have been modified during this audit phase.

---

## 1. Audit Answers to Specific Questions

### 1. Current FastAPI Application Structure
- Framework: `FastAPI` with `CORSMiddleware` configured to allow all origins (`*`).
- Dependency Injection / Lifecycle: Global `AQIInferenceEngine` instance lazily instantiated via `get_inference_engine()`.

### 2. Existing `/health` Endpoint
- `GET /health` (Status 200 OK): Returns model loading state, model checkpoint path (`experiments/final_model/best_dl_model.keras`), model version (`FINAL_OFFICIAL_DL_MODEL_v1.0`), and calibration thresholds (`[0.8, 1.0, 0.9, 0.75, 0.05]`).

### 3. Existing `/predict` Endpoint
- `POST /predict` (Status 200 OK): Receives `PredictionRequest` Pydantic payload (`dynamic`, `static_num`, `static_cat`), converts lists to NumPy arrays, executes `eng.predict_single(dyn, num, cat)`, and returns `{"success": True, "prediction": result}`.

### 4. Existing `/map_data` Endpoint
- `GET /map_data` (Status 200 OK): Generates spatial forecasts across 30 district grid coordinates for Leaflet GIS Dashboard rendering.

### 5. How Environmental Prediction Requests Currently Enter the API
- Via JSON payload to `POST /predict`:
  ```json
  {
    "dynamic": {"data": [[... 24 floats ...] ... 7 timesteps ...]},
    "static_num": {"data": [... 16 floats ...]},
    "static_cat": {"data": [district_id, land_use_id, urban_rural_id]}
  }
  ```

### 6. How `AQIInferenceEngine` is Currently Called
- Lazily initialized via `eng = get_inference_engine()`. Single sample inference executes `eng.predict_single(dyn_arr, num_arr, cat_arr)`.

### 7. Current Request / Response Schemas
- **Request**: `PredictionRequest` containing `dynamic: DynamicFeatures`, `static_num: StaticNumFeatures`, `static_cat: StaticCatFeatures`.
- **Response**: `{"success": true, "prediction": { "risk_class": 2, "risk_label": "Unhealthy", "probabilities": [...], ... }}`.

### 8. Can `PatientContext` be Safely Added Without Breaking `/predict`?
- **YES**. `/predict` remains 100% untouched and backward compatible. A dedicated new endpoint `POST /cdss/assess` will handle CDSS requests.

### 9. Can `CDSSService` be Exposed Through `POST /cdss/assess`?
- **YES**. A dedicated, clean REST endpoint `POST /cdss/assess` will be defined in `deployment/api.py`.

### 10. What Environmental Data is Available at API Request Time?
- Dynamic feature matrix contains ambient pollutant concentrations ($PM_{2.5}, PM_{10}, NO_2, SO_2, CO, O_3$) as the first 6 indices of each timestep.
- Point pollutant readings can also be passed directly in an `environmental` payload block.

### 11. Does `/predict` Response Contain the DL Payload Required by CDSS?
- **YES**. `result["prediction"]` returned by `predict_single()` contains the exact dictionary payload (`risk_class`, `risk_label`, `probabilities`, `applied_thresholds`, `model_version`) expected by `cdss/dl_adapter.py`.

### 12. What Additional Data is Required to Call `CDSSService`?
- Patient context parameters (`PatientContext`):
  - `age` ($0–120$)
  - `smoking_status` (`"never"`, `"former"`, `"current"`)
  - `respiratory_condition` (`"none"`, `"asthma"`, `"copd"`, `"other"`)
  - `respiratory_severity` (`"none"`, `"mild"`, `"moderate"`, `"severe"`)
  - `skin_condition` (`"none"`, `"eczema"`, `"dermatitis"`, `"other"`)
  - `skin_severity` (`"none"`, `"mild"`, `"moderate"`, `"severe"`)
  - `latitude`, `longitude` coordinates

### 13. Exact Files That Would Need Modification
- [`deployment/api.py`](file:///Users/jeevithal/Downloads/AI-AQI-Models%202/deployment/api.py): Add Pydantic API schemas for CDSS request/response and register `POST /cdss/assess`.

### 14. Exact New Files / Schemas / Tests Required
- `tests/test_api.py` *(NEW)*: Unit tests for API endpoints (`/health`, `/predict`, `/map_data`, and `POST /cdss/assess`).

### 15. Can Existing 64 Tests Remain Unchanged?
- **YES**. All 64 existing unit tests (42 model/hardware tests + 11 CDSS tests + 11 DL adapter tests) will remain 100% unchanged and passing.

---

## 2. Target API Architecture

```mermaid
flowchart TD
    subgraph Client Requests
        R1["POST /predict\n(DL Feature Tensors)"]
        R2["POST /cdss/assess\n(Patient Profile + Env Inputs)"]
    end

    subgraph FastAPI Router (deployment/api.py)
        E1["Existing /predict Handler"]
        E2["New /cdss/assess Handler"]
    end

    subgraph Core Engines
        M["AQIInferenceEngine\n(deep_learning/inference.py)"]
        A["DL Adapter\n(cdss/dl_adapter.py)"]
        C["CDSSService\n(cdss/cdss_service.py)"]
    end

    R1 --> E1 --> M --> Res1["Raw Prediction JSON"]
    R2 --> E2
    E2 --> M
    M --> A --> C
    E2 --> C --> Res2["Structured CDSS Response JSON"]
```

---

## 3. Proposed Schema for `POST /cdss/assess`

### Request Payload (`CDSSAssessmentRequest`)
```json
{
  "patient": {
    "age": 45,
    "smoking_status": "current",
    "respiratory_condition": "asthma",
    "respiratory_severity": "moderate",
    "skin_condition": "none",
    "skin_severity": "none",
    "latitude": 12.9716,
    "longitude": 77.5946
  },
  "environmental": {
    "pm25": 75.0,
    "pm10": 110.0,
    "no2": 85.0,
    "o3": 40.0,
    "so2": 12.0,
    "co": 1.2
  },
  "prediction_features": {
    "dynamic": {"data": [[... 24 floats ...] ... 7 timesteps ...]},
    "static_num": {"data": [... 16 floats ...]},
    "static_cat": {"data": [district_id, land_use_id, urban_rural_id]}
  }
}
```

*Note*: `prediction_features` is optional. If omitted, CDSS operates in standalone rule-based mode; if supplied, CDSS executes `AQIInferenceEngine.predict_single()` and passes the prediction into `CDSSService`.
