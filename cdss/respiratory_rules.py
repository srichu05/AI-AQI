"""Respiratory Risk Personalization Engine for AI-AQI CDSS.

Stratifies 'Personalized Respiratory Environmental Risk' by integrating environmental air pollution
risk with patient-specific contextual factors (age-based vulnerability, smoking status, existing condition, severity).

Uses transparent project-defined rule logic without medical diagnostic claims or arbitrary clinical coefficients.

DISCLAIMER:
"Age-based modifiers in this prototype are project-defined contextual vulnerability rules and are not independently clinically validated."
"""

from typing import Any, Dict, List
from cdss.schemas import PatientContext


def evaluate_respiratory_risk(
    env_risk: str,
    env_contributors: List[str],
    patient: PatientContext
) -> Dict[str, Any]:
    """Evaluates personalized respiratory environmental risk based on environmental risk and patient context.

    Args:
        env_risk: Environmental risk label ("Low", "Moderate", "High").
        env_contributors: Environmental pollutant contributors (e.g. ["PM2.5", "NO2"]).
        patient: Validated PatientContext object.

    Returns:
        Dict containing:
            - respiratory_environmental_risk: "Low", "Moderate", or "High"
            - respiratory_contributors: List of environmental and patient contributors
            - patient_context_factors: List of patient contextual factors
    """
    patient_context_factors: List[str] = []
    respiratory_contributors: List[str] = list(env_contributors)

    # Map environmental risk base level to numeric rank: Low=0, Moderate=1, High=2
    risk_rank_map = {"Low": 0, "Moderate": 1, "High": 2}
    base_rank = risk_rank_map.get(env_risk, 0)
    current_rank = base_rank

    # 1. Condition & Severity Impact
    if patient.respiratory_condition != "none":
        cond_str = patient.respiratory_condition
        sev_str = patient.respiratory_severity
        factor_desc = f"Existing respiratory condition: {cond_str} ({sev_str})"
        patient_context_factors.append(factor_desc)
        respiratory_contributors.append(factor_desc)

        if base_rank == 2:  # High environmental risk
            current_rank = 2
        elif base_rank == 1:  # Moderate environmental risk
            if patient.respiratory_severity in ("moderate", "severe"):
                current_rank = 2  # Escalates to High under Moderate env pollution
            else:
                current_rank = 1
        elif base_rank == 0:  # Low environmental risk
            if patient.respiratory_severity == "severe":
                current_rank = 1  # Escalates to Moderate (Low env risk does NOT automatically become High)
            elif patient.respiratory_severity in ("moderate", "mild"):
                current_rank = 0  # Preserves Low risk under Low pollution

    # 2. Smoking Status Impact
    if patient.smoking_status == "current":
        patient_context_factors.append("Current smoking status")
        respiratory_contributors.append("Current smoking status")
        if base_rank >= 1:
            current_rank = min(2, current_rank + 1)
        elif base_rank == 0 and patient.respiratory_condition != "none":
            current_rank = max(current_rank, 1)
    elif patient.smoking_status == "former":
        patient_context_factors.append("Former smoking status")

    # 3. Contextual Age-Based Vulnerability Modifier
    if patient.age > 65 or patient.age < 12:
        age_group = "Advanced age (>65)" if patient.age > 65 else "Pediatric age (<12)"
        age_factor = f"{age_group} contextual vulnerability modifier"
        patient_context_factors.append(age_factor)
        if base_rank >= 1 and patient.respiratory_condition != "none":
            respiratory_contributors.append(age_factor)
            current_rank = min(2, current_rank + 1)

    rank_label_map = {0: "Low", 1: "Moderate", 2: "High"}
    respiratory_environmental_risk = rank_label_map[current_rank]

    return {
        "respiratory_environmental_risk": respiratory_environmental_risk,
        "respiratory_contributors": respiratory_contributors,
        "patient_context_factors": patient_context_factors,
    }
