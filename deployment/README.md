# AI-AQI Deep Learning Model Deployment & Production Guide

This guide documents the procedures for deploying the canonical **AI-AQI Hybrid Deep Learning Model** (`FINAL_OFFICIAL_DL_MODEL`) into production REST API, hardware sensor integration, and GIS dashboard environments.

---

## 1. Architecture & Production Components

```
                +---------------------------------------+
                |    Arduino Cloud Telemetry Sensor     |
                +---------------------------------------+
                                    |
                                    v
                +---------------------------------------+
                |    hardware/live_preprocessing.py     |
                |    hardware/sensor_buffer.py          |
                +---------------------------------------+
                                    |
                                    v (1, 7, 24) + Static Vectors
                +---------------------------------------+
                |     deep_learning/inference.py        |
                |     (AQIInferenceEngine)              |
                +---------------------------------------+
                                    |
            +-----------------------+-----------------------+
            |                                               |
            v                                               |
+-----------------------+                         +-------------------+
|  deployment/api.py    |                         |  GIS Dashboard    |
|  (FastAPI REST App)   |                         |  (Leaflet.js)     |
+-----------------------+                         +-------------------+
```

---

## 2. Model Checkpoint Location

The canonical production model artifact is stored at:
- [`experiments/final_model/best_dl_model.keras`](file:///c:/Users/R%20Raghavendra/Downloads/MP/proj_folder/AI-AQI-Models/experiments/final_model/best_dl_model.keras)
- Alternate path: [`saved_models/best_dl_model.keras`](file:///c:/Users/R%20Raghavendra/Downloads/MP/proj_folder/AI-AQI-Models/saved_models/best_dl_model.keras)

---

## 3. Running the REST API

To launch the FastAPI REST service locally or inside a Docker container:

```bash
# Install production requirements
pip install -r requirements.txt
pip install fastapi uvicorn

# Start FastAPI server on port 8000
uvicorn deployment.api:app --host 0.0.0.0 --port 8000 --reload
```

### API Endpoints
- `GET /health`: Health check and model diagnostic status.
- `POST /predict`: Submit dynamic `(7, 24)` and static features for calibrated AQI prediction.
- `GET /map_data`: Retrieve district risk predictions for GIS rendering.

---

## 4. Launching the GIS Dashboard

The Leaflet.js dashboard located in `deployment/dashboard/index.html` can be served with any static web server:

```bash
python -m http.server 8080 --directory deployment/dashboard
```

Navigate to `http://localhost:8080` in any web browser.

---

## 5. Live Sensor Hardware Integration

To process live telemetry from an Arduino IoT Cloud node:

```python
from hardware.arduino_cloud import ArduinoCloudClient
from hardware.live_preprocessing import LiveTelemetryPreprocessor
from hardware.sensor_buffer import TemporalSensorBuffer, construct_static_vectors
from deep_learning.inference import AQIInferenceEngine

# Initialize client and buffer
client = ArduinoCloudClient(simulate_if_offline=True)
preprocessor = LiveTelemetryPreprocessor()
buffer = TemporalSensorBuffer(sequence_length=7, dynamic_dim=24)
engine = AQIInferenceEngine()

# Process incoming telemetry reading
raw_data = client.fetch_live_telemetry()
dyn_vec = preprocessor.transform_telemetry_to_dynamic_vector(raw_data)
buffer.append_day_features(dyn_vec)

# Execute inference
X_dyn = buffer.get_dynamic_tensor()  # (1, 7, 24)
X_num, X_cat = construct_static_vectors(district_id=0, land_use_id=0, urban_rural_id=0)

prediction = engine.predict_single(X_dyn, X_num, X_cat)
print("Live Forecast:", prediction["risk_label"], prediction["probabilities"])
```

---

## 6. Deployment Environment Variables

Configure the following environment variables if deploying via Docker or Kubernetes:

- `MODEL_PATH`: Custom filesystem path to `best_dl_model.keras`.
- `API_PORT`: Port for FastAPI service (default: `8000`).
- `SIMULATE_SENSOR`: Set to `True` for simulation mode or `False` for live hardware connections.
- `LOG_LEVEL`: Logging verbosity (`INFO`, `DEBUG`, `WARNING`).
