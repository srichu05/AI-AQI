# AI-AQI Project Master Research & Technical Documentation Record

**Repository:** `AI-AQI-Models`  
**Date:** August 2026  
**Status:** **CANONICAL MASTER RESEARCH RECORD — FROZEN**

---

## 1. Project Overview
The AI-AQI project is a multi-stage machine learning and deep learning research initiative designed to predict multi-class Air Quality Index (AQI) health risk levels across complex spatiotemporal environments. The system combines temporal pollutant sequences with static spatial, land-use, and demographic features to forecast 5 distinct AQI risk categories.

---

## 2. Research Objective
The primary research objective is to develop a spatiotemporal neural network architecture (combining 1D Convolutional layers, Bidirectional LSTMs, and Bahdanau Temporal Attention) capable of outperforming classical ML benchmarks (Random Forest, SVM, Logistic Regression) on an out-of-time unseen 2025 test holdout set, specifically optimizing Macro F1-score and minority severe risk recall.

---

## 3. Dataset Description
The dataset integrates ground-level monitoring station telemetries, satellite remote sensing retrievals (AOD, CO, NO2, O3), meteorological measurements (Temperature, Relative Humidity, Wind Speed, Precipitation), spatial geographical features, road density, green cover percentages, and population density across 30 regional districts.

---

## 4. Dataset Dimensions
- **Total Spatiotemporal Observations ($N$)**: 65,132 rows
- **Dynamic Temporal Sequence**: 7 daily timesteps ($T=7$) of 24 hourly environmental features ($D=24$)
- **Static Numerical Features**: 16 continuous features
- **Static Categorical Features**: 3 categorical indices (`district_id`, `land_use_id`, `urban_rural_id`)

---

## 5. Time Period
- **Total Span**: 6 full years (2020 through 2025)
- **Training Period**: 2020–2023 (4 years, $N=43,622$, 66.98%)
- **Validation Period**: 2024 (1 year, $N=10,770$, 16.54%)
- **Test Period (Holdout)**: 2025 (1 year, $N=10,740$, 16.48%)

---

## 6. Geographic Coverage
30 regional districts spanning urban cores, industrial complexes, suburban corridors, transport nodes, green belts, and agricultural zones.

---

## 7. Target Definition
5-class categorical AQI risk indicator derived from ground-level PM2.5 monitoring thresholds adhering to public health standard guidelines.

---

## 8. Class Definitions
- **Class 0 (Low / Good)**: AQI 0 – 50
- **Class 1 (Moderate)**: AQI 51 – 100
- **Class 2 (Unhealthy)**: AQI 101 – 150
- **Class 3 (Very Unhealthy)**: AQI 151 – 200
- **Class 4 (Severe / Hazardous)**: AQI > 200

---

## 9. Class Distribution
- **Class 0 (Low)**: 12,440 Train (28.52%), 3,058 Val (28.39%), 2,526 Test (23.52%)
- **Class 1 (Moderate)**: 18,340 Train (42.04%), 4,665 Val (43.31%), 5,335 Test (49.67%) — *Majority Class*
- **Class 2 (Unhealthy)**: 11,010 Train (25.24%), 2,742 Val (25.46%), 2,608 Test (24.28%)
- **Class 3 (Very Unhealthy)**: 1,507 Train (3.45%), 265 Val (2.46%), 243 Test (2.26%)
- **Class 4 (Severe)**: 325 Train (0.75%), 40 Val (0.37%), 28 Test (0.26%) — *Extreme Minority Class (56.43x Imbalance Ratio)*

---

## 10. Preprocessing Contract
Phase 2A immutable exported NumPy tensors (`data/dl/`). Feature scaling applied via robust min-max normalization. Target vectors are one-hot encoded `(N, 5)`.

---

## 11. Phase 2A Summary
Completed inside `AI-AQI-Preprocessing`. Tensors exported and validated with zero missing values or non-finite entries.

---

