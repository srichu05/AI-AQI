# AI-AQI: Advanced Air Quality Index Forecasting, CDSS & GIS Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg?logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.x-FF6F00.svg?logo=tensorflow&logoColor=white)](https://www.tensorflow.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-4169E1.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An end-to-end, enterprise-grade AI system for real-time Air Quality Index (AQI) telemetry monitoring, spatio-temporal deep learning risk forecasting, personalized Clinical Decision Support (CDSS), and GIS district-level environmental analytics.

---

## 🌟 Executive Overview

The **AI-AQI** platform bridges physical IoT environmental sensors, deep neural spatial-temporal forecasting models, rule-based clinical health guidance, and GIS spatial mapping into a unified microservice architecture. 

It provides real-time particulate matter tracking ($PM_{1.0}$, $PM_{2.5}$, $PM_{10}$), deep learning multi-modal risk prediction, and actionable, patient-contextualized preventive health guidance.

```
       +-----------------------+
       | PMS3003 Sensor Unit  |
       +-----------+-----------+
                   | (UART/Serial)
                   v
       +-----------------------+
       |  ESP32 Microcontroller|
       +-----------+-----------+
                   | (HTTP POST /api/telemetry)
                   v
  +---------------------------------+
  |      FastAPI REST Server        |
  |  (Auth, GIS, CDSS, Inference)   |
  +--------+--------------+---------+
           |              |
           v              v
+--------------------+  +----------------------+
| PostgreSQL Database|  | Deep Learning Model  |
| (sensor_telemetry) |  | (CNN + BiLSTM + Attn)|
+--------------------+  +----------------------+
           ^
           | (REST / WS)
  +--------+------------------------+
  | Modern React + Vite Dashboard   |
  | (Visx Charts, GIS Leaflet Map)  |
  +---------------------------------+
```

---

## ✨ Key Features

### 📡 Real-Time Hardware Telemetry Pipeline
* **Physical PMS3003 Sensor Integration**: Direct sampling of $PM_{1.0}$, $PM_{2.5}$, and $PM_{10}$ particulate concentrations via ESP32 microcontrollers.
* **Persistent PostgreSQL Storage**: Robust telemetry ingestion pipeline inserting validated telemetry records into `public.sensor_telemetry`.
* **Dynamic Visx Visualization**: High-performance 3-series area charts displaying live physical sensor telemetry with interactive crosshairs and tooltip indicators.

### 🧠 Hybrid Deep Learning Architecture
* **Multi-Modal Spatial-Temporal Network**: Combines 1D-CNN feature extraction, Bidirectional LSTM sequence modeling, Bahdanau Temporal Attention mechanisms, and static categorical multi-embeddings ($115,453$ parameters).
* **Calibrated Decision Rules**: Calibrated decision threshold vectors ($\tau^* = [0.80, 1.00, 0.90, 0.75, 0.05]$) optimizing high-risk AQI detection across 5 distinct severity classes.
* **ML Baselines**: Comparative benchmarks including Random Forest, Calibrated Support Vector Machines (SVM), and Logistic Regression.

### 🏥 Clinical Decision Support System (CDSS)
* **Rule-Based Environmental Health Risk Engine**: Calculates a normalized `environmental_risk_index` ($0–100$) based on ambient pollutant levels ($PM_{2.5}$, $PM_{10}$, $NO_2$, $O_3$, $SO_2$, $CO$).
* **Personalized Health Risk Stratification**: Modulates environmental risk against patient context (age, smoking status, pre-existing respiratory conditions like asthma/COPD, and skin conditions like eczema/dermatitis).
* **Preventive Recommendations**: Delivers actionable, clinician-aligned preventive outdoor exposure and symptom monitoring guidance.

### 🗺️ GIS Spatial Risk Analytics
* **Karnataka District Mapping**: Interactive Leaflet GeoJSON visualization covering all 30 Karnataka districts.
* **Data-Grounded z-Score Indicators**: Grounded spatial analytics representing multi-year standardized pollution metrics without artificial physical unit conversions.
* **Temporal Exploration**: Multi-year slider interface enabling temporal comparison of regional pollution trends.

### 🌐 Privacy-Preserving Federated Learning
* **Distributed Simulation Engine**: Modular federated learning simulation module supporting edge-node parameter aggregation across decentralized monitoring stations.

---

## 📁 Repository Structure

