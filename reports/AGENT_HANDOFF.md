# AI-AQI Repository Agent Handoff Document

> [!IMPORTANT]
> **CRITICAL RULE FOR FUTURE CODING AGENTS:**
> - **DO NOT RETRAIN THE CANONICAL FINAL DL MODEL** unless a new experiment is explicitly requested by the user.
> - **DO NOT ALTER THE FROZEN 2025 HOLDOUT TEST RESULTS**.
> - **DO NOT MODIFY THE FROZEN RANDOM FOREST BASELINE**.
> - The current state represents a complete, verified, paper-ready research milestone.

---

## 1. What is Complete & Frozen

1. **Preprocessing Contract (Phase 2A)**: Immutable NumPy tensors stored in `data/dl/`. Shapes: `X_dynamic` `(N, 7, 24)`, `X_static_num` `(N, 16)`, `X_static_cat` `(N, 3)`, `y` `(N, 5)`. Splits: Train (2020–2023, $N=43,622$), Val (2024, $N=10,770$), Test (2025, $N=10,740$).
2. **`tf.data` Input Pipeline (Phase 2B)**: `deep_learning/tf_dataset.py` with batching, shuffling (train split only), caching, and prefetching.
3. **Hybrid Architecture (Phase 2C)**: `deep_learning/architecture.py` — Multi-input Functional Keras model (1D-CNN + BiLSTM + Bahdanau Temporal Attention + Static Numerical MLP + Static Categorical Embeddings $\rightarrow$ Fusion MLP $\rightarrow$ Softmax 5). Parameter count: 115,453.
4. **Validation Improvement Suite (Phase 2D)**:
   - **Experiment 5**: Threshold Calibration ($\tau^* = [0.80, 1.00, 0.90, 0.75, 0.05]$).
   - **Experiment 2**: Power-0.75 Damped Class Weighting ($w_k^{0.75}$).
5. **Canonical DL Model Checkpoint**: [`experiments/final_model/best_dl_model.keras`](file:///c:/Users/R%20Raghavendra/Downloads/MP/proj_folder/AI-AQI-Models/experiments/final_model/best_dl_model.keras) (Backup copy: `saved_models/best_dl_model.keras`).
6. **Out-of-Time 2025 Holdout Evaluation**: Evaluated ONCE ONLY in `deep_learning/evaluate_final_2025.py`. Results: **DL Macro F1 = 0.4741**, **Accuracy = 65.98%** vs **RF Macro F1 = 0.4599**, **Accuracy = 62.25%**.
7. **Production Infrastructure**:
   - `deep_learning/inference.py`: Production `AQIInferenceEngine` with shape and value validation.
   - `hardware/`: `arduino_cloud.py`, `sensor_buffer.py` `(1, 7, 24)`, `live_preprocessing.py`.
   - `deployment/`: `api.py` (FastAPI REST service), `dashboard/` (Leaflet.js map), `README.md`.
   - `federated/`: `simulation.py` (Simulated 3-hospital FedAvg Flower loop).
8. **Unit Test Suite**: 42 unit tests across `tests/` passing with 0 failures.

---

## 2. Key Directories & Artifact Locations

- **Canonical DL Model Record**: [`experiments/final_model/FINAL_OFFICIAL_DL_MODEL.json`](file:///c:/Users/R%20Raghavendra/Downloads/MP/proj_folder/AI-AQI-Models/experiments/final_model/FINAL_OFFICIAL_DL_MODEL.json)
- **Publication Tables**: [`experiments/final_model/paper_ready_results.md`](file:///c:/Users/R%20Raghavendra/Downloads/MP/proj_folder/AI-AQI-Models/experiments/final_model/paper_ready_results.md)
- **Presentation Summary**: [`experiments/final_model/presentation_summary.md`](file:///c:/Users/R%20Raghavendra/Downloads/MP/proj_folder/AI-AQI-Models/experiments/final_model/presentation_summary.md)
- **Master Research Record**: [`FINAL_AI_AQI_MODEL_RECORD.md`](file:///c:/Users/R%20Raghavendra/Downloads/MP/proj_folder/AI-AQI-Models/FINAL_AI_AQI_MODEL_RECORD.md)
- **Project Master Status**: [`PROJECT_COMPLETION_STATUS.md`](file:///c:/Users/R%20Raghavendra/Downloads/MP/proj_folder/AI-AQI-Models/PROJECT_COMPLETION_STATUS.md)
- **Final Evaluation Artifacts**: [`experiments/phase2d/final_2025/`](file:///c:/Users/R%20Raghavendra/Downloads/MP/proj_folder/AI-AQI-Models/experiments/phase2d/final_2025/)
- **Phase Reports**: [`phase_reports/`](file:///c:/Users/R%20Raghavendra/Downloads/MP/proj_folder/AI-AQI-Models/phase_reports/)

---

## 3. Exact Model Inputs & Decision Rule

For any future inference call:
- `X_dynamic`: `(1, 7, 24)` float32
- `X_static_num`: `(1, 16)` float32
- `X_static_cat`: `(1, 3)` int32 (`district_id` 0–29, `land_use_id` 0–5, `urban_rural_id` 0–2)
- **Decision Rule**: `prediction = argmax(P_k / [0.8, 1.0, 0.9, 0.75, 0.05])`

---

## 4. What Remains / Optional Future Extensions

- Real physical deployment of Arduino IoT Cloud REST API credentials (hardware code is complete in simulation mode).
- Extension of Federated Learning from 3-node simulation to physical network deployment.
