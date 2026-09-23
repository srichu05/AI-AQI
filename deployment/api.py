"""REST API Service for AI-AQI Deep Learning Risk Forecasting & Clinical Decision Support.

Provides production endpoints:
    - GET  /health          : Model health and diagnostic status
    - POST /predict         : Single or batch AQI risk inference (optional Auth persistence)
    - GET  /map_data        : District-wide spatial risk predictions for GIS Dashboard
    - POST /cdss/assess     : Environmental health-risk decision support (rule_based or dl_integrated mode)
    - POST /api/telemetry   : ESP32 sensor telemetry ingestion & PostgreSQL persistence
    - GET  /api/telemetry/latest : Latest persisted sensor telemetry retrieval
    - POST /api/auth/sync   : Synchronizes local PostgreSQL user record with verified Supabase Auth JWT
    - GET  /api/me          : Retrieves authenticated user details & role
    - GET/PUT /api/profile  : Reads/updates user profile & CDSS health risk attributes
    - GET  /api/user/predictions : User-specific prediction & health assessment history
    - GET/POST/DELETE /api/user/locations : User saved environmental monitoring locations
    - GET/PUT /api/user/preferences : User notification & alert threshold preferences
"""

import json
from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Literal, Optional, Tuple
import numpy as np

try:
    from fastapi import Depends, FastAPI, HTTPException, Request, status
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field, field_validator, model_validator
    from sqlalchemy.orm import Session
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from cdss import CDSSService
from deep_learning.inference import AQIInferenceEngine
from deployment.auth import RoleChecker, decode_supabase_jwt, get_current_user, get_optional_current_user, sync_local_user
from deployment.database import (
    AuditLog,
    CDSSAssessment,
    DLPrediction,
    FeatureVector,
    HealthProfile,
    SensorTelemetry,
    User,
    UserLocation,
    UserPredictionHistory,
    UserPreference,
    UserProfile,
    get_db,
)
from hardware.environmental_fusion import EnvironmentalDataFusion
from hardware.live_preprocessing import LiveTelemetryPreprocessor

logger = logging.getLogger(__name__)

# Initialize global singletons lazily
engine: Optional[AQIInferenceEngine] = None
cdss_service_instance: Optional[CDSSService] = None
fusion_engine = EnvironmentalDataFusion()
live_preprocessor = LiveTelemetryPreprocessor()


def get_inference_engine() -> AQIInferenceEngine:
    """Returns or lazily instantiates the global inference engine."""
    global engine
    if engine is None:
        engine = AQIInferenceEngine()
    return engine


def get_cdss_service() -> CDSSService:
    """Returns or lazily instantiates the global CDSS service."""
    global cdss_service_instance
    if cdss_service_instance is None:
        cdss_service_instance = CDSSService()
    return cdss_service_instance


