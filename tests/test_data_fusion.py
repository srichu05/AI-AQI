"""Unit and Integration Tests for Real-Time Environmental Data Fusion & Live Inference Trace."""

import unittest
import numpy as np

from hardware.environmental_fusion import EnvironmentalDataFusion
from hardware.live_preprocessing import LiveTelemetryPreprocessor
from hardware.sensor_buffer import TemporalSensorBuffer, construct_static_vectors
from deep_learning.inference import AQIInferenceEngine
from cdss.dl_adapter import adapt_dl_prediction
from cdss import CDSSService


class TestEnvironmentalDataFusion(unittest.TestCase):
    """Test suite for environmental data fusion, strict preprocessor validation, and DL-CDSS trace."""

    @classmethod
    def setUpClass(cls) -> None:
        """Initializes heavy inference engine and CDSS service once for test suite."""
        cls.engine = AQIInferenceEngine()
        cls.cdss = CDSSService()

    def setUp(self) -> None:
        """Sets up test fusion client, preprocessor, and buffer."""
        self.fusion = EnvironmentalDataFusion(timeout_sec=0.5)
        self.preprocessor = LiveTelemetryPreprocessor()
        self.buffer = TemporalSensorBuffer(sequence_length=7, dynamic_dim=24)

        self.raw_esp32_payload = {
            "device_id": "ESP32_AQI_NODE_TEST",
            "pm1_ground": 12.0,
            "pm25_ground": 25.0,
            "pm10_ground": 45.0,
            "timestamp": "2026-08-19T12:00:00+00:00",
        }

    def test_strict_preprocessor_validation_fails_on_raw_esp32(self) -> None:
        """Confirms LiveTelemetryPreprocessor raises ValueError in strict live mode when missing weather/gases."""
        with self.assertRaises(ValueError) as ctx:
            self.preprocessor.transform_telemetry_to_dynamic_vector(
                self.raw_esp32_payload, strict_live_mode=True
            )
        self.assertIn("Missing live environmental variable", str(ctx.exception))

    def test_environmental_data_fusion_produces_complete_telemetry(self) -> None:
        """Tests fusing raw ESP32 readings with environmental context produces a complete telemetry dictionary."""
        fused = self.fusion.fuse_telemetry(self.raw_esp32_payload)

        # Check all required environmental fields are present
        required_fields = [
            "pm10_ground", "temperature_C", "relative_humidity", "wind_speed_10m",
            "precipitation_mm", "CO_col", "NO2_col", "O3_col", "so2_ground", "AOD_actual"
        ]
        for field in required_fields:
            self.assertIn(field, fused)
            self.assertIsNotNone(fused[field])

        # Test strict mode preprocessor transformation passes with fused telemetry
        vec = self.preprocessor.transform_telemetry_to_dynamic_vector(fused, strict_live_mode=True)
        self.assertEqual(len(vec), 24)
        self.assertTrue(np.all(np.isfinite(vec)))

    def test_end_to_end_real_esp32_trace_to_dl_and_cdss(self) -> None:
        """Executes full non-destructive trace: raw ESP32 -> Fusion -> Preprocessor -> Buffer -> DL -> CDSS."""
        # 1. Simulate 7 daily steps of ESP32 telemetry data fusion
        for step in range(7):
            raw_payload = {
                "device_id": "ESP32_AQI_NODE_TEST",
                "pm1_ground": 10.0 + step,
                "pm25_ground": 20.0 + step * 2,
                "pm10_ground": 40.0 + step * 3,
                "timestamp": f"2026-08-{13+step:02d}T12:00:00+00:00",
            }
            fused = self.fusion.fuse_telemetry(raw_payload)
            vec = self.preprocessor.transform_telemetry_to_dynamic_vector(fused, strict_live_mode=True)
            self.buffer.append_day_features(vec)

        self.assertTrue(self.buffer.is_full())

        # 2. Extract model-ready tensors
        dyn_tensor = self.buffer.get_dynamic_tensor()  # (1, 7, 24)
        num_tensor, cat_tensor = construct_static_vectors(district_id=3, land_use_id=1, urban_rural_id=0)

        self.assertEqual(dyn_tensor.shape, (1, 7, 24))
        self.assertEqual(num_tensor.shape, (1, 16))
        self.assertEqual(cat_tensor.shape, (1, 3))

        # 3. Execute DL inference
        dl_pred = self.engine.predict_single(dyn_tensor, num_tensor, cat_tensor)
        self.assertIn("risk_class", dl_pred)
        self.assertIn("probabilities", dl_pred)

        # 4. Adapt prediction for CDSS
        adapted = adapt_dl_prediction(dl_pred)
        self.assertIn("model_environmental_risk", adapted)

        # 5. Assess CDSS clinical risk
        patient_profile = {
            "age": 45,
            "smoking_status": "former",
            "respiratory_condition": "asthma",
            "respiratory_severity": "moderate",
            "skin_condition": "none",
            "skin_severity": "none",
            "latitude": 12.97,
            "longitude": 77.59,
        }
        env_readings = {
            "pm25": float(self.raw_esp32_payload["pm25_ground"]),
            "pm10": float(self.raw_esp32_payload["pm10_ground"]),
            "no2": 25.0,
            "o3": 45.0,
            "so2": 12.0,
            "co": 0.5,
        }

        cdss_result = self.cdss.assess_patient(patient_profile, env_readings, model_prediction=dl_pred)
        self.assertTrue("model_environmental_risk" in cdss_result or "environmental_risk" in cdss_result)
        self.assertIn("recommendations", cdss_result)
        self.assertGreater(len(cdss_result["recommendations"]), 0)


if __name__ == "__main__":
    unittest.main()
