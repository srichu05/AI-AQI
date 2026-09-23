# AI-AQI Project — Master Implementation Record

**Document Version:** 1.0.0  
**Project Name:** AI-Driven Air Pollution and Environmental Health Risk Support System (AI-AQI)  
**Status:** CDSS Module Complete & Validated (Standalone Engine Milestone)  

> [!IMPORTANT]
> **LEGAL & NON-DIAGNOSTIC SCOPE DISCLAIMER**  
> The Clinical Decision Support System (CDSS) module acts strictly as an **Environmental Health-Risk Support Engine** and **NOT** a medical diagnostic system. It does not diagnose disease (such as asthma, COPD, eczema, or dermatitis), prescribe medications, alter medical treatment plans, or replace professional clinical judgment.

---

## 1. System Overview & Component Matrix

The repository combines multi-modal environmental data, Deep Learning AQI risk forecasting, and rule-based personalized health risk stratification.

| Component Name | Status | Location / Artifact | Key Technical Specification |
| :--- | :---: | :--- | :--- |
| **Phase 2A Data Preprocessing** | **COMPLETE** | `data/dl/*.npy` | Immutable normalized tensors ($N=65,132$ samples total across Train, Val, Test). |
| **Phase 2B Data Pipeline** | **COMPLETE** | `deep_learning/tf_dataset.py` | High-performance `tf.data.Dataset` pipeline with batching, shuffling, caching, prefetching. |
| **Phase 2C Hybrid DL Model** | **COMPLETE** | `deep_learning/architecture.py` | 1D-CNN + BiLSTM + Bahdanau Temporal Attention + Static Embeddings ($115,453$ parameters). |
| **Phase 2D Optimization** | **COMPLETE** | `experiments/final_model/best_dl_model.keras` | Calibrated threshold decision rule $\tau^* = [0.80, 1.00, 0.90, 0.75, 0.05]$ (Val F1: $0.5552$). |
| **Random Forest Baseline** | **COMPLETE** | `saved_models/baselines/random_forest.joblib` | 25 engineered features (2025 Test F1: $0.4599$). |
| **Inference Pipeline** | **COMPLETE** | `deep_learning/inference.py` | Production `AQIInferenceEngine` with shape, bounds, NaN validation and `predict_single()`. |
| **Hardware Telemetry** | **COMPLETE** | `hardware/` | `sensor_buffer.py` rolling $(1, 7, 24)$ window buffer + Arduino Cloud connector. |
| **REST API Service** | **COMPLETE** | `deployment/api.py` | FastAPI endpoints `/health`, `/predict`, `/map_data`. |
| **CDSS Engine (NEW)** | **COMPLETE** | `cdss/` | Standalone Python module for environmental health-risk evaluation & preventive guidance. |

---

## 2. CDSS Package Architecture

The CDSS package (`cdss/`) is built as a clean, modular Python package isolated from Flask/FastAPI routes and live hardware.

```
cdss/
├── __init__.py               # Main package interface exposing CDSSService and schemas
├── schemas.py                # Pydantic data validation schemas for PatientContext & EnvironmentalInput
├── environmental_risk.py     # Rule-based environmental classification & environmental_risk_index calculator
├── respiratory_rules.py      # Personalized respiratory environmental risk stratification logic
├── skin_rules.py             # Pollution-associated skin environmental risk stratification logic
├── recommendation_engine.py  # Preventive, non-prescriptive recommendation engine
├── cdss_service.py           # Master service orchestrator returning structured payload
└── README.md                 # Complete CDSS documentation & architectural specification
```