## 12. Phase 2B Summary
Implemented `deep_learning/tf_dataset.py`, establishing an optimized `tf.data.Dataset` input pipeline with batching, shuffling (training split only), memory caching, and prefetching.

---

## 13. Phase 2C Summary
Constructed `deep_learning/architecture.py`, establishing the hybrid multi-input Keras Functional API model architecture.

---

## 14. Phase 2D Summary
Conducted pre-training audit (12/12 checks passed), forensic audit, threshold calibration (Experiment 5), and damped class weighting (Experiment 2).

---

## 15. ML Phase 3 Summary
Evaluated classical machine learning algorithms on Phase 3B selected feature subset (25 features) using 2020–2023 training and 2024 validation data.

---

## 16. Random Forest Feature Selection
Selected top 25 features from 75 candidates using Random Forest MDI importance. Excluded leakage targets (`pm25_ground`, `PM25_est`, `exposure_index`, `risk_class`, `risk_label`, `year`). Retained `pm10_ground` as a valid independent predictor.

---

## 17. Every ML Model Inventory
1. **Random Forest (Final Classical Benchmark)**: `RandomForestClassifier(n_estimators=100, max_depth=15, min_samples_leaf=4, class_weight='balanced')`. Trained.
2. **Logistic Regression**: `LogisticRegression(C=10.0, class_weight='balanced')`. Trained.
3. **Linear SVM (Calibrated)**: `CalibratedClassifierCV(LinearSVC(C=0.1, class_weight='balanced'))`. Trained.
4. **XGBoost Classifier**: *NOT TRAINED* (Excluded in Phase 3 design).

---

## 18. Final RF Model Summary
- Checkpoint: `saved_models/baselines/random_forest.joblib`
- 2025 Test Metrics: Macro F1 = **0.4599**, Accuracy = **62.25%**, Balanced Acc = **48.21%**.

---

