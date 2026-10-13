---
title: AI AQI Inference Service
emoji: 🌫️
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# AI-AQI Hugging Face Inference Service

Standalone, lightweight REST microservice serving the official hybrid deep learning model (`CNN + BiLSTM + Attention + MLP`) for air quality index (AQI) environmental risk classification.

Designed for independent deployment to **Hugging Face Spaces** (Free CPU Hardware Tier) or any containerized edge environment, completely decoupled from PostgreSQL, GIS shapefiles, and clinical decision support systems.

---

## Architecture & Contract Overview

### 1. Multi-Input Tensor Schema

The deep learning model accepts three distinct input tensors:

| Input Name | Shape | Data Type | Description & Value Constraints |
| :--- | :--- | :--- | :--- |
| `dynamic_input` | `(N, 7, 24)` | `float32` | 7 daily temporal steps of 24 dynamic pollutant/meteorological features |
| `static_num_input` | `(N, 16)` | `float32` | 16 static continuous features (coordinates, elevation, emission proxies) |
| `static_cat_input` | `(N, 3)` | `int32` | 3 categorical indices: `[district_id, land_use_id, urban_rural_id]` |

#### Categorical Vocabulary Bounds:
- `district_id`: Integer in range `[0, 29]` (30 Karnataka districts)
- `land_use_id`: Integer in range `[0, 5]` (6 distinct land-use classifications)
- `urban_rural_id`: Integer in range `[0, 2]` (3 categories: Urban, Semi-Urban, Rural)

### 2. Validation-Calibrated Decision Threshold Contract

The model outputs raw 5-class softmax probabilities $P = [P_0, P_1, P_2, P_3, P_4]$. Rather than standard uncalibrated argmax, decision thresholds tuned on the validation set are applied:

$$\text{adjusted\_score}_k = \frac{P_k}{\tau_k}$$
$$\hat{y} = \arg\max_{k \in \{0, 1, 2, 3, 4\}} \text{adjusted\_score}_k$$

Where the frozen threshold vector is:
$$\tau^* = [0.80, 1.00, 0.90, 0.75, 0.05]$$

#### Output Risk Classes:
- `0`: **Low**
- `1`: **Moderate**
- `2`: **Unhealthy**
- `3`: **Very Unhealthy**
- `4`: **Severe**

---

## Security Analysis: Keras `safe_mode=False` Deserialization

### Background & Technical Requirement
When loading `best_dl_model.keras` via Keras 3 (`keras.models.load_model`), setting `safe_mode=False` is **strictly mandatory**.

**Why?**
The model architecture employs three inline Keras `Lambda` layers to partition the 2D categorical tensor `static_cat_input` of shape `(batch, 3)` into individual integer scalar slices:
- `Lambda(lambda x: x[:, 0])` $\rightarrow$ feeds into `district_embedding`
- `Lambda(lambda x: x[:, 1])` $\rightarrow$ feeds into `land_use_embedding`
- `Lambda(lambda x: x[:, 2])` $\rightarrow$ feeds into `urban_rural_embedding`

In Keras 3, `safe_mode=True` blocks the deserialization of arbitrary Python bytecode present in `Lambda` layers to prevent arbitrary code execution from untrusted model files.

### Security Implications & Mitigation
1. **Trusted Artifact Guarantee:** This microservice exclusively loads the internally-trained and verified checkpoint `best_dl_model.keras` co-located in the repository. It **never** accepts, downloads, or deserializes arbitrary model files from untrusted user requests.
2. **Read-Only / Compile Disabled:** The model is deserialized with `compile=False`, ensuring no optimizer states, custom losses, or unneeded training artifacts are evaluated.
3. **Immutability in Production:** In production Docker containers on Hugging Face Spaces, the model artifact is baked into the immutable container image.

---

## Local Development & Setup

### Prerequisites
- Python 3.10 – 3.13
- pip and virtual environment tooling

### Installation

```bash
# 1. Navigate to the service directory
cd hf_inference_service

# 2. Create a virtual environment
python -m venv venv

# On Linux/macOS:
source venv/bin/activate
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt
```

