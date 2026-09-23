"""Skin Risk Personalization Engine for AI-AQI CDSS.

Stratifies 'Pollution-Associated Skin Environmental Risk' based on ambient PM2.5 and Ozone (O3) levels
in conjunction with pre-existing skin conditions (eczema, dermatitis, other) and severity.
"""

from typing import Any, Dict, List
from cdss.schemas import EnvironmentalInput, PatientContext


def evaluate_skin_risk(
    env: EnvironmentalInput,
    patient: PatientContext
) -> Dict[str, Any]:
    """Evaluates pollution-associated skin environmental risk.

    Args:
        env: Validated EnvironmentalInput object.
        patient: Validated PatientContext object.

    Returns:
        Dict containing:
            - skin_environmental_risk: "Low", "Moderate", or "High"
            - skin_contributors: List of environmental pollutants and patient skin factors
    """
    skin_contributors: List[str] = []

    # Evaluate ambient skin-relevant environmental pollution (PM2.5, O3)
    pm25 = env.pm25
    o3 = env.o3

    is_high_skin_env = pm25 > 60.0 or o3 > 100.0
    is_mod_skin_env = (25.0 <= pm25 <= 60.0) or (50.0 <= o3 <= 100.0)

    if is_high_skin_env:
        base_rank = 2
        if pm25 > 60.0:
            skin_contributors.append("PM2.5")
        if o3 > 100.0:
            skin_contributors.append("O3")
    elif is_mod_skin_env:
        base_rank = 1
        if 25.0 <= pm25 <= 60.0:
            skin_contributors.append("PM2.5")
        if 50.0 <= o3 <= 100.0:
            skin_contributors.append("O3")
    else:
        base_rank = 0

    current_rank = base_rank

    # Patient skin condition modulation
    if patient.skin_condition != "none":
        cond_str = patient.skin_condition
        sev_str = patient.skin_severity
        skin_contributors.append(f"Existing skin condition: {cond_str} ({sev_str})")

        if base_rank == 2:
            current_rank = 2
        elif base_rank == 1:
            if patient.skin_severity in ("moderate", "severe"):
                current_rank = 2
            else:
                current_rank = 1
        elif base_rank == 0:
            if patient.skin_severity == "severe":
                current_rank = 1
            else:
                current_rank = 0

    rank_label_map = {0: "Low", 1: "Moderate", 2: "High"}
    skin_environmental_risk = rank_label_map[current_rank]

    return {
        "skin_environmental_risk": skin_environmental_risk,
        "skin_contributors": skin_contributors,
    }
