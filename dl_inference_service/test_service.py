"""Comprehensive Test Suite for AI-AQI Standalone Hugging Face Inference Service.

Tests:
1. Lifespan model startup and memory loading
2. GET /health response and contract metadata
3. POST /predict with frontend nested payload
4. POST /predict with direct flat array payload
5. POST /predict with batch payload (N > 1)
6. Calibrated decision rule verification (argmax(P_k / tau_k))
7. Error handling: invalid tensor shapes (400)
8. Error handling: categorical vocabulary out-of-bounds (400)
9. Error handling: NaN / Inf non-finite values (400)
10. Error handling: batch size mismatch (400)
"""

import sys
from pathlib import Path
import numpy as np

# Ensure service directory is on path
SERVICE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SERVICE_DIR))

from fastapi.testclient import TestClient
from app import app, FROZEN_THRESHOLDS, CLASS_LABELS


def run_all_tests():
    print("=" * 70)
    print("RUNNING VERIFICATION SUITE FOR HF INFERENCE SERVICE")
    print("=" * 70)

    # Use TestClient with lifespan context manager enabled
    with TestClient(app) as client:
        # -------------------------------------------------------------
        # Test 1: GET /health
        # -------------------------------------------------------------
        print("\n[TEST 1] GET /health")
        res = client.get("/health")
        assert res.status_code == 200, f"Health check failed: {res.status_code} {res.text}"
        health_data = res.json()
        assert health_data["status"] == "healthy", f"Expected healthy status, got {health_data['status']}"
        assert health_data["model_loaded"] is True, "Expected model_loaded == True"
        assert health_data["thresholds"] == FROZEN_THRESHOLDS, "Thresholds mismatch"
        assert len(health_data["class_labels"]) == 5, "Expected 5 class labels"
        print(f"  PASS: Health check returned 200 OK. Model loaded: {health_data['model_loaded']}")
        print(f"        Thresholds: {health_data['thresholds']}")

        # -------------------------------------------------------------
        # Test 2: POST /predict (Frontend Nested Payload)
        # -------------------------------------------------------------
        print("\n[TEST 2] POST /predict (Frontend Nested Format)")
        dyn_sample = np.ones((7, 24), dtype=np.float32) * 0.25
        num_sample = np.ones((16,), dtype=np.float32) * 0.5
        cat_sample = [0, 1, 0]  # district 0, land_use 1, urban 0

        nested_payload = {
            "dynamic": {"data": dyn_sample.tolist()},
            "static_num": {"data": num_sample.tolist()},
            "static_cat": {"data": cat_sample},
            "feature_vector_id": 101,
            "device_id": "TEST_NODE_01",
        }

        res = client.post("/predict", json=nested_payload)
        assert res.status_code == 200, f"Predict failed: {res.status_code} {res.text}"
        data = res.json()
        assert data["success"] is True, "Expected success == True"
        assert "prediction" in data, "Expected prediction object in response"

        pred = data["prediction"]
        probs = pred["probabilities"]
        assert len(probs) == 5, f"Expected 5 class probabilities, got {len(probs)}"
        prob_sum = sum(probs)
        assert abs(prob_sum - 1.0) < 1e-4, f"Probabilities must sum to 1.0, got {prob_sum}"

        # Verify argmax threshold calculation
        adj_scores = [p / t for p, t in zip(probs, FROZEN_THRESHOLDS)]
        expected_class = int(np.argmax(adj_scores))
        assert pred["risk_class"] == expected_class, f"Expected risk_class {expected_class}, got {pred['risk_class']}"
        assert pred["risk_label"] == CLASS_LABELS[expected_class], f"Risk label mismatch"
        assert pred["feature_vector_id"] == 101
        assert pred["device_id"] == "TEST_NODE_01"
        print(f"  PASS: Nested prediction returned 200 OK.")
        print(f"        Predicted Class: {pred['risk_class']} ({pred['risk_label']})")
        print(f"        Probabilities  : {[round(p, 4) for p in probs]}")
        print(f"        Probability Sum: {prob_sum:.6f}")

        # -------------------------------------------------------------
        # Test 3: POST /predict (Flat Array Payload)
        # -------------------------------------------------------------
        print("\n[TEST 3] POST /predict (Direct Flat Array Format)")
        flat_payload = {
            "dynamic": dyn_sample.tolist(),
            "static_num": num_sample.tolist(),
            "static_cat": cat_sample,
        }
        res = client.post("/predict", json=flat_payload)
        assert res.status_code == 200, f"Flat predict failed: {res.status_code} {res.text}"
        flat_data = res.json()
        assert flat_data["success"] is True
        assert flat_data["prediction"]["risk_class"] == expected_class
        print(f"  PASS: Flat array prediction returned 200 OK. Matches nested prediction.")

        # -------------------------------------------------------------
        # Test 4: POST /predict (Batch Sample N=2)
        # -------------------------------------------------------------
        print("\n[TEST 4] POST /predict (Batch Payload N=2)")
        dyn_batch = np.ones((2, 7, 24), dtype=np.float32) * 0.3
        num_batch = np.ones((2, 16), dtype=np.float32) * 0.4
        cat_batch = [[5, 2, 1], [15, 3, 2]]

        batch_payload = {
            "dynamic": dyn_batch.tolist(),
            "static_num": num_batch.tolist(),
            "static_cat": cat_batch,
        }
        res = client.post("/predict", json=batch_payload)
        assert res.status_code == 200, f"Batch predict failed: {res.status_code} {res.text}"
        batch_data = res.json()
        assert batch_data["success"] is True
        assert len(batch_data["predictions"]) == 2, f"Expected 2 predictions, got {len(batch_data['predictions'])}"
        print(f"  PASS: Batch prediction returned 200 OK. Received 2 prediction records.")

        # -------------------------------------------------------------
        # Test 5: Error Handling - Shape Mismatch (Dynamic not 7x24)
        # -------------------------------------------------------------
        print("\n[TEST 5] Error Handling: Shape Mismatch (Dynamic shape 5x24)")
        bad_shape_payload = {
            "dynamic": (np.ones((5, 24), dtype=np.float32)).tolist(),  # Invalid: 5 timesteps instead of 7
            "static_num": num_sample.tolist(),
            "static_cat": cat_sample,
        }
        res = client.post("/predict", json=bad_shape_payload)
        assert res.status_code == 400, f"Expected 400 Bad Request, got {res.status_code}"
        print(f"  PASS: Properly caught shape mismatch with HTTP 400: {res.json()['detail']}")

        # -------------------------------------------------------------
        # Test 6: Error Handling - Out of Bounds district_id (35 > 29)
        # -------------------------------------------------------------
        print("\n[TEST 6] Error Handling: Out of Bounds district_id (35)")
        bad_cat_payload = {
            "dynamic": dyn_sample.tolist(),
            "static_num": num_sample.tolist(),
            "static_cat": [35, 1, 0],  # Invalid district_id 35
        }
        res = client.post("/predict", json=bad_cat_payload)
        assert res.status_code == 400, f"Expected 400 Bad Request, got {res.status_code}"
        print(f"  PASS: Properly caught district_id out-of-bounds with HTTP 400: {res.json()['detail']}")

        # -------------------------------------------------------------
        # Test 7: Error Handling - Out of Bounds land_use_id (8 > 5)
        # -------------------------------------------------------------
        print("\n[TEST 7] Error Handling: Out of Bounds land_use_id (8)")
        bad_land_payload = {
            "dynamic": dyn_sample.tolist(),
            "static_num": num_sample.tolist(),
            "static_cat": [10, 8, 0],  # Invalid land_use_id 8
        }
        res = client.post("/predict", json=bad_land_payload)
        assert res.status_code == 400, f"Expected 400 Bad Request, got {res.status_code}"
        print(f"  PASS: Properly caught land_use_id out-of-bounds with HTTP 400: {res.json()['detail']}")

        # -------------------------------------------------------------
        # Test 8: Error Handling - Non-finite values (NaN / Inf)
        # -------------------------------------------------------------
        print("\n[TEST 8] Error Handling: Non-finite values (NaN in dynamic)")
        import json
        nan_dyn = np.ones((7, 24), dtype=np.float32)
        nan_dyn[0, 0] = np.nan
        bad_nan_payload = {
            "dynamic": nan_dyn.tolist(),
            "static_num": num_sample.tolist(),
            "static_cat": cat_sample,
        }
        raw_body = json.dumps(bad_nan_payload).encode("utf-8")
        res = client.post("/predict", content=raw_body, headers={"Content-Type": "application/json"})
        assert res.status_code in [400, 422], f"Expected 400 or 422, got {res.status_code}"
        print(f"  PASS: Properly rejected non-finite NaN input with HTTP {res.status_code}: {res.json()['detail']}")

        # -------------------------------------------------------------
        # Test 9: Error Handling - Batch Size Mismatch
        # -------------------------------------------------------------
        print("\n[TEST 9] Error Handling: Batch Size Mismatch (2 dynamic vs 1 static_num)")
        mismatch_payload = {
            "dynamic": (np.ones((2, 7, 24), dtype=np.float32)).tolist(),
            "static_num": num_sample.tolist(),  # Only 1 sample
            "static_cat": cat_sample,
        }
        res = client.post("/predict", json=mismatch_payload)
        assert res.status_code == 400, f"Expected 400 Bad Request, got {res.status_code}"
        print(f"  PASS: Properly caught batch size mismatch with HTTP 400: {res.json()['detail']}")

    print("\n" + "=" * 70)
    print("ALL 9 TEST SUITES COMPLETED AND PASSED WITH 100% SUCCESS!")
    print("=" * 70)


if __name__ == "__main__":
    run_all_tests()