### Running Locally

```bash
uvicorn app:app --host 0.0.0.0 --port 7860 --reload
```

The service will start at `http://localhost:7860`.
Interactive OpenAPI documentation will be accessible at `http://localhost:7860/docs`.

---

## API Specification & Examples

### 1. Health Check: `GET /health`

Confirms model readiness, device target, threshold configuration, and schema contracts.

#### Request:
```bash
curl -X GET http://localhost:7860/health
```

#### Response (`200 OK`):
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_version": "FINAL_OFFICIAL_DL_MODEL_v1.0",
  "device": "CPU",
  "thresholds": [0.8, 1.0, 0.9, 0.75, 0.05],
  "class_labels": {
    "0": "Low",
    "1": "Moderate",
    "2": "Unhealthy",
    "3": "Very Unhealthy",
    "4": "Severe"
  },
  "contract": {
    "input_shapes": {
      "dynamic_input": "(batch, 7, 24) float32",
      "static_num_input": "(batch, 16) float32",
      "static_cat_input": "(batch, 3) int32"
    },
    "vocab_bounds": {
      "district_id": [0, 29],
      "land_use_id": [0, 5],
      "urban_rural_id": [0, 2]
    },
    "decision_rule": "argmax_k(P_k / tau_k)"
  }
}
```

---

### 2. Prediction: `POST /predict`

Executes multi-input model inference and returns calibrated risk classification.

The endpoint supports:
1. **Frontend Nested Format:** `{ "dynamic": { "data": [...] }, "static_num": { "data": [...] }, "static_cat": { "data": [...] } }`
2. **Direct Array Format:** `{ "dynamic": [...], "static_num": [...], "static_cat": [...] }`
3. Single samples (`7x24`, `16`, `3`) or batch samples (`Nx7x24`, `Nx16`, `Nx3`).

#### Example Request (Single Sample):
```bash
curl -X POST http://localhost:7860/predict \
  -H "Content-Type: application/json" \
  -d '{
    "dynamic": {
      "data": [
        [0.1, 0.2, 0.1, 0.3, 0.2, 0.1, 0.4, 0.2, 0.1, 0.3, 0.2, 0.1, 0.2, 0.1, 0.3, 0.2, 0.1, 0.4, 0.2, 0.1, 0.3, 0.2, 0.1, 0.2],
        [0.2, 0.1, 0.2, 0.2, 0.1, 0.3, 0.2, 0.1, 0.2, 0.1, 0.3, 0.2, 0.1, 0.2, 0.1, 0.3, 0.2, 0.1, 0.2, 0.1, 0.3, 0.2, 0.1, 0.2],
        [0.1, 0.3, 0.2, 0.1, 0.2, 0.1, 0.3, 0.2, 0.1, 0.2, 0.1, 0.3, 0.2, 0.1, 0.2, 0.1, 0.3, 0.2, 0.1, 0.2, 0.1, 0.3, 0.2, 0.1],
        [0.3, 0.2, 0.1, 0.2, 0.1, 0.3, 0.2, 0.1, 0.2, 0.1, 0.3, 0.2, 0.1, 0.2, 0.1, 0.3, 0.2, 0.1, 0.2, 0.1, 0.3, 0.2, 0.1, 0.2],
        [0.2, 0.1, 0.3, 0.2, 0.1, 0.2, 0.1, 0.3, 0.2, 0.1, 0.2, 0.1, 0.3, 0.2, 0.1, 0.2, 0.1, 0.3, 0.2, 0.1, 0.2, 0.1, 0.3, 0.2],
        [0.1, 0.2, 0.1, 0.3, 0.2, 0.1, 0.2, 0.1, 0.3, 0.2, 0.1, 0.2, 0.1, 0.3, 0.2, 0.1, 0.2, 0.1, 0.3, 0.2, 0.1, 0.2, 0.1, 0.3],
        [0.2, 0.3, 0.1, 0.2, 0.1, 0.2, 0.1, 0.3, 0.2, 0.1, 0.2, 0.1, 0.3, 0.2, 0.1, 0.2, 0.1, 0.3, 0.2, 0.1, 0.2, 0.1, 0.3, 0.2]
      ]
    },
    "static_num": {
      "data": [12.97, 12.97, 1.5, 25.0, 5.0, 8000.0, 3.5, 77.59, 77.59, 920.0, 0.15, 0.85, 0.45, 260.0, 0.75, 12.0]
    },
    "static_cat": {
      "data": [0, 1, 0]
    }
  }'