```
AI-AQI/
├── cdss/                       # Clinical Decision Support System package
│   ├── cdss_service.py         # Master CDSS service orchestrator
│   ├── environmental_risk.py   # Environmental risk index & classification engine
│   ├── recommendation_engine.py# Non-prescriptive clinical guidance rules
│   ├── respiratory_rules.py    # Respiratory risk stratification logic
│   ├── skin_rules.py           # Dermatological risk stratification logic
│   └── schemas.py              # Pydantic data validation contracts
├── config/                     # Centralized paths and configuration settings
├── data/                       # Datasets & spatial GIS assets
│   ├── gis/                    # Karnataka district GeoJSON boundaries
│   ├── ml/                     # ML-ready historical dataset (dataset_ml_ready.csv)
│   └── dl/                     # Feature groups & deep learning metadata
├── deep_learning/              # Neural network architecture & training code
│   ├── architecture.py         # CNN + BiLSTM + Attention hybrid model definition
│   ├── attention.py            # Custom Bahdanau temporal attention layer
│   ├── inference.py            # AQIInferenceEngine production predictor
│   └── tf_dataset.py           # Optimized tf.data input pipeline
├── deployment/                 # Backend REST API & Database services
│   ├── api.py                  # FastAPI REST endpoints & route controllers
│   ├── database.py             # PostgreSQL async connection pool & models
│   ├── auth.py                 # JWT security, password hashing & auth middleware
│   └── nginx.conf              # Reverse proxy configuration
├── frontend/                   # Modern React 18 + Vite + Tailwind CSS app
│   ├── src/components/         # Telemetry charts, GIS maps, CDSS widgets
│   ├── src/api/                # API client integration modules
│   └── package.json            # Frontend dependency definitions
├── hardware/                   # ESP32 & IoT sensor telemetry integration
│   ├── sensor_buffer.py        # Sliding window telemetry buffer
│   └── environmental_fusion.py # Multi-sensor data fusion engine
├── reports/                    # Complete technical records & architectural audits
├── saved_models/               # Production model binaries (.keras, .joblib)
├── tests/                      # Automated unit test suite (53 tests passing)
├── Dockerfile                  # Multi-stage production container build
├── docker-compose.yml          # Container orchestration specification
└── README.md                   # Project documentation
```

---

## ⚡ Quickstart Guide

### Prerequisites
* **Python**: `3.10+`
* **Node.js**: `18.0+` & `npm`
* **PostgreSQL**: `15+` (or Docker)

---

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/your-username/AI-AQI.git
cd AI-AQI

# Create and activate Python virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies (or requirements)
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env to set POSTGRES_SERVER, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD

# Initialize database schema
python deployment/init_db.py

# Launch FastAPI development server
uvicorn deployment.api:app --reload --host 0.0.0.0 --port 8000
```

Backend API interactive documentation will be accessible at: `http://localhost:8000/docs`

---

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Configure environment variables
cp .env.example .env

# Launch Vite development server
npm run dev
```

Frontend application will be accessible at: `http://localhost:5173`

---

### 3. Docker Container Deployment

Run the complete backend and NGINX frontend stack with Docker Compose:

```bash
docker-compose up --build -d
```

---

## 🔌 Core API Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Server health check probe |
| `POST` | `/api/telemetry` | Ingest real-time PMS3003 sensor telemetry ($PM_{1.0}$, $PM_{2.5}$, $PM_{10}$) |
| `GET` | `/api/telemetry/live` | Retrieve latest live hardware telemetry reading |
| `GET` | `/api/karnataka_map_data?year={year}` | Fetch Karnataka district-level spatial GIS risk metrics |
| `POST` | `/api/cdss/evaluate` | Evaluate personalized CDSS environmental health risk & recommendations |
| `POST` | `/api/predict` | Run deep learning AQI spatial-temporal forecasting model |

---

## 🧪 Automated Testing Suite

The repository includes 53 comprehensive unit tests covering the API routes, CDSS rule logic, threshold calibrations, and hardware buffers.

```bash
# Run backend test suite
pytest tests/ -v
```

```bash
# Run frontend type-check & lint
cd frontend
npm run build
```

---

## ⚠️ Medical & Legal Disclaimer

> [!IMPORTANT]
> The **Clinical Decision Support System (CDSS)** module acts strictly as an **Environmental Health-Risk Support Engine** and **NOT** a medical diagnostic system. It does not diagnose clinical conditions (such as asthma, COPD, or eczema), prescribe medications, alter medical treatment plans, or replace professional clinical judgment.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