if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="AI-AQI Model Inference & CDSS API",
        description="REST API serving official hybrid Deep Learning AQI forecasts, Clinical Decision Support, IoT Telemetry, and User Application Storage.",
        version="1.2.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------
    # Telemetry Schemas & In-Memory Store
    # ------------------------------------------------------------------

    class TelemetryPayload(BaseModel):
        """ESP32 PMS3003 direct sensor telemetry ingestion payload."""
        device_id: str = Field(
            ...,
            min_length=1,
            description="Unique identifier of the sending ESP32 sensor node.",
            examples=["AI_AQI_SENSOR_NODE_01"],
        )
        pm10_ground: float = Field(
            ...,
            ge=0.0,
            description="PM10 concentration in µg/m³ (non-negative integer or float).",
            examples=[7.0],
        )
        pm25_ground: float = Field(
            ...,
            ge=0.0,
            description="PM2.5 concentration in µg/m³ (non-negative integer or float).",
            examples=[7.0],
        )
        pm1_ground: float = Field(
            ...,
            ge=0.0,
            description="PM1.0 concentration in µg/m³ (non-negative integer or float).",
            examples=[3.0],
        )
        timestamp: Optional[str] = Field(
            default=None,
            description="Optional client timestamp; server-side UTC timestamp assigned if omitted.",
        )

        @field_validator("device_id")
        @classmethod
        def validate_device_id(cls, v: str) -> str:
            if not v or not v.strip():
                raise ValueError("device_id cannot be empty or whitespace-only")
            return v.strip()

        @model_validator(mode="after")
        def validate_non_zero_readings(self) -> "TelemetryPayload":
            if self.pm1_ground == 0.0 and self.pm25_ground == 0.0 and self.pm10_ground == 0.0:
                raise ValueError(
                    "Invalid telemetry payload: pm1_ground, pm25_ground, and pm10_ground cannot all be zero."
                )
            return self

    # In-memory storage buffer for ingested telemetry readings (backward compatibility)
    telemetry_store: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Existing Prediction Schemas
    # ------------------------------------------------------------------

    class DynamicFeatures(BaseModel):
        """Dynamic 7-day temporal window of 24 features per timestep."""
        data: List[List[float]] = Field(
            ...,
            description="7x24 matrix containing 7 daily timesteps of 24 dynamic features.",
        )

    class StaticNumFeatures(BaseModel):
        """Static numerical feature array (16 continuous features)."""
        data: List[float] = Field(
            ...,
            description="16 continuous static numerical features.",
        )

    class StaticCatFeatures(BaseModel):
        """Static categorical IDs [district_id (0-29), land_use_id (0-5), urban_rural_id (0-2)]."""
        data: List[int] = Field(
            ...,
            description="3 categorical indices: [district_id, land_use_id, urban_rural_id].",
        )

    class PredictionRequest(BaseModel):
        """Request payload for model risk prediction."""
        dynamic: DynamicFeatures
        static_num: StaticNumFeatures
        static_cat: StaticCatFeatures
        feature_vector_id: Optional[int] = Field(
            default=None,
            description="Optional foreign key referencing PostgreSQL feature_vectors table.",
        )
        device_id: Optional[str] = Field(
            default=None,
            description="Optional identifier of sending sensor node.",
        )

    # ------------------------------------------------------------------
    # CDSS Assessment Schemas
    # ------------------------------------------------------------------

    class PatientData(BaseModel):
        """Patient demographic and medical risk factor profile."""
        age: int = Field(..., ge=0, le=120, description="Patient age in years.")
        smoking_status: Literal["never", "former", "current"] = Field(
            ..., description="Tobacco smoking status."
        )
        respiratory_condition: Literal["none", "asthma", "copd", "other"] = Field(
            ..., description="Pre-existing respiratory diagnosis."
        )
        respiratory_severity: Literal["none", "mild", "moderate", "severe"] = Field(
            ..., description="Severity of respiratory condition."
        )
        skin_condition: Literal["none", "eczema", "dermatitis", "other"] = Field(
            ..., description="Pre-existing dermatological condition."
        )
        skin_severity: Literal["none", "mild", "moderate", "severe"] = Field(
            ..., description="Severity of skin condition."
        )
        latitude: float = Field(..., ge=-90.0, le=90.0, description="Geographic latitude.")
        longitude: float = Field(..., ge=-180.0, le=180.0, description="Geographic longitude.")

    class EnvironmentalData(BaseModel):
        """Ambient environmental pollutant measurements."""
        pm25: float = Field(..., ge=0.0, description="PM2.5 concentration in µg/m³.")
        pm10: float = Field(..., ge=0.0, description="PM10 concentration in µg/m³.")
        no2: float = Field(..., ge=0.0, description="NO2 concentration in µg/m³.")
        o3: float = Field(..., ge=0.0, description="O3 concentration in µg/m³.")
        so2: float = Field(..., ge=0.0, description="SO2 concentration in µg/m³.")
        co: float = Field(..., ge=0.0, description="CO concentration in µg/m³.")

    class PredictionFeatures(BaseModel):
        """Optional DL feature tensors required for 'dl_integrated' CDSS assessment mode."""
        dynamic: Optional[DynamicFeatures] = None
        static_num: Optional[StaticNumFeatures] = None
        static_cat: Optional[StaticCatFeatures] = None
        feature_vector_id: Optional[int] = None
        device_id: Optional[str] = None

    class CDSSAssessmentRequest(BaseModel):
        """Request payload for CDSS clinical risk assessment."""
        patient: PatientData
        environmental: EnvironmentalData
        prediction_features: Optional[PredictionFeatures] = Field(
            default=None,
            description="If supplied, activates dl_integrated assessment mode using DL model probabilities.",
        )

    # ------------------------------------------------------------------
    # User Application Data Schemas
    # ------------------------------------------------------------------

    class AuthSyncRequest(BaseModel):
        """Optional client request metadata for user synchronization.
        
        NOTE: auth_user_id is NOT accepted from request body. The authoritative identity
        is ALWAYS derived from the verified Bearer JWT 'sub' claim.
        """
        email: Optional[str] = None
        full_name: Optional[str] = None

    class ProfileUpdateRequest(BaseModel):
        full_name: Optional[str] = None
        phone: Optional[str] = None
        preferred_location: Optional[str] = None
        # Health Profile context
        age: Optional[int] = None
        smoking_status: Optional[Literal["never", "former", "current"]] = None
        respiratory_condition: Optional[Literal["none", "asthma", "copd", "other"]] = None
        respiratory_severity: Optional[Literal["none", "mild", "moderate", "severe"]] = None
        skin_condition: Optional[Literal["none", "eczema", "dermatitis", "other"]] = None
        skin_severity: Optional[Literal["none", "mild", "moderate", "severe"]] = None

    class UserLocationCreateRequest(BaseModel):
        label: str = Field(..., min_length=1)
        latitude: float = Field(..., ge=-90.0, le=90.0)
        longitude: float = Field(..., ge=-180.0, le=180.0)
        is_default: bool = False

    class UserPreferenceUpdateRequest(BaseModel):
        alert_threshold_pm25: Optional[float] = Field(default=None, ge=0.0)
        notifications_enabled: Optional[bool] = None
        dark_mode: Optional[bool] = None

    # ------------------------------------------------------------------
    # Sensor Telemetry Ingestion Endpoints (PRESERVED 100%)
    # ------------------------------------------------------------------

    @app.post("/api/telemetry", status_code=status.HTTP_200_OK)
    def receive_telemetry(
        payload: TelemetryPayload,
        request: Request,
        db: Session = Depends(get_db),
    ) -> Dict[str, Any]:
        """Ingests raw ESP32 PMS3003 sensor telemetry, persists to PostgreSQL 'sensor_telemetry', and executes real-time Open-Meteo environmental data fusion into 'feature_vectors'."""
        try:
            dt_utc = datetime.now(timezone.utc)

            # 1. Persist raw sensor reading into PostgreSQL
            db_record = SensorTelemetry(
                device_id=payload.device_id,
                timestamp_utc=dt_utc,
                pm1_ground=payload.pm1_ground,
                pm25_ground=payload.pm25_ground,
                pm10_ground=payload.pm10_ground,
                source="ESP32_PMS3003",
            )
            try:
                db.add(db_record)
                db.commit()
                db.refresh(db_record)
            except Exception as db_err:
                db.rollback()
                logger.error(f"PostgreSQL persistence error: {db_err}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Database write failure: {str(db_err)}",
                )

            client_ip = request.client.host if request.client else "unknown"
            logger.info("============================================================")
            logger.info("[PMS TELEMETRY RECEIVED]")
            logger.info(f"Client IP       : {client_ip}")
            logger.info(f"Device ID       : {payload.device_id}")
            logger.info(f"PM1.0           : {payload.pm1_ground} µg/m³")
            logger.info(f"PM2.5           : {payload.pm25_ground} µg/m³")
            logger.info(f"PM10            : {payload.pm10_ground} µg/m³")
            logger.info("")
            logger.info("DATABASE")
            logger.info("Engine          : PostgreSQL")
            logger.info("Database        : ai_aqi")
            logger.info("Table           : sensor_telemetry")
            logger.info("")
            logger.info("PERSISTENCE")
            logger.info("Insert          : SUCCESS")
            logger.info(f"Record ID       : {db_record.id}")
            logger.info("Commit          : SUCCESS")
            logger.info("")
            logger.info("HTTP RESPONSE")
            logger.info("Status          : 200")
            logger.info("============================================================")

            # 2. Append to in-memory store buffer
            record_dict = db_record.to_dict()
            telemetry_store.append(record_dict)

            # 3. Execute Real-Time Open-Meteo Environmental Data Fusion
            raw_dict = {
                "device_id": payload.device_id,
                "pm1_ground": payload.pm1_ground,
                "pm25_ground": payload.pm25_ground,
                "pm10_ground": payload.pm10_ground,
                "timestamp": dt_utc.isoformat(),
            }
            fused_payload = fusion_engine.fuse_telemetry(raw_dict)
            fv_vector = live_preprocessor.transform_telemetry_to_dynamic_vector(fused_payload)

            fv_json = json.dumps(fv_vector.tolist())
            fv_record = FeatureVector(
                device_id=payload.device_id,
                timestamp_utc=dt_utc,
                pm10_ground=payload.pm10_ground,
                temperature_c=fused_payload["temperature_C"],
                relative_humidity=fused_payload["relative_humidity"],
                wind_speed_10m=fused_payload["wind_speed_10m"],
                co_col=fused_payload["CO_col"],
                no2_col=fused_payload["NO2_col"],
                o3_col=fused_payload["O3_col"],
                so2_ground=fused_payload["so2_ground"],
                aod_actual=fused_payload["AOD_actual"],
                feature_vector_json=fv_json,
                provenance=fused_payload["provenance"],
            )

            try:
                db.add(fv_record)
                db.commit()
                db.refresh(fv_record)
            except Exception as fv_err:
                db.rollback()
                logger.warning(f"Feature vector persistence error: {fv_err}")

            return {
                "status": "received",
                "device_id": payload.device_id,
                "timestamp": dt_utc.isoformat(),
                "telemetry": record_dict,
                "fused_features": {
                    "feature_vector_id": fv_record.id if fv_record else None,
                    "temperature_c": fused_payload["temperature_C"],
                    "relative_humidity": fused_payload["relative_humidity"],
                    "provenance": fused_payload["provenance"],
                },
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in receive_telemetry: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal telemetry processing error: {str(e)}",
            )

    @app.get("/api/telemetry/latest", status_code=status.HTTP_200_OK)
    def get_latest_telemetry(
        db: Session = Depends(get_db),
    ) -> Dict[str, Any]:
        record = (
            db.query(SensorTelemetry)
            .filter(
                ~(
                    (SensorTelemetry.pm1_ground == 0.0)
                    & (SensorTelemetry.pm25_ground == 0.0)
                    & (SensorTelemetry.pm10_ground == 0.0)
                )
            )
            .order_by(SensorTelemetry.timestamp_utc.desc())
            .first()
        )

        if record:
            return {"status": "success", "data": record.to_dict()}

        if telemetry_store:
            return {"status": "success", "data": telemetry_store[-1]}

        return {
            "status": "empty",
            "message": "No sensor telemetry records available.",
            "data": None,
        }

    @app.get("/api/telemetry/history", status_code=status.HTTP_200_OK)
    def get_telemetry_history(
        limit: int = 30,
        db: Session = Depends(get_db),
    ) -> Dict[str, Any]:
        """Returns the most recent N persisted sensor telemetry records from PostgreSQL."""
        records = (
            db.query(SensorTelemetry)
            .filter(
                ~(
                    (SensorTelemetry.pm1_ground == 0.0)
                    & (SensorTelemetry.pm25_ground == 0.0)
                    & (SensorTelemetry.pm10_ground == 0.0)
                )
            )
            .order_by(SensorTelemetry.timestamp_utc.desc())
            .limit(limit)
            .all()
        )

        return {
            "status": "success",
            "data": [r.to_dict() for r in reversed(records)],
        }

    # Helper function for resolving feature vector source
    def resolve_feature_vector_source(
        db: Session,
        explicit_fv_id: Optional[int] = None,
        explicit_device_id: Optional[str] = None,
    ) -> Tuple[Optional[int], Optional[str]]:
        if explicit_fv_id is not None:
            fv = db.query(FeatureVector).filter(FeatureVector.id == explicit_fv_id).first()
            if fv:
                return fv.id, fv.device_id
            return explicit_fv_id, explicit_device_id

        if explicit_device_id:
            fv = (
                db.query(FeatureVector)
                .filter(FeatureVector.device_id == explicit_device_id)
                .order_by(FeatureVector.timestamp_utc.desc())
                .first()
            )
            if fv:
                return fv.id, fv.device_id

        fv = db.query(FeatureVector).order_by(FeatureVector.timestamp_utc.desc()).first()
        if fv:
            return fv.id, fv.device_id

        return None, explicit_device_id

    # ------------------------------------------------------------------
    # Prediction & Health Endpoints
    # ------------------------------------------------------------------

    @app.get("/", status_code=status.HTTP_200_OK)
    def root() -> Dict[str, Any]:
        """Root status endpoint for AI-AQI API."""
        return {
            "status": "online",
            "service": "AI-AQI Model Inference & CDSS API",
            "version": "1.2.0",
            "health": "/health",
            "docs": "/docs",
        }

    @app.get("/health", status_code=status.HTTP_200_OK)
    def health_check() -> Dict[str, Any]:

        """Health check endpoint confirming model status and readiness."""
        eng = get_inference_engine()
        return {
            "status": "healthy",
            "model_loaded": True,
            "model_version": eng.model_version,
            "model_path": str(eng.model_path),
            "thresholds": eng.thresholds,
        }

    @app.post("/predict", status_code=status.HTTP_200_OK)
    def predict_aqi(
        request: PredictionRequest,
        db: Session = Depends(get_db),
        current_user: Optional[User] = Depends(get_optional_current_user),
    ) -> Dict[str, Any]:
        """Executes DL model inference, persists prediction to PostgreSQL 'dl_predictions', and links to user history if authenticated."""
        try:
            dyn_arr = np.array(request.dynamic.data, dtype=np.float32)
            num_arr = np.array(request.static_num.data, dtype=np.float32)
            cat_arr = np.array(request.static_cat.data, dtype=np.int32)

            eng = get_inference_engine()
            result = eng.predict_single(dyn_arr, num_arr, cat_arr)

            # Resolve source feature_vector_id and device_id
            fv_id, dev_id = resolve_feature_vector_source(
                db,
                explicit_fv_id=request.feature_vector_id,
                explicit_device_id=request.device_id,
            )

            # Persist DL Prediction to PostgreSQL
            dt = datetime.now(timezone.utc)
            db_pred = DLPrediction(
                feature_vector_id=fv_id,
                device_id=dev_id,
                risk_class=int(result["risk_class"]),
                risk_label=str(result["risk_label"]),
                probabilities_json=json.dumps(result.get("probabilities", [])),
                applied_thresholds_json=json.dumps(result.get("applied_thresholds", [])),
                model_version=str(result.get("model_version", "FINAL_OFFICIAL_DL_MODEL_v1.0")),
                timestamp_utc=dt,
            )
            try:
                db.add(db_pred)
                db.commit()
                db.refresh(db_pred)
                result["prediction_id"] = db_pred.id
                result["feature_vector_id"] = db_pred.feature_vector_id

                # Link prediction to user history if authenticated
                if current_user:
                    user_history = UserPredictionHistory(
                        user_id=current_user.id,
                        dl_prediction_id=db_pred.id,
                        risk_label=str(result["risk_label"]),
                        latitude=float(request.static_num.data[0]) if len(request.static_num.data) > 0 else None,
                        longitude=float(request.static_num.data[7]) if len(request.static_num.data) > 7 else None,
                    )
                    db.add(user_history)
                    db.commit()

            except Exception as db_err:
                db.rollback()
                logger.warning(f"DLPrediction database persistence warning: {db_err}")

            return {"success": True, "prediction": result}
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            logger.error(f"Inference error: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    @app.get("/map_data", status_code=status.HTTP_200_OK)
    def get_map_data() -> Dict[str, Any]:
        """Returns district-wide risk predictions for Leaflet GIS Dashboard rendering."""
        eng = get_inference_engine()
        districts = []

        district_names = [
            "Central Business District", "North Industrial Zone", "South Residential",
            "East Tech Park", "West Agricultural Belt", "Suburban North",
            "Airport Corridor", "Riverside Basin", "Hill Station Foothills",
            "Highway Node 1", "Highway Node 2", "Port Transit Hub",
            "Forest Reserve Border", "Urban Slum Cluster", "University Campus",
            "Metro Junction East", "Metro Junction West", "Outer Ring Road",
            "Lake Catchment Area", "Industrial Estate B", "Commercial Hub North",
            "Commercial Hub South", "Green Belt West", "Mining Vicinity",
            "Thermal Power Zone", "Coastal Delta North", "Coastal Delta South",
            "Valley Pass East", "Valley Pass West", "Metropolitan Core"
        ]

        np.random.seed(42)
        for d_id in range(30):
            lat = 12.80 + (d_id % 6) * 0.08
            lon = 77.45 + (d_id // 6) * 0.08

            dyn = np.random.normal(45.0, 10.0, size=(1, 7, 24)).astype(np.float32)
            num = np.array([[lat, lat, 1.5, 20.0, 4.0, 7500.0, 3.0, lon, lon, 900.0, 0.1, 0.8, 0.4, 250.0, 0.7, 10.0]], dtype=np.float32)
            cat = np.array([[d_id, d_id % 6, d_id % 3]], dtype=np.int32)

            pred = eng.predict(dyn, num, cat)[0]

            districts.append({
                "district_id": d_id,
                "district_name": district_names[d_id],
                "lat": lat,
                "lon": lon,
                "risk_class": pred["risk_class"],
                "risk_label": pred["risk_label"],
                "probabilities": pred["probabilities"],
                "timestamp": pred["timestamp"],
            })

        return {"success": True, "district_count": len(districts), "districts": districts}

    @app.get("/api/karnataka_map_data", status_code=status.HTTP_200_OK)
    def get_karnataka_map_data(year: Optional[int] = 2025) -> Dict[str, Any]:
        """Returns official Karnataka 30-district polygon GeoJSON joined with real ML-ready dataset features."""
        try:
            import pandas as pd
            import json
            import os

            PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            csv_path = os.path.join(PROJECT_ROOT, "data", "ml", "dataset_ml_ready.csv")
            geojson_path = os.path.join(PROJECT_ROOT, "data", "gis", "karnataka_districts.geojson")


            if not os.path.exists(csv_path) or not os.path.exists(geojson_path):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset or GIS polygon GeoJSON file missing.")

            df = pd.read_csv(csv_path)
            with open(geojson_path, "r", encoding="utf-8") as f:
                geojson_base = json.load(f)

            ALIAS_MAP = {
                "bagalkot": "bagalkote",
                "bangalore": "bengaluru",
                "bangalore rural": "bengaluru rural",
                "bellary": "ballari",
                "bijapur": "vijayapura",
                "chamrajnagar": "chamarajanagar",
                "chikkaballapura": "chikkaballapur",
                "chikmagalur": "chikkamanagaluru",
                "gulbarga": "kalaburagi",
                "mysore": "mysuru",
                "tumkur": "tumakuru",
                "davanagere": "davangere"
            }

            def normalize_name(name: str) -> str:
                low = name.lower().strip()
                return ALIAS_MAP.get(low, low)

            district_cols = [c for c in df.columns if c.startswith("district_") and not c.endswith("_km2")]
            year_df = df[df["year"] == year] if "year" in df.columns and year in df["year"].values else df

            district_data = {}
            for col in district_cols:
                d_name_raw = col.replace("district_", "").title()
                d_norm = normalize_name(d_name_raw)
                d_slice = year_df[year_df[col] == 1]
                if not d_slice.empty:
                    row = d_slice.iloc[-1]
                    district_data[d_norm] = {
                        "district_name": d_name_raw,
                        "has_data": True,
                        "risk_class": int(row["risk_class"]),
                        "risk_label": str(row["risk_label"]),
                        "pm25_ground": float(round(row["pm25_ground"], 2)),
                        "pm10_ground": float(round(row["pm10_ground"], 2)),
                        "exposure_index": float(round(row["exposure_index"], 2)),
                        "temperature_C": float(round(row["temperature_C"], 2)),
                        "relative_humidity": float(round(row["relative_humidity"], 2)),
                        "year": int(row["year"]) if "year" in row else year
                    }

            bagalkote_slice = year_df[year_df[district_cols].sum(axis=1) == 0]
            if not bagalkote_slice.empty:
                row = bagalkote_slice.iloc[-1]
                district_data["bagalkote"] = {
                    "district_name": "Bagalkote",
                    "has_data": True,
                    "risk_class": int(row["risk_class"]),
                    "risk_label": str(row["risk_label"]),
                    "pm25_ground": float(round(row["pm25_ground"], 2)),
                    "pm10_ground": float(round(row["pm10_ground"], 2)),
                    "exposure_index": float(round(row["exposure_index"], 2)),
                    "temperature_C": float(round(row["temperature_C"], 2)),
                    "relative_humidity": float(round(row["relative_humidity"], 2)),
                    "year": int(row["year"]) if "year" in row else year
                }

            features = []
            for feat in geojson_base.get("features", []):
                raw_name = feat.get("properties", {}).get("DISTRICT", "")
                norm_name = normalize_name(raw_name)
                data_props = district_data.get(norm_name, {
                    "district_name": raw_name,
                    "has_data": False,
                    "risk_class": None,
                    "risk_label": "No Data",
                    "pm25_ground": None,
                    "pm10_ground": None,
                    "exposure_index": None,
                    "temperature_C": None,
                    "relative_humidity": None,
                    "year": year
                })
                features.append({
                    "type": "Feature",
                    "geometry": feat.get("geometry"),
                    "properties": data_props
                })

            return {
                "type": "FeatureCollection",
                "features": features
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error serving Karnataka GeoJSON map data: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


    # ------------------------------------------------------------------
    # Clinical Decision Support System Endpoint
    # ------------------------------------------------------------------

    @app.post("/cdss/assess", status_code=status.HTTP_200_OK)
    def assess_cdss_risk(
        request: CDSSAssessmentRequest,
        db: Session = Depends(get_db),
        current_user: Optional[User] = Depends(get_optional_current_user),
    ) -> Dict[str, Any]:
        """Evaluates environmental health-risk, persists assessment to PostgreSQL 'cdss_assessments', and links to user history if authenticated."""
        cdss = get_cdss_service()
        patient_dict = request.patient.model_dump() if hasattr(request.patient, 'model_dump') else request.patient.dict()
        environmental_dict = request.environmental.model_dump() if hasattr(request.environmental, 'model_dump') else request.environmental.dict()
        dt_now = datetime.now(timezone.utc)
        dl_pred_id = None

        # Check prediction_features specification
        if request.prediction_features is not None:
            pf = request.prediction_features
            if pf.dynamic is None or pf.static_num is None or pf.static_cat is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Incomplete prediction_features. Must supply dynamic, static_num, and static_cat blocks."
                )

            try:
                dyn_arr = np.array(pf.dynamic.data, dtype=np.float32)
                num_arr = np.array(pf.static_num.data, dtype=np.float32)
                cat_arr = np.array(pf.static_cat.data, dtype=np.int32)

                eng = get_inference_engine()
                dl_pred = eng.predict_single(dyn_arr, num_arr, cat_arr)

                fv_id, dev_id = resolve_feature_vector_source(
                    db,
                    explicit_fv_id=pf.feature_vector_id,
                    explicit_device_id=pf.device_id,
                )

                db_pred = DLPrediction(
                    feature_vector_id=fv_id,
                    device_id=dev_id,
                    risk_class=int(dl_pred["risk_class"]),
                    risk_label=str(dl_pred["risk_label"]),
                    probabilities_json=json.dumps(dl_pred.get("probabilities", [])),
                    applied_thresholds_json=json.dumps(dl_pred.get("applied_thresholds", [])),
                    model_version=str(dl_pred.get("model_version", "FINAL_OFFICIAL_DL_MODEL_v1.0")),
                    timestamp_utc=dt_now,
                )
                try:
                    db.add(db_pred)
                    db.commit()
                    db.refresh(db_pred)
                    dl_pred_id = db_pred.id
                except Exception as db_err:
                    db.rollback()
                    logger.warning(f"DLPrediction persistence error in CDSS endpoint: {db_err}")

            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"DL feature validation error: {str(e)}"
                )
            except Exception as e:
                logger.error(f"Inference error in CDSS endpoint: {e}", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Model inference failed: {str(e)}"
                )

            result = cdss.assess_patient(patient_dict, environmental_dict, model_prediction=dl_pred)
            response = {"mode": "dl_integrated"}
            response.update(result)

        else:
            result = cdss.assess_patient(patient_dict, environmental_dict)
            response = {"mode": "rule_based"}
            response.update(result)

        db_assessment = CDSSAssessment(
            dl_prediction_id=dl_pred_id,
            mode=response.get("mode", "rule_based"),
            age=request.patient.age,
            smoking_status=request.patient.smoking_status,
            respiratory_condition=request.patient.respiratory_condition,
            respiratory_severity=request.patient.respiratory_severity,
            skin_condition=request.patient.skin_condition,
            skin_severity=request.patient.skin_severity,
            latitude=request.patient.latitude,
            longitude=request.patient.longitude,
            pm25=request.environmental.pm25,
            pm10=request.environmental.pm10,
            no2=request.environmental.no2,
            o3=request.environmental.o3,
            so2=request.environmental.so2,
            co=request.environmental.co,
            rule_based_environmental_risk=str(result.get("rule_based_environmental_risk", result.get("environmental_risk", "Low"))),
            model_environmental_risk=str(result["model_environmental_risk"]) if "model_environmental_risk" in result else None,
            respiratory_environmental_risk=str(result.get("respiratory_environmental_risk", "Low")),
            skin_environmental_risk=str(result.get("skin_environmental_risk", "Low")),
            recommendations_json=json.dumps(result.get("recommendations", [])),
            contributors_json=json.dumps({
                "environmental": result.get("environmental_contributors", []),
                "respiratory": result.get("respiratory_contributors", []),
                "skin": result.get("skin_contributors", []),
                "patient_context": result.get("patient_context_factors", []),
            }),
            disclaimer=str(result.get("disclaimer", "")),
            timestamp_utc=dt_now,
        )

        try:
            db.add(db_assessment)
            db.commit()
            db.refresh(db_assessment)
            response["assessment_id"] = db_assessment.id

            if current_user:
                user_history = UserPredictionHistory(
                    user_id=current_user.id,
                    dl_prediction_id=dl_pred_id,
                    cdss_assessment_id=db_assessment.id,
                    latitude=request.patient.latitude,
                    longitude=request.patient.longitude,
                    risk_label=str(result.get("rule_based_environmental_risk", result.get("environmental_risk", "Low"))),
                    respiratory_risk=str(result.get("respiratory_environmental_risk", "Low")),
                    skin_risk=str(result.get("skin_environmental_risk", "Low")),
                )
                db.add(user_history)
                db.commit()

        except Exception as db_err:
            db.rollback()
            logger.warning(f"CDSSAssessment persistence error: {db_err}")

        return response

    # ------------------------------------------------------------------
    # User Authentication & Application Data Endpoints
    # ------------------------------------------------------------------

    @app.post("/api/auth/sync", status_code=status.HTTP_200_OK)
    def sync_user(
        payload: Optional[AuthSyncRequest] = None,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> Dict[str, Any]:
        """Synchronizes Supabase authenticated user with local PostgreSQL user domain.
        
        SECURITY GUARANTEE:
        - Requires a valid Supabase Bearer JWT.
        - Uses the verified JWT 'sub' claim (current_user.auth_user_id) as authoritative identity.
        - Ignores/rejects any client-supplied auth_user_id in request body to prevent user spoofing.
        """
        email = payload.email if (payload and payload.email) else current_user.email
        full_name = payload.full_name if (payload and payload.full_name) else current_user.full_name

        user = sync_local_user(
            db,
            auth_user_id=current_user.auth_user_id,
            email=email,
            full_name=full_name,
            role=current_user.role,
        )
        return {"status": "success", "user": user.to_dict()}

    @app.get("/api/me", status_code=status.HTTP_200_OK)
    def get_me(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
        """Returns details and role of the currently authenticated user."""
        return {
            "status": "success",
            "user": current_user.to_dict(),
            "profile": current_user.profile.to_dict() if current_user.profile else None,
            "health_profile": current_user.health_profile.to_dict() if current_user.health_profile else None,
            "preference": current_user.preference.to_dict() if current_user.preference else None,
        }

    @app.get("/api/profile", status_code=status.HTTP_200_OK)
    def get_user_profile(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
        """Reads profile attributes and CDSS health risk profile for authenticated user."""
        return {
            "user": current_user.to_dict(),
            "profile": current_user.profile.to_dict() if current_user.profile else None,
            "health_profile": current_user.health_profile.to_dict() if current_user.health_profile else None,
        }

    @app.put("/api/profile", status_code=status.HTTP_200_OK)
    def update_user_profile(
        payload: ProfileUpdateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> Dict[str, Any]:
        """Updates profile attributes and CDSS health profile for authenticated user."""
        if payload.full_name is not None:
            current_user.full_name = payload.full_name

        profile = current_user.profile
        if not profile:
            profile = UserProfile(user_id=current_user.id)
            db.add(profile)

        if payload.phone is not None:
            profile.phone = payload.phone
        if payload.preferred_location is not None:
            profile.preferred_location = payload.preferred_location

        health = current_user.health_profile
        if not health:
            health = HealthProfile(user_id=current_user.id)
            db.add(health)

        if payload.age is not None:
            health.age = payload.age
        if payload.smoking_status is not None:
            health.smoking_status = payload.smoking_status
        if payload.respiratory_condition is not None:
            health.respiratory_condition = payload.respiratory_condition
        if payload.respiratory_severity is not None:
            health.respiratory_severity = payload.respiratory_severity
        if payload.skin_condition is not None:
            health.skin_condition = payload.skin_condition
        if payload.skin_severity is not None:
            health.skin_severity = payload.skin_severity

        db.commit()
        db.refresh(current_user)

        return {
            "status": "success",
            "message": "User profile updated successfully",
            "user": current_user.to_dict(),
            "profile": profile.to_dict(),
            "health_profile": health.to_dict(),
        }

    @app.get("/api/user/predictions", status_code=status.HTTP_200_OK)
    def get_user_predictions(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> Dict[str, Any]:
        """Retrieves prediction & CDSS assessment history for authenticated user."""
        history = (
            db.query(UserPredictionHistory)
            .filter(UserPredictionHistory.user_id == current_user.id)
            .order_by(UserPredictionHistory.created_at.desc())
            .all()
        )
        return {
            "status": "success",
            "count": len(history),
            "predictions": [h.to_dict() for h in history],
        }

    @app.get("/api/user/locations", status_code=status.HTTP_200_OK)
    def get_user_locations(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> Dict[str, Any]:
        """Retrieves saved environmental monitoring locations for authenticated user."""
        locations = (
            db.query(UserLocation)
            .filter(UserLocation.user_id == current_user.id)
            .order_by(UserLocation.created_at.desc())
            .all()
        )
        return {
            "status": "success",
            "count": len(locations),
            "locations": [loc.to_dict() for loc in locations],
        }

    @app.post("/api/user/locations", status_code=status.HTTP_200_OK)
    def add_user_location(
        payload: UserLocationCreateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> Dict[str, Any]:
        """Saves a new environmental monitoring location for authenticated user."""
        if payload.is_default:
            db.query(UserLocation).filter(UserLocation.user_id == current_user.id).update({"is_default": False})

        loc = UserLocation(
            user_id=current_user.id,
            label=payload.label,
            latitude=payload.latitude,
            longitude=payload.longitude,
            is_default=payload.is_default,
        )
        db.add(loc)
        db.commit()
        db.refresh(loc)

        return {"status": "success", "location": loc.to_dict()}

    @app.delete("/api/user/locations/{location_id}", status_code=status.HTTP_200_OK)
    def delete_user_location(
        location_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> Dict[str, Any]:
        """Deletes a saved location belonging to authenticated user."""
        loc = (
            db.query(UserLocation)
            .filter(UserLocation.id == location_id, UserLocation.user_id == current_user.id)
            .first()
        )
        if not loc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Location not found or unauthorized")

        db.delete(loc)
        db.commit()
        return {"status": "success", "message": "Location deleted"}

    @app.get("/api/user/preferences", status_code=status.HTTP_200_OK)
    def get_user_preferences(
        current_user: User = Depends(get_current_user),
    ) -> Dict[str, Any]:
        """Retrieves user notification & alert threshold preferences."""
        pref = current_user.preference
        return {
            "status": "success",
            "preference": pref.to_dict() if pref else None,
        }

    @app.put("/api/user/preferences", status_code=status.HTTP_200_OK)
    def update_user_preferences(
        payload: UserPreferenceUpdateRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> Dict[str, Any]:
        """Updates user alert thresholds and notification preferences."""
        pref = current_user.preference
        if not pref:
            pref = UserPreference(user_id=current_user.id)
            db.add(pref)

        if payload.alert_threshold_pm25 is not None:
            pref.alert_threshold_pm25 = payload.alert_threshold_pm25
        if payload.notifications_enabled is not None:
            pref.notifications_enabled = payload.notifications_enabled
        if payload.dark_mode is not None:
            pref.dark_mode = payload.dark_mode

        db.commit()
        db.refresh(pref)
        return {"status": "success", "preference": pref.to_dict()}


else:
    class MockApp:
        def __init__(self) -> None:
            self.message = "FastAPI is not installed in the Python environment. Install with: pip install fastapi uvicorn"

    app = MockApp()
