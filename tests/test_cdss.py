"""Automated Unit Tests for AI-AQI CDSS Package.

Tests all required CDSS scenario cases, logical boundaries, validation errors,
and threshold consistency against the final output payload structure.
"""

import unittest
from pydantic import ValidationError

from cdss import (
    CDSSService,
    EnvironmentalInput,
    PatientContext,
    evaluate_environmental_risk,
    evaluate_respiratory_risk,
    evaluate_skin_risk,
    generate_recommendations,
)


class TestCDSSPackage(unittest.TestCase):
    """Unit tests for CDSS schemas, risk engines, recommendations, and service layer."""

    def setUp(self) -> None:
        self.service = CDSSService()

    # MANUAL TEST 1: Healthy + Low pollution
    def test_healthy_low_pollution(self) -> None:
        patient = {
            "age": 22,
            "smoking_status": "never",
            "respiratory_condition": "none",
            "respiratory_severity": "none",
            "skin_condition": "none",
            "skin_severity": "none",
            "latitude": 12.97,
            "longitude": 77.59,
        }
        env = {
            "pm25": 10.0,
            "pm10": 20.0,
            "no2": 15.0,
            "o3": 20.0,
            "so2": 5.0,
            "co": 0.3,
        }
        result = self.service.assess_patient(patient, env)

        self.assertEqual(result["environmental_risk"], "Low")
        self.assertIsInstance(result["environmental_risk_index"], int)
        self.assertLess(result["environmental_risk_index"], 40)
        self.assertEqual(result["respiratory_environmental_risk"], "Low")
        self.assertEqual(result["skin_environmental_risk"], "Low")
        self.assertEqual(len(result["environmental_contributors"]), 0)
        self.assertIn("disclaimer", result)

    # MANUAL TEST 2: Asthma + Moderate pollution
    def test_asthma_moderate_pollution(self) -> None:
        patient = {
            "age": 35,
            "smoking_status": "never",
            "respiratory_condition": "asthma",
            "respiratory_severity": "moderate",
            "skin_condition": "none",
            "skin_severity": "none",
            "latitude": 12.97,
            "longitude": 77.59,
        }
        env = {
            "pm25": 35.0,  # Moderate env pollution
            "pm10": 50.0,
            "no2": 25.0,
            "o3": 30.0,
            "so2": 5.0,
            "co": 0.5,
        }
        result = self.service.assess_patient(patient, env)

        self.assertEqual(result["environmental_risk"], "Moderate")
        self.assertEqual(result["respiratory_environmental_risk"], "High")
        self.assertIn("PM2.5", result["environmental_contributors"])
        self.assertTrue(any("asthma" in c.lower() for c in result["respiratory_contributors"]))

    # MANUAL TEST 3: Asthma + High pollution
    def test_asthma_high_pollution(self) -> None:
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
            "pm25": 75.0,  # High PM2.5 (>60)
            "pm10": 110.0,
            "no2": 85.0,   # High NO2 (>80)
            "o3": 40.0,
            "so2": 12.0,
            "co": 1.2,
        }
        result = self.service.assess_patient(patient, env)

        self.assertEqual(result["environmental_risk"], "High")
        self.assertEqual(result["environmental_risk_index"], 88)
        self.assertEqual(result["respiratory_environmental_risk"], "High")
        self.assertIn("PM2.5", result["environmental_contributors"])
        self.assertIn("NO2", result["environmental_contributors"])
        self.assertTrue(any("asthma" in c.lower() for c in result["patient_context_factors"]))

    # MANUAL TEST 4: Smoker + High pollution
    def test_smoker_high_pollution(self) -> None:
        patient = {
            "age": 40,
            "smoking_status": "current",
            "respiratory_condition": "none",
            "respiratory_severity": "none",
            "skin_condition": "none",
            "skin_severity": "none",
            "latitude": 12.97,
            "longitude": 77.59,
        }
        env = {
            "pm25": 70.0,
            "pm10": 100.0,
            "no2": 85.0,
            "o3": 30.0,
            "so2": 10.0,
            "co": 1.0,
        }
        result = self.service.assess_patient(patient, env)

        self.assertEqual(result["environmental_risk"], "High")
        self.assertEqual(result["respiratory_environmental_risk"], "High")
        self.assertTrue(any("smoking" in f.lower() for f in result["patient_context_factors"]))
        self.assertTrue(any("smoking" in r.lower() for r in result["recommendations"]))

    # MANUAL TEST 5: Asthma + Smoker + High pollution
    def test_asthma_smoker_high_pollution(self) -> None:
        patient = {
            "age": 50,
            "smoking_status": "current",
            "respiratory_condition": "asthma",
            "respiratory_severity": "severe",
            "skin_condition": "none",
            "skin_severity": "none",
            "latitude": 12.97,
            "longitude": 77.59,
        }
        env = {
            "pm25": 85.0,
            "pm10": 120.0,
            "no2": 90.0,
            "o3": 45.0,
            "so2": 12.0,
            "co": 1.4,
        }
        result = self.service.assess_patient(patient, env)

        self.assertEqual(result["environmental_risk"], "High")
        self.assertEqual(result["respiratory_environmental_risk"], "High")
        self.assertTrue(any("asthma" in f.lower() for f in result["patient_context_factors"]))
        self.assertTrue(any("smoking" in f.lower() for f in result["patient_context_factors"]))

    # MANUAL TEST 6: Skin condition + High PM2.5/O3
    def test_skin_condition_high_pm25_o3(self) -> None:
        patient = {
            "age": 28,
            "smoking_status": "never",
            "respiratory_condition": "none",
            "respiratory_severity": "none",
            "skin_condition": "dermatitis",
            "skin_severity": "moderate",
            "latitude": 12.97,
            "longitude": 77.59,
        }
        env = {
            "pm25": 65.0,
            "pm10": 80.0,
            "no2": 30.0,
            "o3": 110.0,  # High Ozone (>100)
            "so2": 4.0,
            "co": 0.5,
        }
        result = self.service.assess_patient(patient, env)

        self.assertEqual(result["skin_environmental_risk"], "High")
        self.assertIn("PM2.5", result["skin_contributors"])
        self.assertIn("O3", result["skin_contributors"])
        self.assertTrue(any("skin exposure" in r.lower() for r in result["recommendations"]))

    # TEST 7: Low env risk + condition does not trigger High risk
    def test_low_env_risk_with_condition_not_high(self) -> None:
        patient = {
            "age": 30,
            "smoking_status": "never",
            "respiratory_condition": "asthma",
            "respiratory_severity": "moderate",
            "skin_condition": "none",
            "skin_severity": "none",
            "latitude": 12.97,
            "longitude": 77.59,
        }
        env = {
            "pm25": 10.0,
            "pm10": 20.0,
            "no2": 15.0,
            "o3": 20.0,
            "so2": 5.0,
            "co": 0.3,
        }
        result = self.service.assess_patient(patient, env)

        self.assertEqual(result["environmental_risk"], "Low")
        self.assertNotEqual(result["respiratory_environmental_risk"], "High")

    # TEST 8: Age modifier does not independently trigger High risk
    def test_age_modifier_no_independent_high_risk(self) -> None:
        patient = {
            "age": 75,
            "smoking_status": "never",
            "respiratory_condition": "none",
            "respiratory_severity": "none",
            "skin_condition": "none",
            "skin_severity": "none",
            "latitude": 12.97,
            "longitude": 77.59,
        }
        env = {
            "pm25": 10.0,
            "pm10": 20.0,
            "no2": 15.0,
            "o3": 20.0,
            "so2": 5.0,
            "co": 0.3,
        }
        result = self.service.assess_patient(patient, env)

        self.assertEqual(result["environmental_risk"], "Low")
        self.assertEqual(result["respiratory_environmental_risk"], "Low")

    # TEST 9: Invalid patient input validation
    def test_invalid_patient_fields(self) -> None:
        with self.assertRaises(ValidationError):
            PatientContext(
                age=-5,
                smoking_status="never",
                respiratory_condition="none",
                respiratory_severity="none",
                skin_condition="none",
                skin_severity="none",
                latitude=12.97,
                longitude=77.59,
            )

    # TEST 10: Invalid negative pollution values
    def test_invalid_negative_pollution(self) -> None:
        with self.assertRaises(ValidationError):
            EnvironmentalInput(
                pm25=-10.0,
                pm10=20.0,
                no2=15.0,
                o3=20.0,
                so2=5.0,
                co=0.3,
            )

    # TEST 11: Exact boundary threshold testing (PM2.5 = 25, 60; NO2 = 40, 80)
    def test_exact_boundary_thresholds(self) -> None:
        e_low = EnvironmentalInput(pm25=24.9, pm10=30.0, no2=39.9, o3=20.0, so2=5.0, co=0.4)
        self.assertEqual(evaluate_environmental_risk(e_low)["environmental_risk"], "Low")

        e_mod_25 = EnvironmentalInput(pm25=25.0, pm10=30.0, no2=10.0, o3=20.0, so2=5.0, co=0.4)
        self.assertEqual(evaluate_environmental_risk(e_mod_25)["environmental_risk"], "Moderate")

        e_mod_60 = EnvironmentalInput(pm25=60.0, pm10=80.0, no2=10.0, o3=20.0, so2=5.0, co=0.4)
        self.assertEqual(evaluate_environmental_risk(e_mod_60)["environmental_risk"], "Moderate")

        e_high_601 = EnvironmentalInput(pm25=60.1, pm10=80.0, no2=10.0, o3=20.0, so2=5.0, co=0.4)
        self.assertEqual(evaluate_environmental_risk(e_high_601)["environmental_risk"], "High")


if __name__ == "__main__":
    unittest.main()
