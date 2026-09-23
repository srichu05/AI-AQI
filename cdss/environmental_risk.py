"""Environmental Risk Classification Engine for AI-AQI CDSS.

Applies project-defined environmental threshold rules on air pollution concentrations:
- HIGH: PM2.5 > 60 µg/m³ OR NO2 > 80 µg/m³
- MODERATE: 25 <= PM2.5 <= 60 µg/m³ OR 40 <= NO2 <= 80 µg/m³
- LOW: Otherwise

Calculates a normalized 0-100 environmental_risk_index for relative categorization.

DISCLAIMER:
"The environmental_risk_index is a project-defined normalized environmental pollution index
used for relative categorization. It is not a clinically validated probability or measure of disease."
"""

from typing import Any, Dict, List
from cdss.schemas import EnvironmentalInput


def evaluate_environmental_risk(env: EnvironmentalInput) -> Dict[str, Any]:
    """Classifies environmental air pollution risk and calculates environmental_risk_index.

    Args:
        env: Validated EnvironmentalInput data containing pollutant measurements.

    Returns:
        Dict containing:
            - environmental_risk: "High", "Moderate", or "Low"
            - environmental_risk_index: Integer normalized index [0-100]
            - environmental_contributors: List of pollutant names contributing to non-low risk
    """
    pm25 = env.pm25
    no2 = env.no2

    is_pm25_high = pm25 > 60.0
    is_no2_high = no2 > 80.0

    is_pm25_mod = 25.0 <= pm25 <= 60.0
    is_no2_mod = 40.0 <= no2 <= 80.0

    environmental_contributors: List[str] = []

    if is_pm25_high or is_no2_high:
        risk_category = "High"
        if is_pm25_high:
            environmental_contributors.append("PM2.5")
        if is_no2_high:
            environmental_contributors.append("NO2")
    elif is_pm25_mod or is_no2_mod:
        risk_category = "Moderate"
        if is_pm25_mod:
            environmental_contributors.append("PM2.5")
        if is_no2_mod:
            environmental_contributors.append("NO2")
    else:
        risk_category = "Low"

    # Deterministic engineering calculation for environmental_risk_index (0 - 100)
    # PM2.5 normalized relative to 60.0 µg/m³ threshold (scale factor 70)
    pm25_subscore = (pm25 / 60.0) * 70.0
    # NO2 normalized relative to 80.0 µg/m³ threshold (scale factor 70)
    no2_subscore = (no2 / 80.0) * 70.0

    raw_score = max(pm25_subscore, no2_subscore)

    if risk_category == "High":
        # Scale into 70 - 100 range
        environmental_risk_index = min(100, max(70, int(round(raw_score))))
    elif risk_category == "Moderate":
        # Scale into 40 - 69 range
        pm25_mod_ratio = (pm25 - 25.0) / 35.0 if pm25 >= 25.0 else 0.0
        no2_mod_ratio = (no2 - 40.0) / 40.0 if no2 >= 40.0 else 0.0
        mod_ratio = max(pm25_mod_ratio, no2_mod_ratio)
        environmental_risk_index = 40 + int(round(mod_ratio * 29.0))
        environmental_risk_index = min(69, max(40, environmental_risk_index))
    else:
        # Scale into 0 - 39 range
        ratio = max(pm25 / 25.0, no2 / 40.0)
        environmental_risk_index = min(39, int(round(ratio * 39.0)))

    return {
        "environmental_risk": risk_category,
        "environmental_risk_index": environmental_risk_index,
        "environmental_contributors": environmental_contributors,
    }
