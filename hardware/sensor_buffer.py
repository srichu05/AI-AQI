"""Rolling Temporal Sensor Buffer for Real-Time Model Input Assembly.

Maintains a 7-day rolling window of 24 dynamic hourly environmental features,
outputting formatted (1, 7, 24) dynamic tensors alongside (1, 16) static numerical
and (1, 3) static categorical input vectors.
"""

from collections import deque
import logging
from typing import Dict, List, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)

# Canonical 24 dynamic features expected per daily timestep
DYNAMIC_FEATURE_NAMES = [
    "pm10_ground", "CO_col", "AOD_actual", "O3_col", "so2_ground",
    "relative_humidity", "NO2_col", "temperature_C", "precipitation_mm", "wind_speed_10m",
    "day_of_year_sin", "day_of_year_cos", "month_sin", "month_cos",
    "pm10_roll_mean_24h", "pm10_roll_std_24h", "temp_humidity_index",
    "wind_dispersion_index", "pm10_lag_1h", "pm10_lag_2h", "pm10_lag_3h",
    "co_no2_ratio", "solar_diffuse_est", "boundary_layer_height_est"
]

STATIC_NUM_FEATURE_NAMES = [
    "shp_centroid_lat", "lat", "distance_to_nearest_major_highway_km",
    "green_cover_pct", "road_density_km_km2", "pop_density",
    "distance_to_nearest_industrial_area_km", "shp_centroid_lon", "lon",
    "elevation_m", "industrial_zone_density", "highway_proximity_score",
    "vegetation_index_proxy", "coastal_distance_km", "urban_density_index", "terrain_roughness"
]

STATIC_CAT_FEATURE_NAMES = ["district_id", "land_use_id", "urban_rural_id"]


class TemporalSensorBuffer:
    """Rolling temporal sliding-window buffer for live model inference."""

    def __init__(self, sequence_length: int = 7, dynamic_dim: int = 24) -> None:
        """Initializes 7-day rolling buffer.

        Args:
            sequence_length: Number of temporal timesteps (days). Defaults to 7.
            dynamic_dim: Number of dynamic features per timestep. Defaults to 24.
        """
        self.sequence_length = sequence_length
        self.dynamic_dim = dynamic_dim
        self.buffer: deque = deque(maxlen=sequence_length)

    def append_day_features(self, day_feature_vector: np.ndarray) -> None:
        """Appends a 24-element daily dynamic feature vector to the rolling buffer.

        Args:
            day_feature_vector: 1D array of shape (24,) or 2D array of shape (1, 24).
        """
        vec = np.asarray(day_feature_vector, dtype=np.float32).flatten()
        if len(vec) != self.dynamic_dim:
            raise ValueError(f"Day feature vector must have length {self.dynamic_dim}, got {len(vec)}")
        self.buffer.append(vec)

    def is_full(self) -> bool:
        """Returns True if the buffer contains all 7 required temporal steps."""
        return len(self.buffer) == self.sequence_length

    def get_dynamic_tensor(self) -> np.ndarray:
        """Constructs model-ready dynamic tensor of shape (1, 7, 24).

        If buffer is partially filled, backfills earlier timesteps by padding
        with the earliest available reading.

        Returns:
            np.ndarray: 3D dynamic array of shape (1, 7, 24).
        """
        if len(self.buffer) == 0:
            raise ValueError("Buffer is completely empty. Append telemetry readings first.")

        history = list(self.buffer)
        while len(history) < self.sequence_length:
            history.insert(0, history[0])  # Backfill padding

        tensor = np.array(history, dtype=np.float32)  # Shape (7, 24)
        return np.expand_dims(tensor, axis=0)  # Shape (1, 7, 24)


def construct_static_vectors(
    district_id: int = 0,
    land_use_id: int = 0,
    urban_rural_id: int = 0,
    custom_static_num: Optional[Dict[str, float]] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    """Constructs model-ready static numerical (1, 16) and static categorical (1, 3) vectors.

    Args:
        district_id: Categorical district identifier [0-29].
        land_use_id: Categorical land-use identifier [0-5].
        urban_rural_id: Categorical urban/rural identifier [0-2].
        custom_static_num: Optional dictionary overriding default static numerical metadata.

    Returns:
        Tuple[np.ndarray, np.ndarray]:
            - X_static_num: Shape (1, 16)
            - X_static_cat: Shape (1, 3)
    """
    default_num = {
        "shp_centroid_lat": 12.9716,
        "lat": 12.9716,
        "distance_to_nearest_major_highway_km": 1.2,
        "green_cover_pct": 22.5,
        "road_density_km_km2": 4.5,
        "pop_density": 8500.0,
        "distance_to_nearest_industrial_area_km": 3.8,
        "shp_centroid_lon": 77.5946,
        "lon": 77.5946,
        "elevation_m": 920.0,
        "industrial_zone_density": 0.15,
        "highway_proximity_score": 0.85,
        "vegetation_index_proxy": 0.42,
        "coastal_distance_km": 280.0,
        "urban_density_index": 0.72,
        "terrain_roughness": 12.0,
    }

    if custom_static_num:
        default_num.update(custom_static_num)

    num_arr = np.array([default_num[key] for key in STATIC_NUM_FEATURE_NAMES], dtype=np.float32)
    cat_arr = np.array([district_id, land_use_id, urban_rural_id], dtype=np.int32)

    return np.expand_dims(num_arr, axis=0), np.expand_dims(cat_arr, axis=0)
