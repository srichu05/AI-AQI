"""Automated Unit Tests for CDSS DL Adapter (cdss/dl_adapter.py).

Tests 5-class to 3-tier mappings, payload validation, malformed payload handling,
and end-to-end integration with CDSSService.
"""

import unittest
from cdss import CDSSService
from cdss.dl_adapter import adapt_dl_prediction


class TestDLAdapter(unittest.TestCase):
    """Unit tests for DL model prediction adapter."""

    def setUp(self) -> None:
        self.service = CDSSService()

    # 1. Test mappings for all 5 DL classes
    def test_dl_class_0_low_mapping(self) -> None:
        payload = {
            "risk_class": 0,
            "risk_label": "Low",
            "probabilities": [0.80, 0.10, 0.05, 0.03, 0.02],
            "model_version": "v1.0",
        }
        res = adapt_dl_prediction(payload)
        self.assertEqual(res["model_risk_class"], 0)
        self.assertEqual(res["model_risk_label"], "Low")
        self.assertEqual(res["model_environmental_risk"], "Low")

    def test_dl_class_1_moderate_mapping(self) -> None:
        payload = {
            "risk_class": 1,
            "risk_label": "Moderate",
            "probabilities": [0.10, 0.75, 0.10, 0.03, 0.02],
            "model_version": "v1.0",
        }
        res = adapt_dl_prediction(payload)
        self.assertEqual(res["model_risk_class"], 1)
        self.assertEqual(res["model_risk_label"], "Moderate")
        self.assertEqual(res["model_environmental_risk"], "Moderate")

    def test_dl_class_2_unhealthy_mapping(self) -> None:
        payload = {
            "risk_class": 2,
            "risk_label": "Unhealthy",
            "probabilities": [0.05, 0.15, 0.70, 0.05, 0.05],
            "model_version": "v1.0",
        }
        res = adapt_dl_prediction(payload)
        self.assertEqual(res["model_risk_class"], 2)
        self.assertEqual(res["model_risk_label"], "Unhealthy")
        self.assertEqual(res["model_environmental_risk"], "High")

    def test_dl_class_3_very_unhealthy_mapping(self) -> None:
        payload = {
            "risk_class": 3,
            "risk_label": "Very Unhealthy",
            "probabilities": [0.02, 0.08, 0.15, 0.70, 0.05],
            "model_version": "v1.0",
        }
        res = adapt_dl_prediction(payload)
        self.assertEqual(res["model_risk_class"], 3)
        self.assertEqual(res["model_risk_label"], "Very Unhealthy")
        self.assertEqual(res["model_environmental_risk"], "High")

    def test_dl_class_4_severe_mapping(self) -> None:
        payload = {
            "risk_class": 4,
            "risk_label": "Severe",
            "probabilities": [0.01, 0.04, 0.05, 0.10, 0.80],
            "model_version": "v1.0",
        }
        res = adapt_dl_prediction(payload)
        self.assertEqual(res["model_risk_class"], 4)
        self.assertEqual(res["model_risk_label"], "Severe")
        self.assertEqual(res["model_environmental_risk"], "High")

    # 2. Validation error tests
    def test_invalid_risk_class_out_of_bounds(self) -> None:
        payload = {"risk_class": 5, "risk_label": "Low", "probabilities": [0.2] * 5}
        with self.assertRaises(ValueError):
            adapt_dl_prediction(payload)

    def test_invalid_risk_class_negative(self) -> None:
        payload = {"risk_class": -1, "risk_label": "Low", "probabilities": [0.2] * 5}
        with self.assertRaises(ValueError):
            adapt_dl_prediction(payload)

    def test_missing_risk_class(self) -> None:
        payload = {"risk_label": "Low", "probabilities": [0.2] * 5}
        with self.assertRaises(ValueError):
            adapt_dl_prediction(payload)

    def test_malformed_probabilities_length(self) -> None:
        payload = {"risk_class": 1, "risk_label": "Moderate", "probabilities": [0.5, 0.5]}
        with self.assertRaises(ValueError):
            adapt_dl_prediction(payload)

    def test_inconsistent_risk_label(self) -> None:
        payload = {"risk_class": 1, "risk_label": "Severe", "probabilities": [0.2] * 5}
        with self.assertRaises(ValueError):
            adapt_dl_prediction(payload)

    # 3. End-to-End Integration with CDSSService
    def test_end_to_end_dl_cdss_integration(self) -> None:
        patient = {
            "age": 45,
            "smoking_status": "never",
            "respiratory_condition": "asthma",
            "respiratory_severity": "moderate",
            "skin_condition": "none",
            "skin_severity": "none",
            "latitude": 12.97,
            "longitude": 77.59,
        }
        env = {
            "pm25": 15.0,  # Rule-based env is Low
            "pm10": 25.0,
            "no2": 20.0,
            "o3": 30.0,
            "so2": 5.0,
            "co": 0.4,
        }
        # Simulated DL prediction payload (Class 3: Very Unhealthy)
        dl_pred = {
            "sample_index": 0,
            "risk_class": 3,
            "risk_label": "Very Unhealthy",
            "probabilities": [0.02, 0.08, 0.10, 0.75, 0.05],
            "applied_thresholds": [0.8, 1.0, 0.9, 0.75, 0.05],
            "model_version": "FINAL_OFFICIAL_DL_MODEL_v1.0",
        }

        result = self.service.assess_patient(patient, env, model_prediction=dl_pred)

        # Assert raw DL model output is strictly preserved
        self.assertEqual(result["model_risk_class"], 3)
        self.assertEqual(result["model_risk_label"], "Very Unhealthy")
        self.assertEqual(result["model_environmental_risk"], "High")

        # Assert rule-based environmental risk is also preserved separately
        self.assertEqual(result["rule_based_environmental_risk"], "Low")

        # Assert mapped model_environmental_risk ("High") drives respiratory environmental risk for asthma
        self.assertEqual(result["respiratory_environmental_risk"], "High")
        self.assertIn("disclaimer", result)


if __name__ == "__main__":
    unittest.main()
