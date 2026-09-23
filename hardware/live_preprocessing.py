"""Live Telemetry Preprocessor & Feature Alignment Module.

Transforms raw IoT telemetry dictionaries into 24-element model-aligned dynamic feature vectors,
computing cyclical time encodings, rolling metrics, and physical index proxies.
"""

import logging
from typing import Any, Dict

import numpy as np

logger = logging.getLogger(__name__)


class LiveTelemetryPreprocessor:
    """Preprocessor for converting raw sensor telemetry into model feature contracts."""

    def __init__(self) -> None:
        """Initializes rolling state tracking for lag features."""
        self.pm10_history = [45.0, 48.0, 42.0]

    def transform_telemetry_to_dynamic_vector(self, telemetry: Dict[str, Any], strict_live_mode: bool = False) -> np.ndarray:
        """Transforms a single raw hourly telemetry dictionary into a 24-element dynamic feature vector.

        Telemetry to Feature Mapping:
            1. pm10_ground -> raw sensor PM10 (µg/m³)
            2. CO_col -> raw sensor CO (mol/m²)
            3. AOD_actual -> raw sensor Aerosol Optical Depth
            4. O3_col -> raw sensor O3 (mol/m²)
            5. so2_ground -> raw sensor SO2 (µg/m³)
            6. relative_humidity -> raw sensor RH (%)
            7. NO2_col -> raw sensor NO2 (mol/m²)
            8. temperature_C -> raw sensor Temperature (°C)
            9. precipitation_mm -> raw sensor Precip (mm)
            10. wind_speed_10m -> raw sensor Wind Speed (m/s)
            11-14. Cyclical sine/cosine encodings for day_of_year and month
            15. pm10_roll_mean_24h -> 24h rolling average PM10
            16. pm10_roll_std_24h -> 24h rolling std PM10
            17. temp_humidity_index -> Heat Index proxy (T * RH / 100)
            18. wind_dispersion_index -> Pollution dispersion proxy (Wind / (PM10 + 1))
            19-21. pm10_lag_1h, pm10_lag_2h, pm10_lag_3h -> Historical PM10 lags
            22. co_no2_ratio -> Chemical ratio (CO / (NO2 + 1e-6))
            23. solar_diffuse_est -> Estimated diffuse radiation proxy
            24. boundary_layer_height_est -> Planetary boundary layer height proxy

        Args:
            telemetry: Raw telemetry payload from ArduinoCloudClient.

        Returns:
            np.ndarray: 1D array of shape (24,) containing dynamic features.
        """
        if strict_live_mode:
            required_vars = [
                "temperature_C", "relative_humidity", "wind_speed_10m",
                "precipitation_mm", "CO_col", "NO2_col", "O3_col",
                "so2_ground", "AOD_actual"
            ]
            for var in required_vars:
                if var not in telemetry or telemetry[var] is None:
                    raise ValueError(f"Missing live environmental variable: {var}")

        pm10 = float(telemetry.get("pm10_ground", 45.0))
        temp = float(telemetry.get("temperature_C", 25.0))
        rh = float(telemetry.get("relative_humidity", 60.0))
        wind = float(telemetry.get("wind_speed_10m", 3.0))
        precip = float(telemetry.get("precipitation_mm", 0.0))
        co = float(telemetry.get("CO_col", 0.035))
        no2 = float(telemetry.get("NO2_col", 0.00012))
        o3 = float(telemetry.get("O3_col", 0.125))
        so2 = float(telemetry.get("so2_ground", 12.5))
        aod = float(telemetry.get("AOD_actual", 0.35))

        doy = int(telemetry.get("day_of_year", 180))
        month = int(telemetry.get("month", 6))

        # Update lag history
        self.pm10_history.append(pm10)
        if len(self.pm10_history) > 24:
            self.pm10_history.pop(0)

        # Cyclical time features
        doy_sin = float(np.sin(2 * np.pi * doy / 365.25))
        doy_cos = float(np.cos(2 * np.pi * doy / 365.25))
        mon_sin = float(np.sin(2 * np.pi * month / 12.0))
        mon_cos = float(np.cos(2 * np.pi * month / 12.0))

        # Derived rolling & physical features
        pm10_mean = float(np.mean(self.pm10_history))
        pm10_std = float(np.std(self.pm10_history)) if len(self.pm10_history) > 1 else 0.0
        thi = float(temp * (rh / 100.0))
        wdi = float(wind / (pm10 + 1.0))

        lag1 = float(self.pm10_history[-2]) if len(self.pm10_history) >= 2 else pm10
        lag2 = float(self.pm10_history[-3]) if len(self.pm10_history) >= 3 else pm10
        lag3 = float(self.pm10_history[-4]) if len(self.pm10_history) >= 4 else pm10

        co_no2_ratio = float(co / (no2 + 1e-6))
        solar_est = float(max(0.0, 800.0 * np.sin(np.pi * (telemetry.get("hour", 12) - 6) / 12)))
        pblh_est = float(max(200.0, 1200.0 + 300.0 * temp - 50.0 * rh))

        feature_vector = np.array([
            pm10, co, aod, o3, so2, rh, no2, temp, precip, wind,
            doy_sin, doy_cos, mon_sin, mon_cos,
            pm10_mean, pm10_std, thi, wdi,
            lag1, lag2, lag3, co_no2_ratio, solar_est, pblh_est
        ], dtype=np.float32)

        return feature_vector
