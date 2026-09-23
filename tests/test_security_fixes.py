"""Targeted Automated Security Test Suite for Supabase ES256 JWKS Asymmetric Verification.

Verifies:
  ES256 / JWKS REQUIREMENTS:
    1. Valid ES256 Supabase JWT -> accepted (HTTP 200).
    2. Expired JWT -> HTTP 401.
    3. Invalid cryptographic signature -> HTTP 401.
    4. Malformed JWT -> HTTP 401.
    5. Wrong issuer -> HTTP 401.
    6. Wrong audience -> HTTP 401.
    7. Missing 'sub' claim -> HTTP 401.
    8. Unknown/invalid 'kid' -> HTTP 401 (JWKS key lookup fails closed).
    9. Missing SUPABASE_URL / JWKS unavailable -> authentication fails closed (HTTP 401).
   10. /api/auth/sync derives auth_user_id ONLY from verified JWT sub.
   11. Spoofed auth_user_id in request body cannot change identity.
   12. Existing authenticated endpoints resolve PostgreSQL User.
   13. Unauthenticated ESP32 telemetry endpoint POST /api/telemetry remains 100% operational.
"""

import datetime
import os
import sys
import unittest
import uuid
from unittest.mock import MagicMock, patch

import jwt
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from deployment.api import app
from deployment.database import Base, User, get_db

TEST_DB_URL = "sqlite:///./test_security_fixes.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

SUPABASE_TEST_URL = "https://test-project.supabase.co"
EXPECTED_ISSUER = f"{SUPABASE_TEST_URL}/auth/v1"


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


class MockSigningKey:
    def __init__(self, key_obj):
        self.key = key_obj