## 19. Final DL Model Summary
- Checkpoint: [`experiments/final_model/best_dl_model.keras`](file:///c:/Users/R%20Raghavendra/Downloads/MP/proj_folder/AI-AQI-Models/experiments/final_model/best_dl_model.keras)
- Candidate ID: `phase2d_dl_pow75_weights_calibrated`
- 2025 Test Metrics: Macro F1 = **0.4741**, Accuracy = **65.98%**, Weighted F1 = **0.6560**.

---

## 20. Deep Learning Architecture Specification
- **Dynamic Branch**: (7, 24) $\rightarrow$ Conv1D (64 filters, kernel 3) $\rightarrow$ BatchNorm $\rightarrow$ ReLU $\rightarrow$ MaxPool1D(2) $\rightarrow$ BiLSTM (64 per direction) $\rightarrow$ **Bahdanau Temporal Attention** (64 units) $\rightarrow$ Dense (64, ReLU).
- **Static Numerical Branch**: (16) $\rightarrow$ Dense (64) $\rightarrow$ BatchNorm $\rightarrow$ ReLU $\rightarrow$ Dropout (0.3) $\rightarrow$ Dense (32, ReLU).
- **Static Categorical Branch**: (3) $\rightarrow$ Embeddings (District 30$\rightarrow$16, Land Use 6$\rightarrow$4, Urban/Rural 3$\rightarrow$2) $\rightarrow$ Concat (22) $\rightarrow$ Dense (16, ReLU).
- **Fusion Network**: Concat (112) $\rightarrow$ Dense (128) $\rightarrow$ BatchNorm $\rightarrow$ ReLU $\rightarrow$ Dropout (0.3) $\rightarrow$ Dense (64, ReLU) $\rightarrow$ Softmax (5).
- **Parameters**: 115,453 total (114,941 trainable).

---

## 21. Training Procedure
- Optimizer: Adam (`lr=1e-3`, `min_lr=1e-6`, `ReduceLROnPlateau` factor 0.5, patience 4)
- Loss: Categorical Cross-Entropy
- Batch Size: 32
- Max Epochs: 40 (Best epoch: **16**, early stopping at epoch 26)
- Seed: `42`

---

## 22. Class Imbalance Strategy
Power-0.75 Damped Class Weighting ($w_k^{0.75}$):
$w = [0.7664, 0.5728, 0.8401, 3.7321, 11.6853]$ (reduced weight ratio from 55.74x to 20.40x).

---

## 23. Threshold Calibration
Validation-derived decision threshold vector: $\tau^* = [0.80, 1.00, 0.90, 0.75, 0.05]$ applied via $\arg\max_k (P_k / \tau_k)$.

---

## 24. Validation Protocol
Trained on 2020–2023, evaluated strictly on 2024 Validation set ($N=10,770$) for threshold tuning and model selection.

---

## 25. Test Protocol
Untouched out-of-time 2025 Test holdout ($N=10,740$) evaluated ONCE ONLY following model freeze.

---

## 26. Final 2025 Test Results
- Macro F1: **0.4741**
- Accuracy: **65.98%**
- Macro Precision: **0.4936**
- Macro Recall: **0.4616**
- Weighted F1: **0.6560**
- Balanced Accuracy: **46.16%**

---

## 27. ML vs DL Comparison
The Deep Learning model achieved a higher Macro F1 than the Random Forest baseline by **+0.0142** (+3.09% relative gain) and +3.73% higher accuracy.

---

## 28. Error Analysis
Minority class misclassifications primarily occur adjacent to class boundaries (e.g. Class 3 mistaken for Class 2).

---

## 29. Class 3 Analysis (Very Unhealthy, $N=243$)
- RF: Precision = 33.92%, Recall = 37.45%, F1 = 0.3560
- DL: Precision = **37.85%**, Recall = 27.57%, F1 = 0.3190
- DL reduced false alarms (+3.93% higher precision).

---

## 30. Class 4 Analysis (Severe, $N=28$)
- RF: Precision = 4.62%, Recall = 10.71%, F1 = 0.0645
- DL: Precision = **11.11%**, Recall = **10.71%**, F1 = **0.1091** (+69.15% higher F1). Both models hit 3/28 cases; DL generated less than half the false positives of RF.

---

## 31. Live Sensor Architecture
Arduino IoT Cloud integration streaming raw sensor readings mapped via `LiveTelemetryPreprocessor` into a rolling 7-day `(1, 7, 24)` temporal buffer in `hardware/sensor_buffer.py`.

---

## 32. Inference Pipeline
Implemented in `deep_learning/inference.py` (`AQIInferenceEngine`) with shape, non-finite NaN, and categorical boundary guards.

---

## 33. REST API
Implemented in `deployment/api.py` using FastAPI providing `/health`, `/predict`, and `/map_data` endpoints.

---

## 34. GIS Dashboard
Implemented in `deployment/dashboard/` (`index.html`, `dashboard.js`, `style.css`) using Leaflet.js rendering 30-district interactive spatial risk maps.

---

## 35. Federated Learning
Simulated 3-hospital node (Hospital A, B, C) FedAvg Flower simulation implemented in `federated/simulation.py`. Explicitly labeled as **SIMULATED FEDERATED LEARNING**.

---

## 36. Deployment Architecture
Documented in `deployment/README.md` with configurable model paths and zero `.venv` dependency.

---

## 37. Reproducibility
Fixed random seed `42` across NumPy, TensorFlow, and Python random modules. All experimental seeds and parameters logged.

---

## 38. Known Limitations
Wide confidence intervals on Class 4 Severe events due to small test support ($N=28$).

---

## 39. Scientific Caveats
Decision threshold calibration was fitted on 2024 validation probabilities; minor out-of-time calibration decay occurs on 2025 test data.

---

## 40. Future Work
Integration of satellite multi-spectral raster imagery, expansion to multi-city physical IoT sensor networks, and physical clinical node federated deployment.
