"""Unit tests for live hardware sensor integration and temporal buffer assembly."""

import unittest
import numpy as np

from hardware.arduino_cloud import ArduinoCloudClient
from hardware.live_preprocessing import LiveTelemetryPreprocessor
from hardware.sensor_buffer import TemporalSensorBuffer, construct_static_vectors


class TestHardwareIntegration(unittest.TestCase):
    """Test suite for hardware telemetry and sensor buffer modules."""

    def setUp(self) -> None:
        """Sets up test client, preprocessor, and buffer."""
        self.client = ArduinoCloudClient(simulate_if_offline=True)
        self.preprocessor = LiveTelemetryPreprocessor()
        self.buffer = TemporalSensorBuffer(sequence_length=7, dynamic_dim=24)

    def test_arduino_cloud_telemetry_fetch(self) -> None:
        """Tests live/synthetic sensor telemetry payload fetching."""
        telemetry = self.client.fetch_live_telemetry()
        self.assertIn("pm10_ground", telemetry)
        self.assertIn("temperature_C", telemetry)
        self.assertGreater(telemetry["pm10_ground"], 0.0)

    def test_live_preprocessing_transformation(self) -> None:
        """Tests transformation of raw telemetry payload into 24 dynamic features."""
        telemetry = self.client.fetch_live_telemetry()
        vec = self.preprocessor.transform_telemetry_to_dynamic_vector(telemetry)
        self.assertEqual(len(vec), 24)
        self.assertTrue(np.all(np.isfinite(vec)))

    def test_sensor_buffer_sliding_window(self) -> None:
        """Tests rolling buffer append and dynamic (1, 7, 24) tensor construction."""
        for _ in range(7):
            telemetry = self.client.fetch_live_telemetry()
            vec = self.preprocessor.transform_telemetry_to_dynamic_vector(telemetry)
            self.buffer.append_day_features(vec)

        self.assertTrue(self.buffer.is_full())
        tensor = self.buffer.get_dynamic_tensor()
        self.assertEqual(tensor.shape, (1, 7, 24))

    def test_static_vector_construction(self) -> None:
        """Tests static numerical (1, 16) and static categorical (1, 3) vector builder."""
        num, cat = construct_static_vectors(district_id=3, land_use_id=1, urban_rural_id=0)
        self.assertEqual(num.shape, (1, 16))
        self.assertEqual(cat.shape, (1, 3))
        self.assertEqual(cat[0, 0], 3)


if __name__ == "__main__":
    unittest.main()
