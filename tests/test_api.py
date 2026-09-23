"""Automated Unit Tests for REST API Service (deployment/api.py).

Tests endpoints GET /health, POST /predict, GET /map_data, POST /cdss/assess,
POST /api/telemetry, and GET /api/telemetry/latest across rule_based, dl_integrated,
and telemetry persistence operating modes.
"""

import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

try:
    from fastapi.testclient import TestClient
    from deployment.api import app, FASTAPI_AVAILABLE, telemetry_store
    from deployment.database import Base, SensorTelemetry, get_db
except ImportError:
    FASTAPI_AVAILABLE = False

# Isolated in-memory test database using StaticPool so connection is shared
TEST_DATABASE_URL = "sqlite:///:memory:"
if FASTAPI_AVAILABLE:
    test_engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    """FastAPI dependency override providing an isolated test database session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@unittest.skipUnless(FASTAPI_AVAILABLE, "FastAPI is not installed in the environment.")
class TestAPIService(unittest.TestCase):
    """Unit tests for inference, health, map, and CDSS endpoints in deployment/api.py."""

    @classmethod
    def setUpClass(cls) -> None:
        """Create database tables in isolated in-memory SQLite engine for tests."""
        if FASTAPI_AVAILABLE:
            Base.metadata.create_all(bind=test_engine)

    def setUp(self) -> None:
        """Override database dependency and initialize TestClient."""
        if FASTAPI_AVAILABLE:
            app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

        # Standard valid patient input
        self.valid_patient = {
            "age": 45,
            "smoking_status": "never",
            "respiratory_condition": "asthma",
            "respiratory_severity": "moderate",
            "skin_condition": "none",
            "skin_severity": "none",
            "latitude": 12.9716,
            "longitude": 77.5946,
        }

        # Standard valid environmental input (Low pollution)
        self.valid_environmental = {
            "pm25": 15.0,
            "pm10": 25.0,
            "no2": 20.0,
            "o3": 30.0,
            "so2": 5.0,
            "co": 0.4,
        }

        # Standard valid prediction_features input
        self.valid_prediction_features = {
            "dynamic": {"data": [[45.0] * 24] * 7},
            "static_num": {"data": [12.97, 12.97, 1.5, 20.0, 4.0, 7500.0, 3.0, 77.59, 77.59, 900.0, 0.1, 0.8, 0.4, 250.0, 0.7, 10.0]},
            "static_cat": {"data": [0, 1, 0]},
        }

        # Mock engine instance
        self.mock_engine = MagicMock()
        self.mock_engine.model_version = "FINAL_OFFICIAL_DL_MODEL_v1.0"
        self.mock_engine.model_path = "/path/to/best_dl_model.keras"
        self.mock_engine.thresholds = [0.8, 1.0, 0.9, 0.75, 0.05]
        self.mock_engine.predict_single.return_value = {
            "sample_index": 0,
            "risk_class": 3,
            "risk_label": "Very Unhealthy",
            "probabilities": [0.02, 0.05, 0.13, 0.75, 0.05],
            "applied_thresholds": [0.8, 1.0, 0.9, 0.75, 0.05],
            "model_version": "FINAL_OFFICIAL_DL_MODEL_v1.0",
            "timestamp": "2026-08-13T15:00:00Z",
        }
        self.mock_engine.predict.return_value = [{
            "risk_class": 3,
            "risk_label": "Very Unhealthy",
            "probabilities": [0.02, 0.05, 0.13, 0.75, 0.05],
            "timestamp": "2026-08-13T15:00:00Z",
        }] * 30

    # 1. Test GET /health
    @patch("deployment.api.get_inference_engine")
    def test_health_endpoint(self, mock_get_engine: MagicMock) -> None:
        mock_get_engine.return_value = self.mock_engine
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["model_loaded"])

    # 2. Test existing POST /predict
    @patch("deployment.api.get_inference_engine")
    def test_predict_endpoint(self, mock_get_engine: MagicMock) -> None:
        mock_get_engine.return_value = self.mock_engine
        payload = self.valid_prediction_features
        response = self.client.post("/predict", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("prediction", data)
        self.assertEqual(data["prediction"]["risk_class"], 3)

    # 3. Test existing GET /map_data
    @patch("deployment.api.get_inference_engine")
    def test_map_data_endpoint(self, mock_get_engine: MagicMock) -> None:
        mock_get_engine.return_value = self.mock_engine
        response = self.client.get("/map_data")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["district_count"], 30)

    # 4. Test POST /cdss/assess in rule_based mode
    def test_cdss_assess_rule_based_mode(self) -> None:
        payload = {
            "patient": self.valid_patient,
            "environmental": self.valid_environmental,
        }
        response = self.client.post("/cdss/assess", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["mode"], "rule_based")
        self.assertEqual(data["environmental_risk"], "Low")
        self.assertEqual(data["respiratory_environmental_risk"], "Low")
        self.assertIn("recommendations", data)
        self.assertIn("disclaimer", data)
        self.assertNotIn("model_risk_class", data)

    # 5. Test POST /cdss/assess in dl_integrated mode
    @patch("deployment.api.get_inference_engine")
    def test_cdss_assess_dl_integrated_mode(self, mock_get_engine: MagicMock) -> None:
        mock_get_engine.return_value = self.mock_engine
        payload = {
            "patient": self.valid_patient,
            "environmental": self.valid_environmental,
            "prediction_features": self.valid_prediction_features,
        }
        response = self.client.post("/cdss/assess", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["mode"], "dl_integrated")
        self.assertEqual(data["model_risk_class"], 3)
        self.assertEqual(data["model_risk_label"], "Very Unhealthy")
        self.assertEqual(data["model_environmental_risk"], "High")
        self.assertEqual(data["rule_based_environmental_risk"], "Low")
        self.assertEqual(data["respiratory_environmental_risk"], "High")

    # 6. Test incomplete prediction_features -> HTTP 422
    def test_cdss_assess_incomplete_prediction_features_returns_422(self) -> None:
        payload = {
            "patient": self.valid_patient,
            "environmental": self.valid_environmental,
            "prediction_features": {
                "dynamic": self.valid_prediction_features["dynamic"],
            },
        }
        response = self.client.post("/cdss/assess", json=payload)
        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertIn("Incomplete prediction_features", data["detail"])

    # 7. Test invalid patient data -> HTTP 422
    def test_cdss_assess_invalid_patient_data_returns_422(self) -> None:
        invalid_patient = dict(self.valid_patient)
        invalid_patient["age"] = -10
        payload = {
            "patient": invalid_patient,
            "environmental": self.valid_environmental,
        }
        response = self.client.post("/cdss/assess", json=payload)
        self.assertEqual(response.status_code, 422)

    # 8. Test invalid environmental data -> HTTP 422
    def test_cdss_assess_invalid_environmental_data_returns_422(self) -> None:
        invalid_environmental = dict(self.valid_environmental)
        invalid_environmental["pm25"] = -5.0
        payload = {
            "patient": self.valid_patient,
            "environmental": invalid_environmental,
        }
        response = self.client.post("/cdss/assess", json=payload)
        self.assertEqual(response.status_code, 422)

    # 9. Test invalid DL tensor shape or validation error -> HTTP 422
    @patch("deployment.api.get_inference_engine")
    def test_cdss_assess_invalid_tensor_shape_returns_422(self, mock_get_engine: MagicMock) -> None:
        mock_engine = MagicMock()
        mock_engine.predict_single.side_effect = ValueError("X_dynamic must have shape (N, 7, 24), got (1, 3)")
        mock_get_engine.return_value = mock_engine

        payload = {
            "patient": self.valid_patient,
            "environmental": self.valid_environmental,
            "prediction_features": self.valid_prediction_features,
        }
        response = self.client.post("/cdss/assess", json=payload)
        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertIn("DL feature validation error", data["detail"])

    # 10. Test model vs rule disagreement visible
    @patch("deployment.api.get_inference_engine")
    def test_cdss_assess_model_vs_rule_disagreement_visible(self, mock_get_engine: MagicMock) -> None:
        mock_get_engine.return_value = self.mock_engine
        payload = {
            "patient": self.valid_patient,
            "environmental": self.valid_environmental,
            "prediction_features": self.valid_prediction_features,
        }
        response = self.client.post("/cdss/assess", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["mode"], "dl_integrated")
        self.assertEqual(data["rule_based_environmental_risk"], "Low")
        self.assertEqual(data["model_environmental_risk"], "High")
        self.assertEqual(data["model_risk_label"], "Very Unhealthy")
        self.assertIn("model_probabilities", data)


@unittest.skipUnless(FASTAPI_AVAILABLE, "FastAPI is not installed in the environment.")
class TestTelemetryAPI(unittest.TestCase):
    """Test suite for telemetry POST and GET endpoints with database persistence."""

    @classmethod
    def setUpClass(cls) -> None:
        """Initializes isolated in-memory test database tables and overrides get_db dependency."""
        Base.metadata.create_all(bind=test_engine)
        app.dependency_overrides[get_db] = override_get_db

    @classmethod
    def tearDownClass(cls) -> None:
        """Cleans up dependency overrides and test database tables."""
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=test_engine)

    def setUp(self) -> None:
        """Initializes TestClient and clears test database table & in-memory store before each test."""
        self.client = TestClient(app)
        telemetry_store.clear()
        db = TestingSessionLocal()
        try:
            db.query(SensorTelemetry).delete()
            db.commit()
        finally:
            db.close()

    def test_valid_telemetry_payload_and_persistence(self) -> None:
        """Tests ingestion and persistence of valid ESP32 PMS3003 telemetry payload."""
        payload = {
            "device_id": "ESP32_AQI_NODE_TEST_01",
            "pm10_ground": 14,
            "pm25_ground": 14,
            "pm1_ground": 7,
        }
        response = self.client.post("/api/telemetry", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["status"], "received")
        self.assertEqual(data["device_id"], "ESP32_AQI_NODE_TEST_01")
        self.assertIn("timestamp", data)
        self.assertEqual(len(telemetry_store), 1)

        # Verify record was stored in database
        db = TestingSessionLocal()
        try:
            records = db.query(SensorTelemetry).all()
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].device_id, "ESP32_AQI_NODE_TEST_01")
            self.assertEqual(records[0].pm1_ground, 7.0)
            self.assertEqual(records[0].pm25_ground, 14.0)
            self.assertEqual(records[0].pm10_ground, 14.0)
        finally:
            db.close()

    def test_get_latest_telemetry_endpoint(self) -> None:
        """Tests GET /api/telemetry/latest returns the most recent persisted record."""
        payload = {
            "device_id": "ESP32_AQI_NODE_LATEST_01",
            "pm10_ground": 16.0,
            "pm25_ground": 14.0,
            "pm1_ground": 7.0,
        }
        post_res = self.client.post("/api/telemetry", json=payload)
        self.assertEqual(post_res.status_code, 200)

        get_res = self.client.get("/api/telemetry/latest")
        self.assertEqual(get_res.status_code, 200)
        latest_data = get_res.json()
        record_data = latest_data.get("data", latest_data) or {}

        self.assertEqual(record_data["device_id"], "ESP32_AQI_NODE_LATEST_01")
        self.assertEqual(record_data["pm1_ground"], 7.0)
        self.assertEqual(record_data["pm25_ground"], 14.0)
        self.assertEqual(record_data["pm10_ground"], 16.0)
        self.assertIn("timestamp_utc", record_data)
        self.assertEqual(record_data["source"], "ESP32_PMS3003")

    def test_valid_telemetry_floats_and_integers(self) -> None:
        """Tests that both floating-point and integer PM values are accepted."""
        payload = {
            "device_id": "ESP32_AQI_NODE_02",
            "pm10_ground": 12.5,
            "pm25_ground": 8.0,
            "pm1_ground": 4,
        }
        response = self.client.post("/api/telemetry", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "received")
        self.assertEqual(data["device_id"], "ESP32_AQI_NODE_02")

    def test_missing_device_id(self) -> None:
        """Tests rejection when device_id field is omitted."""
        payload = {
            "pm10_ground": 7,
            "pm25_ground": 7,
            "pm1_ground": 3,
        }
        response = self.client.post("/api/telemetry", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_empty_device_id(self) -> None:
        """Tests rejection when device_id is empty or whitespace."""
        payload = {
            "device_id": "   ",
            "pm10_ground": 7,
            "pm25_ground": 7,
            "pm1_ground": 3,
        }
        response = self.client.post("/api/telemetry", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_missing_pm25(self) -> None:
        """Tests rejection when pm25_ground field is omitted."""
        payload = {
            "device_id": "ESP32_AQI_NODE",
            "pm10_ground": 7,
            "pm1_ground": 3,
        }
        response = self.client.post("/api/telemetry", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_missing_pm10(self) -> None:
        """Tests rejection when pm10_ground field is omitted."""
        payload = {
            "device_id": "ESP32_AQI_NODE",
            "pm25_ground": 7,
            "pm1_ground": 3,
        }
        response = self.client.post("/api/telemetry", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_missing_pm1(self) -> None:
        """Tests rejection when pm1_ground field is omitted."""
        payload = {
            "device_id": "ESP32_AQI_NODE",
            "pm10_ground": 7,
            "pm25_ground": 7,
        }
        response = self.client.post("/api/telemetry", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_negative_pm_value(self) -> None:
        """Tests rejection when PM values are negative."""
        payload_neg_pm10 = {
            "device_id": "ESP32_AQI_NODE",
            "pm10_ground": -5.0,
            "pm25_ground": 7.0,
            "pm1_ground": 3.0,
        }
        res1 = self.client.post("/api/telemetry", json=payload_neg_pm10)
        self.assertEqual(res1.status_code, 422)

        payload_neg_pm25 = {
            "device_id": "ESP32_AQI_NODE",
            "pm10_ground": 7.0,
            "pm25_ground": -1.0,
            "pm1_ground": 3.0,
        }
        res2 = self.client.post("/api/telemetry", json=payload_neg_pm25)
        self.assertEqual(res2.status_code, 422)

    def test_non_numeric_pm_value(self) -> None:
        """Tests rejection when PM values are non-numeric strings."""
        payload = {
            "device_id": "ESP32_AQI_NODE",
            "pm10_ground": "invalid_number",
            "pm25_ground": 7,
            "pm1_ground": 3,
        }
        response = self.client.post("/api/telemetry", json=payload)
        self.assertEqual(response.status_code, 422)

    def test_all_zero_pm_payload_rejection(self) -> None:
        """Tests rejection when pm1_ground, pm25_ground, and pm10_ground are all zero."""
        payload = {
            "device_id": "ESP32_AQI_NODE_ZERO",
            "pm10_ground": 0,
            "pm25_ground": 0,
            "pm1_ground": 0,
        }
        response = self.client.post("/api/telemetry", json=payload)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(len(telemetry_store), 0)

        # Verify not inserted into database
        db = TestingSessionLocal()
        try:
            records = db.query(SensorTelemetry).filter_by(device_id="ESP32_AQI_NODE_ZERO").all()
            self.assertEqual(len(records), 0)
        finally:
            db.close()

    def test_at_least_one_nonzero_pm_accepted(self) -> None:
        """Tests acceptance when at least one PM reading is non-zero."""
        payload = {
            "device_id": "ESP32_AQI_NODE_PARTIAL",
            "pm10_ground": 0,
            "pm25_ground": 5.0,
            "pm1_ground": 0,
        }
        response = self.client.post("/api/telemetry", json=payload)
        self.assertEqual(response.status_code, 200)

        db = TestingSessionLocal()
        try:
            records = db.query(SensorTelemetry).filter_by(device_id="ESP32_AQI_NODE_PARTIAL").all()
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].pm25_ground, 5.0)
        finally:
            db.close()

    def test_get_latest_telemetry_filters_existing_all_zero_records(self) -> None:
        """Tests GET /api/telemetry/latest ignores existing all-zero database records."""
        from datetime import datetime, timezone

        db = TestingSessionLocal()
        try:
            # Insert older valid record
            valid_record = SensorTelemetry(
                device_id="ESP32_VALID_NODE",
                pm1_ground=3.0,
                pm25_ground=7.0,
                pm10_ground=10.0,
                timestamp_utc=datetime.now(timezone.utc),
                source="ESP32_PMS3003",
            )
            db.add(valid_record)
            db.commit()

            # Insert newer all-zero invalid record
            zero_record = SensorTelemetry(
                device_id="ESP32_ZERO_NODE",
                pm1_ground=0.0,
                pm25_ground=0.0,
                pm10_ground=0.0,
                timestamp_utc=datetime.now(timezone.utc),
                source="ESP32_PMS3003",
            )
            db.add(zero_record)
            db.commit()
        finally:
            db.close()

        get_res = self.client.get("/api/telemetry/latest")
        self.assertEqual(get_res.status_code, 200)
        latest_data = get_res.json()
        record_data = latest_data.get("data", latest_data) or {}
        self.assertEqual(record_data["device_id"], "ESP32_VALID_NODE")
        self.assertEqual(record_data["pm25_ground"], 7.0)

    def test_telemetry_persistence_failure_raises_500(self) -> None:
        """Tests that database persistence failure rolls back, raises HTTP 500, and avoids in-memory storage."""
        mock_db = MagicMock()
        mock_db.add.side_effect = Exception("Simulated DB Write Error")

        app.dependency_overrides[get_db] = lambda: mock_db
        try:
            payload = {
                "device_id": "ESP32_AQI_NODE_FAIL",
                "pm10_ground": 10,
                "pm25_ground": 10,
                "pm1_ground": 5,
            }
            response = self.client.post("/api/telemetry", json=payload)
            self.assertEqual(response.status_code, 500)
            self.assertIn("Database write failure", response.json()["detail"])
            mock_db.rollback.assert_called_once()
            self.assertEqual(len(telemetry_store), 0)
        finally:
            app.dependency_overrides[get_db] = override_get_db


if __name__ == "__main__":
    unittest.main()
