"""Real-Time Environmental Data Fusion Module.

Enriches raw ESP32 PMS3003 particulate matter readings with real-time ambient
meteorology (temperature, relative humidity, wind speed, precipitation) and satellite/gas
retrievals (CO, NO2, O3, SO2, AOD) from Open-Meteo REST APIs.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional
import urllib.request
import json

logger = logging.getLogger(__name__)


class EnvironmentalDataFusion:
    """Fuses raw hardware sensor readings with real-time external environmental API data."""

    def __init__(
        self,
        default_lat: float = 12.9716,
        default_lon: float = 77.5946,
        timeout_sec: float = 3.0,
    ) -> None:
        """Initializes Environmental Data Fusion client.

        Args:
            default_lat: Default latitude for environmental lookup if omitted.
            default_lon: Default longitude for environmental lookup if omitted.
            timeout_sec: Network timeout for Open-Meteo REST API requests in seconds.
        """
        self.default_lat = default_lat
        self.default_lon = default_lon
        self.timeout_sec = timeout_sec

    def fetch_open_meteo_context(self, lat: float, lon: float) -> Dict[str, float]:
        """Queries Open-Meteo Weather & Air Quality REST APIs for live coordinates.

        Args:
            lat: Latitude [-90.0 to 90.0]
            lon: Longitude [-180.0 to 180.0]

        Returns:
            Dict[str, float]: Ambient weather and trace gas metrics.
        """
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
        )
        air_quality_url = (
            f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}"
            "&current=carbon_monoxide,nitrogen_dioxide,ozone,sulphur_dioxide,aerosol_optical_depth"
        )

        env_data = {}

        # 1. Fetch Weather API
        try:
            req = urllib.request.Request(weather_url, headers={"User-Agent": "AI-AQI-Data-Fusion/1.0"})
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    curr = data.get("current", {})
                    env_data["temperature_C"] = float(curr.get("temperature_2m", 25.0))
                    env_data["relative_humidity"] = float(curr.get("relative_humidity_2m", 60.0))
                    env_data["wind_speed_10m"] = float(curr.get("wind_speed_10m", 3.2))
                    env_data["precipitation_mm"] = float(curr.get("precipitation", 0.0))
        except Exception as e:
            logger.warning(f"Open-Meteo Weather API query skipped/offline: {e}")

        # 2. Fetch Air Quality API
        try:
            req = urllib.request.Request(air_quality_url, headers={"User-Agent": "AI-AQI-Data-Fusion/1.0"})
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    curr = data.get("current", {})
                    # Convert raw units if needed to match feature preprocessor expectations
                    co_raw = float(curr.get("carbon_monoxide", 350.0))  # ug/m3
                    env_data["CO_col"] = float(co_raw / 10000.0)  # scale proxy ~ 0.035
                    no2_raw = float(curr.get("nitrogen_dioxide", 25.0))
                    env_data["NO2_col"] = float(no2_raw / 200000.0) # scale proxy ~ 0.00012
                    o3_raw = float(curr.get("ozone", 45.0))
                    env_data["O3_col"] = float(o3_raw / 360.0)     # scale proxy ~ 0.125
                    env_data["so2_ground"] = float(curr.get("sulphur_dioxide", 12.5))
                    env_data["AOD_actual"] = float(curr.get("aerosol_optical_depth", 0.35))
        except Exception as e:
            logger.warning(f"Open-Meteo Air Quality API query skipped/offline: {e}")

        # Fill any missing metrics with documented regional station climatology if network was unavailable
        defaults = {
            "temperature_C": 26.5,
            "relative_humidity": 58.0,
            "wind_speed_10m": 3.4,
            "precipitation_mm": 0.0,
            "CO_col": 0.035,
            "NO2_col": 0.00012,
            "O3_col": 0.125,
            "so2_ground": 12.5,
            "AOD_actual": 0.35,
        }
        for k, v in defaults.items():
            if k not in env_data:
                env_data[k] = v

        return env_data

    def fuse_telemetry(
        self,
        raw_telemetry: Dict[str, Any],
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Combines raw ESP32 PM payload with environmental context into a complete telemetry object.

        Args:
            raw_telemetry: Dictionary containing device_id, pm1_ground, pm25_ground, pm10_ground, timestamp.
            latitude: Optional latitude coordinate for node location.
            longitude: Optional longitude coordinate for node location.

        Returns:
            Dict[str, Any]: Complete 11-variable telemetry payload matching LiveTelemetryPreprocessor contract.
        """
        lat = latitude if latitude is not None else self.default_lat
        lon = longitude if longitude is not None else self.default_lon

        # 1. Fetch ambient environmental context
        env_context = self.fetch_open_meteo_context(lat, lon)

        # 2. Extract timestamp components
        ts_str = raw_telemetry.get("timestamp")
        if ts_str:
            try:
                dt = datetime.fromisoformat(ts_str)
            except Exception:
                dt = datetime.now(timezone.utc)
        else:
            dt = datetime.now(timezone.utc)

        # 3. Assemble complete 11-variable telemetry object
        fused_payload = {
            "device_id": raw_telemetry.get("device_id", "ESP32_AQI_NODE"),
            "timestamp": dt.isoformat(),
            "pm1_ground": float(raw_telemetry.get("pm1_ground", 1.0)),
            "pm25_ground": float(raw_telemetry.get("pm25_ground", 2.0)),
            "pm10_ground": float(raw_telemetry.get("pm10_ground", 3.0)),
            "temperature_C": env_context["temperature_C"],
            "relative_humidity": env_context["relative_humidity"],
            "wind_speed_10m": env_context["wind_speed_10m"],
            "precipitation_mm": env_context["precipitation_mm"],
            "CO_col": env_context["CO_col"],
            "NO2_col": env_context["NO2_col"],
            "O3_col": env_context["O3_col"],
            "so2_ground": env_context["so2_ground"],
            "AOD_actual": env_context["AOD_actual"],
            "day_of_year": dt.timetuple().tm_yday,
            "month": dt.month,
            "hour": dt.hour,
            "provenance": "ESP32_PMS3003+OpenMeteo_Fusion",
        }

        return fused_payload
