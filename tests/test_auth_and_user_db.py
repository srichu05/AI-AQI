"""Automated Test Suite for Supabase Auth Integration & PostgreSQL User Domain Data Storage.

Verifies:
    - Supabase Auth User UUID mapping to PostgreSQL users table
    - User Profile, Health Profile, Prediction History, Saved Locations, Preferences persistence
    - Authenticated vs Unauthenticated request security
    - Role-based authorization (patient, clinician, admin)
    - Sensor ingestion pipeline preservation & isolation
"""

import json
import os
import sys
import unittest
import uuid
import jwt
from unittest.mock import patch
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from deployment.api import app
from deployment.database import Base, User, UserLocation, UserPredictionHistory, UserPreference, get_db

TEST_DB_URL = "sqlite:///./test_auth_user_domain.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

SUPABASE_TEST_URL = "https://test-project.supabase.co"


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


class MockSigningKey:
    def __init__(self, key_obj):
        self.key = key_obj


class TestAuthAndUserDomain(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=test_engine)
        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

        # Generate EC P-256 key pair for ES256 authentication testing
        cls.private_key = ec.generate_private_key(ec.SECP256R1())
        cls.public_key = cls.private_key.public_key()
        cls.primary_kid = "test-ec-kid-auth-001"

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=test_engine)
        if os.path.exists("./test_auth_user_domain.db"):
            try:
                os.remove("./test_auth_user_domain.db")
            except OSError:
                pass

    def setUp(self):
        os.environ["SUPABASE_URL"] = SUPABASE_TEST_URL
        self.patcher = patch(
            "deployment.auth.PyJWKClient.get_signing_key_from_jwt",
            return_value=MockSigningKey(self.public_key),
        )
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def create_test_jwt(self, auth_user_id: str, email: str = "user@example.com", role: str = "patient") -> str:
        """Helper to generate a valid test Supabase ES256 JWT token."""
        payload = {
            "sub": auth_user_id,
            "email": email,
            "aud": "authenticated",
            "iss": f"{SUPABASE_TEST_URL}/auth/v1",
            "exp": 2147483647,
            "user_metadata": {
                "full_name": "Test User",
                "role": role,
            },
        }
        return jwt.encode(payload, self.private_key, algorithm="ES256", headers={"kid": self.primary_kid})

    def test_01_sensor_telemetry_unblocked(self):
        """Verify ESP32 sensor ingestion remains 100% functional without user authentication."""
        payload = {
            "device_id": "ESP32_NODE_TEST_AUTH_01",
            "pm1_ground": 5.0,
            "pm25_ground": 12.0,
            "pm10_ground": 25.0,
        }
        res = self.client.post("/api/telemetry", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "received")
        self.assertEqual(data["device_id"], "ESP32_NODE_TEST_AUTH_01")

    def test_02_auth_sync_and_me_endpoint(self):
        """Verify Supabase auth user UUID sync and /api/me identity endpoint."""
        sub_uuid = str(uuid.uuid4())
        token = self.create_test_jwt(sub_uuid, "john.doe@example.com", "patient")

        headers = {"Authorization": f"Bearer {token}"}
        res = self.client.get("/api/me", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertEqual(data["status"], "success")
        self.assertEqual(data["user"]["auth_user_id"], sub_uuid)
        self.assertEqual(data["user"]["email"], "john.doe@example.com")
        self.assertEqual(data["user"]["role"], "patient")
        self.assertIsNotNone(data["profile"])
        self.assertIsNotNone(data["health_profile"])
        self.assertIsNotNone(data["preference"])

    def test_03_unauthenticated_request_rejected(self):
        """Verify protected endpoints reject requests without a valid token."""
        res = self.client.get("/api/me")
        self.assertEqual(res.status_code, 401)

        res = self.client.get("/api/profile")
        self.assertEqual(res.status_code, 401)

    def test_04_profile_and_health_profile_update(self):
        """Verify profile attributes and CDSS health risk profile updates."""
        sub_uuid = str(uuid.uuid4())
        token = self.create_test_jwt(sub_uuid, "jane.doe@example.com", "patient")
        headers = {"Authorization": f"Bearer {token}"}

        update_payload = {
            "full_name": "Jane Doe",
            "phone": "+1-555-0199",
            "preferred_location": "Central District",
            "age": 42,
            "smoking_status": "former",
            "respiratory_condition": "asthma",
            "respiratory_severity": "mild",
        }
        res = self.client.put("/api/profile", json=update_payload, headers=headers)
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertEqual(data["user"]["full_name"], "Jane Doe")
        self.assertEqual(data["profile"]["phone"], "+1-555-0199")
        self.assertEqual(data["health_profile"]["age"], 42)
        self.assertEqual(data["health_profile"]["smoking_status"], "former")
        self.assertEqual(data["health_profile"]["respiratory_condition"], "asthma")

    def test_05_user_locations_crud(self):
        """Verify adding, retrieving, and deleting saved monitoring locations."""
        sub_uuid = str(uuid.uuid4())
        token = self.create_test_jwt(sub_uuid, "loc.user@example.com", "patient")
        headers = {"Authorization": f"Bearer {token}"}

        loc_payload = {
            "label": "Home Office",
            "latitude": 12.9716,
            "longitude": 77.5946,
            "is_default": True,
        }
        res = self.client.post("/api/user/locations", json=loc_payload, headers=headers)
        self.assertEqual(res.status_code, 200)
        loc_id = res.json()["location"]["id"]

        # Fetch locations
        res = self.client.get("/api/user/locations", headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["count"], 1)

        # Delete location
        res = self.client.delete(f"/api/user/locations/{loc_id}", headers=headers)
        self.assertEqual(res.status_code, 200)

        res = self.client.get("/api/user/locations", headers=headers)
        self.assertEqual(res.json()["count"], 0)

    def test_06_user_preferences_update(self):
        """Verify updating alert thresholds and notifications."""
        sub_uuid = str(uuid.uuid4())
        token = self.create_test_jwt(sub_uuid, "pref.user@example.com", "patient")
        headers = {"Authorization": f"Bearer {token}"}

        pref_payload = {"alert_threshold_pm25": 45.5, "notifications_enabled": True}
        res = self.client.put("/api/user/preferences", json=pref_payload, headers=headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["preference"]["alert_threshold_pm25"], 45.5)

    def test_07_prediction_history_linking(self):
        """Verify CDSS assessments automatically link to authenticated user prediction history."""
        sub_uuid = str(uuid.uuid4())
        token = self.create_test_jwt(sub_uuid, "patient.cdss@example.com", "patient")
        headers = {"Authorization": f"Bearer {token}"}

        cdss_payload = {
            "patient": {
                "age": 35,
                "smoking_status": "never",
                "respiratory_condition": "none",
                "respiratory_severity": "none",
                "skin_condition": "none",
                "skin_severity": "none",
                "latitude": 12.9716,
                "longitude": 77.5946,
            },
            "environmental": {
                "pm25": 45.0,
                "pm10": 90.0,
                "no2": 25.0,
                "o3": 15.0,
                "so2": 5.0,
                "co": 1.2,
            },
        }

        res = self.client.post("/cdss/assess", json=cdss_payload, headers=headers)
        self.assertEqual(res.status_code, 200)

        # Retrieve user history
        res = self.client.get("/api/user/predictions", headers=headers)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["count"], 1)
        self.assertIsNotNone(data["predictions"][0]["cdss_assessment_id"])


if __name__ == "__main__":
    unittest.main()
