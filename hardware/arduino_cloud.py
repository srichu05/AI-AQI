"""Arduino IoT Cloud Client & Live Telemetry Connector.

Fetches or simulates live environmental sensor telemetry from Arduino Cloud API endpoints.
Raw sensor measurements include PM10, PM2.5, Temperature, Relative Humidity,
Wind Speed, Precipitation, and Satellite/Colular trace gases (CO, NO2, O3, SO2).
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional

import numpy as np

logger = logging.getLogger(__name__)


class ArduinoCloudClient:
    """Client interface for retrieving live IoT sensor telemetry from Arduino Cloud."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        device_id: Optional[str] = None,
        simulate_if_offline: bool = True,
    ) -> None:
        """Initializes Arduino Cloud telemetry client.

        Args:
            api_key: Secret API key for Arduino Cloud REST endpoints.
            device_id: Unique hardware identifier for the environmental sensor node.
            simulate_if_offline: If True, generates physics-bounded synthetic telemetry when offline.
        """
        self.api_key = api_key
        self.device_id = device_id or "ARDUINO_AQI_NODE_01"
        self.simulate_if_offline = simulate_if_offline

    def fetch_live_telemetry(self) -> Dict[str, Any]:
        """Fetches latest hourly sensor telemetry reading.

        Raw Sensor Telemetry Contract:
            - pm10_ground (µg/m³)
            - pm25_ground (µg/m³, reference/monitoring)
            - temperature_C (°C)
            - relative_humidity (%)
            - wind_speed_10m (m/s)
            - precipitation_mm (mm)
            - CO_col (mol/m²)
            - NO2_col (mol/m²)
            - O3_col (mol/m²)
            - so2_ground (µg/m³)
            - AOD_actual (unitless)

        Returns:
            Dict[str, Any]: Raw telemetry payload with ISO UTC timestamp.
        """
        if self.api_key and not self.simulate_if_offline:
            # Placeholder for live HTTP GET to Arduino IoT Cloud REST API
            logger.info(f"Querying Arduino IoT Cloud API for device {self.device_id}...")
            raise NotImplementedError("Live REST connection requires valid Arduino Cloud credentials.")

        # Physics-bounded synthetic telemetry for testing and simulation
        now = datetime.now(timezone.utc)
        hour = now.hour
        doy = now.timetuple().tm_yday

        # Diurnal PM10 variation (higher in morning/evening rush hours)
        base_pm10 = 45.0 + 20.0 * np.sin((hour - 8) * np.pi / 12) + np.random.normal(0, 5)
        base_pm10 = max(5.0, base_pm10)

        telemetry = {
            "device_id": self.device_id,
            "timestamp": now.isoformat(),
            "pm10_ground": float(base_pm10),
            "pm25_ground": float(base_pm10 * 0.55 + np.random.normal(0, 2)),
            "temperature_C": float(24.0 + 6.0 * np.sin((hour - 14) * np.pi / 12)),
            "relative_humidity": float(65.0 - 20.0 * np.sin((hour - 14) * np.pi / 12)),
            "wind_speed_10m": float(max(0.5, 3.2 + np.random.normal(0, 0.8))),
            "precipitation_mm": float(max(0.0, np.random.choice([0.0, 0.0, 0.0, 1.2]))),
            "CO_col": float(0.035 + 0.005 * np.random.normal(0, 1)),
            "NO2_col": float(0.00012 + 0.00002 * np.random.normal(0, 1)),
            "O3_col": float(0.125 + 0.01 * np.random.normal(0, 1)),
            "so2_ground": float(12.5 + np.random.normal(0, 2)),
            "AOD_actual": float(0.35 + 0.05 * np.random.normal(0, 1)),
            "day_of_year": doy,
            "hour": hour,
            "month": now.month,
        }

        return telemetry