class TestES256SecurityFixes(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=test_engine)
        app.dependency_overrides[get_db] = override_get_db
        cls.client = TestClient(app)

        # Generate primary EC P-256 key pair for ES256 testing
        cls.private_key = ec.generate_private_key(ec.SECP256R1())
        cls.public_key = cls.private_key.public_key()
        cls.primary_kid = "test-ec-kid-001"

        # Generate secondary key pair for signature mismatch testing
        cls.bad_private_key = ec.generate_private_key(ec.SECP256R1())

    @classmethod
    def tearDownClass(cls):
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=test_engine)
        if os.path.exists("./test_security_fixes.db"):
            try:
                os.remove("./test_security_fixes.db")
            except OSError:
                pass

    def setUp(self):
        os.environ["SUPABASE_URL"] = SUPABASE_TEST_URL

    def create_es256_jwt(
        self,
        sub: str,
        priv_key=None,
        kid: str = "test-ec-kid-001",
        iss: str = EXPECTED_ISSUER,
        aud: str = "authenticated",
        exp_delta_seconds: int = 3600,
        email: str = "user@es256.test",
        include_sub: bool = True,
    ) -> str:
        key = priv_key or self.private_key
        now = datetime.datetime.now(datetime.timezone.utc)
        payload = {
            "email": email,
            "aud": aud,
            "iss": iss,
            "iat": int(now.timestamp()),
            "exp": int((now + datetime.timedelta(seconds=exp_delta_seconds)).timestamp()),
            "user_metadata": {"full_name": "ES256 Test User", "role": "patient"},
        }
        if include_sub:
            payload["sub"] = sub

        return jwt.encode(payload, key, algorithm="ES256", headers={"kid": kid})

    def mock_get_signing_key(self, token: str):
        """Mock JWKS key resolver returning public_key for valid kid."""
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if kid == self.primary_kid:
            return MockSigningKey(self.public_key)
        raise jwt.PyJWKClientError(f"No key found for kid '{kid}' in test JWKS")

    # ------------------------------------------------------------------
    # ES256 / JWKS SPECIFIC TESTS
    # ------------------------------------------------------------------

    def test_01_valid_es256_jwt_accepted(self):
        """1. Valid ES256 Supabase JWT -> accepted (HTTP 200)."""
        sub_uuid = str(uuid.uuid4())
        token = self.create_es256_jwt(sub_uuid)

        with patch("deployment.auth.PyJWKClient.get_signing_key_from_jwt", side_effect=self.mock_get_signing_key):
            res = self.client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["user"]["auth_user_id"], sub_uuid)

    def test_02_expired_jwt_returns_401(self):
        """2. Expired JWT -> HTTP 401."""
        sub_uuid = str(uuid.uuid4())
        token = self.create_es256_jwt(sub_uuid, exp_delta_seconds=-3600)

        with patch("deployment.auth.PyJWKClient.get_signing_key_from_jwt", side_effect=self.mock_get_signing_key):
            res = self.client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(res.status_code, 401)
            self.assertIn("expired", res.json()["detail"].lower())

    def test_03_invalid_signature_returns_401(self):
        """3. Invalid signature (signed with wrong EC key) -> HTTP 401."""
        sub_uuid = str(uuid.uuid4())
        bad_token = self.create_es256_jwt(sub_uuid, priv_key=self.bad_private_key, kid=self.primary_kid)

        with patch("deployment.auth.PyJWKClient.get_signing_key_from_jwt", side_effect=self.mock_get_signing_key):
            res = self.client.get("/api/me", headers={"Authorization": f"Bearer {bad_token}"})
            self.assertEqual(res.status_code, 401)
            self.assertIn("signature verification failed", res.json()["detail"].lower())

    def test_04_malformed_jwt_returns_401(self):
        """4. Malformed JWT -> HTTP 401."""
        res = self.client.get("/api/me", headers={"Authorization": "Bearer not.a.valid.jwt"})
        self.assertEqual(res.status_code, 401)

    def test_05_wrong_issuer_returns_401(self):
        """5. Wrong issuer -> HTTP 401."""
        sub_uuid = str(uuid.uuid4())
        token = self.create_es256_jwt(sub_uuid, iss="https://hacker.com/auth/v1")

        with patch("deployment.auth.PyJWKClient.get_signing_key_from_jwt", side_effect=self.mock_get_signing_key):
            res = self.client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(res.status_code, 401)
            self.assertIn("issuer", res.json()["detail"].lower())

    def test_06_wrong_audience_returns_401(self):
        """6. Wrong audience -> HTTP 401."""
        sub_uuid = str(uuid.uuid4())
        token = self.create_es256_jwt(sub_uuid, aud="untrusted_audience")

        with patch("deployment.auth.PyJWKClient.get_signing_key_from_jwt", side_effect=self.mock_get_signing_key):
            res = self.client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(res.status_code, 401)
            self.assertIn("audience", res.json()["detail"].lower())

    def test_07_missing_sub_returns_401(self):
        """7. Missing 'sub' claim -> HTTP 401."""
        token = self.create_es256_jwt("none", include_sub=False)

        with patch("deployment.auth.PyJWKClient.get_signing_key_from_jwt", side_effect=self.mock_get_signing_key):
            res = self.client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(res.status_code, 401)

    def test_08_unknown_kid_fails_closed(self):
        """8. Unknown/invalid 'kid' -> HTTP 401 (JWKS lookup fails closed)."""
        sub_uuid = str(uuid.uuid4())
        token = self.create_es256_jwt(sub_uuid, kid="unknown-kid-999")

        with patch("deployment.auth.PyJWKClient.get_signing_key_from_jwt", side_effect=self.mock_get_signing_key):
            res = self.client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
            self.assertEqual(res.status_code, 401)
            self.assertIn("unknown key id", res.json()["detail"].lower())

    def test_09_missing_supabase_url_fails_closed(self):
        """9. Missing SUPABASE_URL -> authentication fails closed."""
        sub_uuid = str(uuid.uuid4())
        token = self.create_es256_jwt(sub_uuid)

        os.environ["SUPABASE_URL"] = ""
        res = self.client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(res.status_code, 401)
        self.assertIn("configuration error", res.json()["detail"].lower())

    # ------------------------------------------------------------------
    # IDENTITY & SENSOR INTEGRATION TESTS
    # ------------------------------------------------------------------

    def test_10_auth_sync_uses_verified_jwt_sub(self):
        """10. /api/auth/sync derives auth_user_id ONLY from verified JWT sub."""
        sub_uuid = str(uuid.uuid4())
        token = self.create_es256_jwt(sub_uuid, email="verified@es256.com")

        with patch("deployment.auth.PyJWKClient.get_signing_key_from_jwt", side_effect=self.mock_get_signing_key):
            res = self.client.post(
                "/api/auth/sync",
                json={"full_name": "ES256 Verified User"},
                headers={"Authorization": f"Bearer {token}"},
            )
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["user"]["auth_user_id"], sub_uuid)
            self.assertEqual(res.json()["user"]["email"], "verified@es256.com")

    def test_11_spoofed_auth_user_id_rejected(self):
        """11. Spoofed auth_user_id in request body cannot change identity."""
        victim_uuid = str(uuid.uuid4())
        attacker_uuid = str(uuid.uuid4())
        attacker_token = self.create_es256_jwt(attacker_uuid, email="attacker@es256.com")

        with patch("deployment.auth.PyJWKClient.get_signing_key_from_jwt", side_effect=self.mock_get_signing_key):
            res = self.client.post(
                "/api/auth/sync",
                json={"auth_user_id": victim_uuid, "full_name": "Spoofed Victim"},
                headers={"Authorization": f"Bearer {attacker_token}"},
            )
            self.assertEqual(res.status_code, 200)
            # Identity MUST remain attacker_uuid from verified JWT sub
            self.assertEqual(res.json()["user"]["auth_user_id"], attacker_uuid)
            self.assertNotEqual(res.json()["user"]["auth_user_id"], victim_uuid)

    def test_12_authenticated_endpoints_resolve_correct_user(self):
        """12. Existing authenticated endpoints continue resolving the correct PostgreSQL User."""
        sub_uuid = str(uuid.uuid4())
        token = self.create_es256_jwt(sub_uuid, email="profile@es256.com")
        headers = {"Authorization": f"Bearer {token}"}

        with patch("deployment.auth.PyJWKClient.get_signing_key_from_jwt", side_effect=self.mock_get_signing_key):
            self.client.put("/api/profile", json={"phone": "+1-800-ES256"}, headers=headers)
            res = self.client.get("/api/profile", headers=headers)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["user"]["auth_user_id"], sub_uuid)
            self.assertEqual(res.json()["profile"]["phone"], "+1-800-ES256")

    def test_13_unauthenticated_sensor_telemetry_unaffected(self):
        """13. Existing unauthenticated ESP32 /api/telemetry behavior remains 100% operational."""
        payload = {
            "device_id": "ESP32_ES256_TEST_NODE",
            "pm1_ground": 3.5,
            "pm25_ground": 7.0,
            "pm10_ground": 14.0,
        }
        res = self.client.post("/api/telemetry", json=payload)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "received")
        self.assertEqual(res.json()["device_id"], "ESP32_ES256_TEST_NODE")


if __name__ == "__main__":
    unittest.main()
