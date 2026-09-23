"""Database configuration, SQLAlchemy models, and session management for AI-AQI telemetry persistence & user application data storage.

Target Database: ai_aqi
Existing Tables: sensor_telemetry, feature_vectors, dl_predictions, cdss_assessments
User Schema Tables: users, user_profiles, health_profiles, user_prediction_history, user_locations, user_preferences, audit_logs
"""

from datetime import datetime, timezone
import logging
import os
import uuid
from typing import Generator, Optional
from urllib.parse import urlparse

from dotenv import load_dotenv
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, create_engine, text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

logger = logging.getLogger(__name__)

# Load environment variables from .env file if present
load_dotenv()

DEFAULT_DATABASE_URL = "sqlite:///./ai_aqi_telemetry.db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

# Normalize postgres:// scheme to postgresql:// for SQLAlchemy 1.4+
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLAlchemy Base model definition
Base = declarative_base()


# ------------------------------------------------------------------
# 1. Existing Sensor & AI Model Persistence Tables (PRESERVED 100%)
# ------------------------------------------------------------------

class SensorTelemetry(Base):
    """SQLAlchemy model for raw ESP32 PMS3003 sensor telemetry persistence."""

    __tablename__ = "sensor_telemetry"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String(100), nullable=False, index=True)
    timestamp_utc = Column(DateTime(timezone=True), nullable=False, index=True)
    pm1_ground = Column(Float, nullable=False)
    pm25_ground = Column(Float, nullable=False)
    pm10_ground = Column(Float, nullable=False)
    source = Column(String(50), nullable=False, default="ESP32_PMS3003")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        """Converts database model instance to dictionary representation."""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "pm1_ground": self.pm1_ground,
            "pm25_ground": self.pm25_ground,
            "pm10_ground": self.pm10_ground,
            "timestamp_utc": self.timestamp_utc.isoformat() if self.timestamp_utc else None,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class FeatureVector(Base):
    """SQLAlchemy model for engineered 24-feature dynamic model vector persistence."""

    __tablename__ = "feature_vectors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    device_id = Column(String(100), nullable=False, index=True)
    timestamp_utc = Column(DateTime(timezone=True), nullable=False, index=True)
    pm10_ground = Column(Float, nullable=False)
    temperature_c = Column(Float, nullable=False)
    relative_humidity = Column(Float, nullable=False)
    wind_speed_10m = Column(Float, nullable=False)
    co_col = Column(Float, nullable=False)
    no2_col = Column(Float, nullable=False)
    o3_col = Column(Float, nullable=False)
    so2_ground = Column(Float, nullable=False)
    aod_actual = Column(Float, nullable=False)
    feature_vector_json = Column(String(2000), nullable=False)
    provenance = Column(String(100), nullable=False, default="ESP32_PMS3003+OpenMeteo_Fusion")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        """Converts feature vector instance to dictionary representation."""
        import json
        return {
            "id": self.id,
            "device_id": self.device_id,
            "timestamp_utc": self.timestamp_utc.isoformat() if self.timestamp_utc else None,
            "pm10_ground": self.pm10_ground,
            "temperature_c": self.temperature_c,
            "relative_humidity": self.relative_humidity,
            "wind_speed_10m": self.wind_speed_10m,
            "co_col": self.co_col,
            "no2_col": self.no2_col,
            "o3_col": self.o3_col,
            "so2_ground": self.so2_ground,
            "aod_actual": self.aod_actual,
            "feature_vector": json.loads(self.feature_vector_json) if self.feature_vector_json else [],
            "provenance": self.provenance,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DLPrediction(Base):
    """SQLAlchemy model for deep learning AQI model prediction persistence."""

    __tablename__ = "dl_predictions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    feature_vector_id = Column(Integer, ForeignKey("feature_vectors.id"), nullable=True, index=True)
    device_id = Column(String(100), nullable=True, index=True)
    risk_class = Column(Integer, nullable=False)
    risk_label = Column(String(50), nullable=False)
    probabilities_json = Column(String(500), nullable=False)
    applied_thresholds_json = Column(String(500), nullable=False)
    model_version = Column(String(100), nullable=False, default="FINAL_OFFICIAL_DL_MODEL_v1.0")
    timestamp_utc = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        """Converts prediction instance to dictionary representation."""
        import json
        return {
            "id": self.id,
            "feature_vector_id": self.feature_vector_id,
            "device_id": self.device_id,
            "risk_class": self.risk_class,
            "risk_label": self.risk_label,
            "probabilities": json.loads(self.probabilities_json) if self.probabilities_json else [],
            "applied_thresholds": json.loads(self.applied_thresholds_json) if self.applied_thresholds_json else [],
            "model_version": self.model_version,
            "timestamp_utc": self.timestamp_utc.isoformat() if self.timestamp_utc else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CDSSAssessment(Base):
    """SQLAlchemy model for clinical decision support system (CDSS) risk assessment persistence."""

    __tablename__ = "cdss_assessments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    dl_prediction_id = Column(Integer, ForeignKey("dl_predictions.id"), nullable=True, index=True)
    mode = Column(String(50), nullable=False, default="rule_based")
    age = Column(Integer, nullable=False)
    smoking_status = Column(String(50), nullable=False)
    respiratory_condition = Column(String(50), nullable=False)
    respiratory_severity = Column(String(50), nullable=False)
    skin_condition = Column(String(50), nullable=False)
    skin_severity = Column(String(50), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    pm25 = Column(Float, nullable=False)
    pm10 = Column(Float, nullable=False)
    no2 = Column(Float, nullable=False)
    o3 = Column(Float, nullable=False)
    so2 = Column(Float, nullable=False)
    co = Column(Float, nullable=False)
    rule_based_environmental_risk = Column(String(50), nullable=False)
    model_environmental_risk = Column(String(50), nullable=True)
    respiratory_environmental_risk = Column(String(50), nullable=False)
    skin_environmental_risk = Column(String(50), nullable=False)
    recommendations_json = Column(String(2000), nullable=False)
    contributors_json = Column(String(2000), nullable=False)
    disclaimer = Column(String(500), nullable=False)
    timestamp_utc = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        """Converts CDSS assessment instance to dictionary representation."""
        import json
        return {
            "id": self.id,
            "dl_prediction_id": self.dl_prediction_id,
            "mode": self.mode,
            "patient": {
                "age": self.age,
                "smoking_status": self.smoking_status,
                "respiratory_condition": self.respiratory_condition,
                "respiratory_severity": self.respiratory_severity,
                "skin_condition": self.skin_condition,
                "skin_severity": self.skin_severity,
                "latitude": self.latitude,
                "longitude": self.longitude,
            },
            "environmental": {
                "pm25": self.pm25,
                "pm10": self.pm10,
                "no2": self.no2,
                "o3": self.o3,
                "so2": self.so2,
                "co": self.co,
            },
            "rule_based_environmental_risk": self.rule_based_environmental_risk,
            "model_environmental_risk": self.model_environmental_risk,
            "respiratory_environmental_risk": self.respiratory_environmental_risk,
            "skin_environmental_risk": self.skin_environmental_risk,
            "recommendations": json.loads(self.recommendations_json) if self.recommendations_json else [],
            "contributors": json.loads(self.contributors_json) if self.contributors_json else {},
            "disclaimer": self.disclaimer,
            "timestamp_utc": self.timestamp_utc.isoformat() if self.timestamp_utc else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ------------------------------------------------------------------
# 2. Local Application & User Domain Models (Supabase Auth Mapping)
# ------------------------------------------------------------------

class User(Base):
    """Local application user table mapped to Supabase authenticated user UUID (auth_user_id).
    
    NO PASSWORDS ARE STORED HERE. Password hashing and auth identity are owned by Supabase Auth.
    """

    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    auth_user_id = Column(String(36), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    role = Column(String(50), nullable=False, default="patient")
    tenant_id = Column(String(36), nullable=True, index=True)  # Future multi-tenancy readiness
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    profile = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    health_profile = relationship("HealthProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    predictions = relationship("UserPredictionHistory", back_populates="user", cascade="all, delete-orphan")
    locations = relationship("UserLocation", back_populates="user", cascade="all, delete-orphan")
    preference = relationship("UserPreference", back_populates="user", uselist=False, cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "auth_user_id": self.auth_user_id,
            "email": self.email,
            "role": self.role,
            "tenant_id": self.tenant_id,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class UserProfile(Base):
    """User profile attributes table."""

    __tablename__ = "user_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    preferred_location = Column(String(255), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="profile")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "phone": self.phone,
            "preferred_location": self.preferred_location,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class HealthProfile(Base):
    """User clinical health risk profile context (used by CDSS)."""

    __tablename__ = "health_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, index=True)
    age = Column(Integer, nullable=True)
    smoking_status = Column(String(50), nullable=True, default="never")
    respiratory_condition = Column(String(50), nullable=True, default="none")
    respiratory_severity = Column(String(50), nullable=True, default="none")
    skin_condition = Column(String(50), nullable=True, default="none")
    skin_severity = Column(String(50), nullable=True, default="none")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="health_profile")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "age": self.age,
            "smoking_status": self.smoking_status,
            "respiratory_condition": self.respiratory_condition,
            "respiratory_severity": self.respiratory_severity,
            "skin_condition": self.skin_condition,
            "skin_severity": self.skin_severity,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class UserPredictionHistory(Base):
    """User-specific AI-AQI risk prediction & CDSS assessment log."""

    __tablename__ = "user_prediction_history"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    dl_prediction_id = Column(Integer, ForeignKey("dl_predictions.id"), nullable=True, index=True)
    cdss_assessment_id = Column(Integer, ForeignKey("cdss_assessments.id"), nullable=True, index=True)
    location_label = Column(String(255), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    risk_label = Column(String(50), nullable=True)
    respiratory_risk = Column(String(50), nullable=True)
    skin_risk = Column(String(50), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="predictions")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "dl_prediction_id": self.dl_prediction_id,
            "cdss_assessment_id": self.cdss_assessment_id,
            "location_label": self.location_label,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "risk_label": self.risk_label,
            "respiratory_risk": self.respiratory_risk,
            "skin_risk": self.skin_risk,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class UserLocation(Base):
    """User-specific saved environmental monitoring locations."""

    __tablename__ = "user_locations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    label = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    is_default = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="locations")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "label": self.label,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class UserPreference(Base):
    """User preferences and environmental alert threshold settings."""

    __tablename__ = "user_preferences"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), unique=True, nullable=False, index=True)
    alert_threshold_pm25 = Column(Float, nullable=False, default=35.0)
    notifications_enabled = Column(Boolean, nullable=False, default=True)
    dark_mode = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="preference")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "alert_threshold_pm25": self.alert_threshold_pm25,
            "notifications_enabled": self.notifications_enabled,
            "dark_mode": self.dark_mode,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AuditLog(Base):
    """Application security and audit trail log."""

    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    actor_user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(255), nullable=True)
    ip_address = Column(String(50), nullable=True)
    timestamp_utc = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "actor_user_id": self.actor_user_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "ip_address": self.ip_address,
            "timestamp_utc": self.timestamp_utc.isoformat() if self.timestamp_utc else None,
        }


# ------------------------------------------------------------------
# 3. Database Engine & Helpers
# ------------------------------------------------------------------

def get_engine(db_url: Optional[str] = None):
    """Creates a SQLAlchemy engine for the specified database URL, raising an error if PostgreSQL connection fails."""
    url = db_url or os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    connect_args = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
        return create_engine(url, connect_args=connect_args, pool_pre_ping=True)

    parsed = urlparse(url)
    db_name = parsed.path.lstrip("/") or "ai_aqi"
    host = parsed.hostname or "localhost"
    port = parsed.port or 5432

    try:
        test_engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True)
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info(
            f"Database engine: PostgreSQL | Database name: {db_name} | Host: {host} | Port: {port} | Status: CONNECTED"
        )
        return test_engine
    except Exception as e:
        logger.error(
            f"Database engine: PostgreSQL | Database: {db_name} | Host: {host} | Port: {port} | Status: CONNECTION FAILED - {e}"
        )
        raise RuntimeError(
            f"Could not connect to target PostgreSQL database '{db_name}' on {host}:{port}. Error: {e}"
        ) from e


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



def get_db() -> Generator:
    """FastAPI dependency yielding a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_database_exists(db_url: str) -> None:
    """Ensures the target PostgreSQL database exists without affecting existing databases."""
    if not db_url.startswith("postgresql"):
        return

    parsed = urlparse(db_url)
    target_db = parsed.path.lstrip("/")

    if not target_db or target_db == "postgres":
        return

    maintenance_url = db_url.replace(f"/{target_db}", "/postgres", 1)

    try:
        temp_engine = create_engine(maintenance_url, isolation_level="AUTOCOMMIT")
        with temp_engine.connect() as conn:
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
                {"dbname": target_db},
            )
            exists = result.scalar() is not None
            if not exists:
                logger.info(f"Database '{target_db}' does not exist. Creating database '{target_db}'...")
                conn.execute(text(f'CREATE DATABASE "{target_db}"'))
                logger.info(f"Database '{target_db}' created successfully.")
        temp_engine.dispose()
    except Exception as e:
        logger.warning(f"Database existence check note: {e}")


def init_db(db_url: Optional[str] = None) -> None:
    """Initializes and verifies all database schema tables."""
    target_url = db_url or os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    if target_url.startswith("postgres://"):
        target_url = target_url.replace("postgres://", "postgresql://", 1)

    ensure_database_exists(target_url)

    target_engine = get_engine(target_url)
    Base.metadata.create_all(bind=target_engine)
    logger.info("AI-AQI Database schema (Telemetry, AI Predictions, CDSS & User Auth Schema) verified successfully.")