```

#### Response (`200 OK`):
```json
{
  "success": true,
  "prediction": {
    "sample_index": 0,
    "risk_class": 1,
    "risk_label": "Moderate",
    "probabilities": [
      0.00288887950591743,
      0.9786438345909119,
      0.01770932599902153,
      0.000672159018,
      8.580436406191438e-05
    ],
    "applied_thresholds": [0.8, 1.0, 0.9, 0.75, 0.05],
    "model_version": "FINAL_OFFICIAL_DL_MODEL_v1.0",
    "timestamp": "2026-10-12T12:00:00+00:00",
    "feature_vector_id": null,
    "device_id": null
  },
  "predictions": [
    {
      "sample_index": 0,
      "risk_class": 1,
      "risk_label": "Moderate",
      "probabilities": [
        0.00288887950591743,
        0.9786438345909119,
        0.01770932599902153,
        0.000672159018,
        8.580436406191438e-05
      ],
      "applied_thresholds": [0.8, 1.0, 0.9, 0.75, 0.05],
      "model_version": "FINAL_OFFICIAL_DL_MODEL_v1.0",
      "timestamp": "2026-10-12T12:00:00+00:00",
      "feature_vector_id": null,
      "device_id": null
    }
  ]
}
```

---

## Deploying to Hugging Face Spaces

### Step-by-Step Manual Deployment Guide

1. Log in to [Hugging Face](https://huggingface.co/) and navigate to **New Space** (`https://huggingface.co/new-space`).
2. Configure Space settings:
   - **Space Name**: e.g., `ai-aqi-inference`
   - **License**: `mit` (or preferred)
   - **Select Space SDK**: Choose **Docker** -> **Blank**.
   - **Space Hardware**: Select **CPU basic • 2 vCPU • 16 GB RAM • Free**.
   - **Space visibility**: Public (or Private).
3. Clone or push the contents of `hf_inference_service/` to the Hugging Face repository:
   ```bash
   git remote add space https://huggingface.co/spaces/<YOUR_HF_USERNAME>/<SPACE_NAME>
   git push space main
   ```
   Or upload the files directly via the Hugging Face web UI:
   - `Dockerfile`
   - `.dockerignore`
   - `requirements.txt`
   - `attention.py`
   - `app.py`
   - `best_dl_model.keras`
   - `README.md`
4. The Space will automatically build the Docker container and start Uvicorn on port `7860`.

---

## Safe Public API Testing

Once the Space displays **Running**, test the live endpoints:

### 1. Public Health Check
```bash
curl -X GET "https://<YOUR_HF_USERNAME>-<SPACE_NAME>.hf.space/health"
```

Expected response (`200 OK`):
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_version": "FINAL_OFFICIAL_DL_MODEL_v1.0",
  "device": "CPU",
  "thresholds": [0.8, 1.0, 0.9, 0.75, 0.05]
}
```

### 2. Public Safe Prediction Test
```bash
curl -X POST "https://<YOUR_HF_USERNAME>-<SPACE_NAME>.hf.space/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "dynamic": [[0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1],[0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1],[0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1],[0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1],[0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1],[0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1],[0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1,0.2,0.1]],
    "static_num": [12.97, 12.97, 1.5, 25.0, 5.0, 8000.0, 3.5, 77.59, 77.59, 920.0, 0.15, 0.85, 0.45, 260.0, 0.75, 12.0],
    "static_cat": [0, 1, 0]
  }'
```