### Supporting Demonstration & Test Files
- [`examples/test_cdss.py`](file:///Users/jeevithal/Downloads/AI-AQI-Models%202/examples/test_cdss.py): Standalone CLI demonstration script.
- [`tests/test_cdss.py`](file:///Users/jeevithal/Downloads/AI-AQI-Models%202/tests/test_cdss.py): Automated unit test suite covering logical boundaries and threshold checks.

---

## 3. Detailed CDSS Technical Rules & Specifications

### 3.1 Input Data Schemas (`cdss/schemas.py`)
- **`PatientContext`**: Validates `age` ($0–120$), `smoking_status` (`never`, `former`, `current`), `respiratory_condition` (`none`, `asthma`, `copd`, `other`), `respiratory_severity`, `skin_condition` (`none`, `eczema`, `dermatitis`, `other`), `skin_severity`, `latitude` ($-90.0$ to $90.0$), and `longitude` ($-180.0$ to $180.0$).
- **`EnvironmentalInput`**: Validates non-negative pollutant concentrations ($\ge 0.0\,\mu g/m^3$) for $PM_{2.5}, PM_{10}, NO_2, O_3, SO_2, CO$. Includes optional `model_predicted_risk` field for AI model integration.

---

### 3.2 Environmental Risk Classification & Index (`cdss/environmental_risk.py`)

#### Classification Rules:
- **HIGH**: $PM_{2.5} > 60.0\,\mu g/m^3$ **OR** $NO_2 > 80.0\,\mu g/m^3$
- **MODERATE**: $25.0 \le PM_{2.5} \le 60.0\,\mu g/m^3$ **OR** $40.0 \le NO_2 \le 80.0\,\mu g/m^3$
- **LOW**: Otherwise

#### `environmental_risk_index` Calculation Formula:
> *"The environmental_risk_index is a project-defined normalized environmental pollution index used for relative categorization. It is not a clinically validated probability or measure of disease."*

1. Calculate pollutant subscores:
   $$\text{PM2.5\_subscore} = \left(\frac{PM_{2.5}}{60.0}\right) \times 70.0$$
   $$\text{NO2\_subscore} = \left(\frac{NO_2}{80.0}\right) \times 70.0$$
2. Determine raw maximum score:
   $$\text{raw\_score} = \max(\text{PM2.5\_subscore}, \text{NO2\_subscore})$$
3. Range mapping:
   - High Risk: $\text{environmental\_risk\_index} = \min(100, \max(70, \text{round}(\text{raw\_score})))$
   - Moderate Risk: Mapped into $[40, 69]$.
   - Low Risk: Mapped into $[0, 39]$.

---

### 3.3 Personalized Respiratory Risk Stratification (`cdss/respiratory_rules.py`)
- **Terminology**: *"Personalized Respiratory Environmental Risk"* (`respiratory_environmental_risk`).
- **Rule Logic**:
  - Baseline inherited from ambient environmental risk ("Low", "Moderate", "High").
  - Moderate Env Risk + Moderate/Severe Condition $\rightarrow$ Escalates to High.
  - Low Env Risk + Pre-existing Condition $\rightarrow$ Low or Moderate (Low pollution does NOT spuriously trigger High risk).
  - Active Smoking under Moderate/High Env Risk $\rightarrow$ Escalates respiratory concern tier.
  - Contextual Age Modifiers ($<12$ or $>65$) noted as *"age-based contextual vulnerability modifiers"*. Age never independently creates High risk without environmental context.

---

### 3.4 Pollution-Associated Skin Risk Stratification (`cdss/skin_rules.py`)
- **Terminology**: *"Pollution-Associated Skin Environmental Risk"* (`skin_environmental_risk`).
- **Relevant Pollutants**: $PM_{2.5}$ ($>60$ High, $\ge 25$ Moderate) and Ozone $O_3$ ($>100$ High, $\ge 50$ Moderate).
- **Modulation**: Pre-existing skin conditions (eczema, dermatitis) modulate environmental skin risk tier.

---

### 3.5 Preventive Recommendation Engine (`cdss/recommendation_engine.py`)
- **Non-Prescriptive Boundaries**: Zero drug prescriptions, zero dosage recommendations, zero medical treatment plans, zero emergency directives.
- **Guidance Focus**: Outdoor exposure reduction, symptom monitoring, clinician-directed care plan adherence, smoking-cessation support.

---

## 4. Structured Output Payload Schema

The CDSS service (`CDSSService.assess_patient()`) returns a standardized, JSON-serializable output payload:

```json
{
  "environmental_risk": "High",
  "environmental_risk_index": 88,
  "environmental_contributors": [
    "PM2.5",
    "NO2"
  ],
  "respiratory_environmental_risk": "High",
  "respiratory_contributors": [
    "PM2.5",
    "NO2",
    "Existing respiratory condition: asthma (moderate)"
  ],
  "skin_environmental_risk": "High",
  "skin_contributors": [
    "PM2.5"
  ],
  "patient_context_factors": [
    "Existing respiratory condition: asthma (moderate)"
  ],
  "recommendations": [
    "Reduce prolonged exposure to heavily polluted outdoor environments.",
    "Monitor respiratory symptoms.",
    "Follow existing clinician-directed care.",
    "Seek professional medical advice if symptoms worsen.",
    "Reduce direct skin exposure during periods of elevated pollution.",
    "Monitor skin symptoms.",
    "Seek professional medical advice if skin symptoms persist or worsen."
  ],
  "disclaimer": "This system provides environmental health-risk information and preventive guidance. It does not diagnose disease or replace professional clinical judgment."
}
```

---

## 5. Verification & Test Suite Results

- **Existing Unit Tests**: 42 tests across `tests/test_phase2b.py`, `tests/test_phase2c.py`, `tests/test_phase2d.py`, `tests/test_threshold_calibration.py`, `tests/test_hardware.py`, `tests/test_inference.py`.
- **CDSS Unit Tests (`tests/test_cdss.py`)**: 11 tests covering logical boundaries, threshold checks, negative pollution validation, and payload schema assertion.
- **Total Suite**: 53 unit tests.
- **CDSS Test Execution Result**: 11/11 Passed (0 Failures, 0 Errors) in 0.001s.

---

## 6. Trained DL Model Inference Inspection (Future Integration)

Inspection details for future integration of the canonical DL model with the CDSS:

1. **Model Checkpoint Path**: [`experiments/final_model/best_dl_model.keras`](file:///Users/jeevithal/Downloads/AI-AQI-Models%202/experiments/final_model/best_dl_model.keras)
2. **Inference Interface**: `AQIInferenceEngine.predict_single(X_dynamic, X_static_num, X_static_cat)` in `deep_learning/inference.py`.
3. **Input Shapes**:
   - `X_dynamic`: `(1, 7, 24)` float32
   - `X_static_num`: `(1, 16)` float32
   - `X_static_cat`: `(1, 3)` int32 (`district_id`, `land_use_id`, `urban_rural_id`)
4. **Output Decision Rule**: Softmax probabilities $(1, 5) \rightarrow \text{argmax}(P_k / [0.80, 1.00, 0.90, 0.75, 0.05]) \rightarrow$ Risk Class (0: Low, 1: Moderate, 2: Unhealthy, 3: Very Unhealthy, 4: Severe).
5. **Future Coupling**: Passing `AQIInferenceEngine` prediction payload into `EnvironmentalInput.model_predicted_risk` without changing existing DL code or retraining models.
