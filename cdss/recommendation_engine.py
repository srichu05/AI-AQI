"""Preventive Recommendation Engine for AI-AQI CDSS.

Generates general preventive environmental health guidance based on environmental risk classification,
personalized respiratory environmental risk, skin environmental risk, and patient behavioral/clinical factors.

STRICT MEDICAL BOUNDARIES:
- Does NOT prescribe medications or dosage modifications.
- Does NOT provide diagnostic claims or treatment plans.
- Provides non-invasive preventive guidance only.
"""

from typing import List
from cdss.schemas import PatientContext


def generate_recommendations(
    environmental_risk: str,
    respiratory_environmental_risk: str,
    skin_environmental_risk: str,
    patient: PatientContext
) -> List[str]:
    """Generates preventive environmental health guidance records.

    Args:
        environmental_risk: "High", "Moderate", or "Low"
        respiratory_environmental_risk: "High", "Moderate", or "Low"
        skin_environmental_risk: "High", "Moderate", or "Low"
        patient: Validated PatientContext object

    Returns:
        List[str]: List of actionable, non-prescriptive preventive recommendations.
    """
    recommendations: List[str] = []

    # 1. Respiratory Guidance based on Personalized Respiratory Environmental Risk
    if respiratory_environmental_risk == "High":
        recommendations.append("Reduce prolonged exposure to heavily polluted outdoor environments.")
        recommendations.append("Monitor respiratory symptoms.")
        recommendations.append("Follow existing clinician-directed care.")
        recommendations.append("Seek professional medical advice if symptoms worsen.")
    elif respiratory_environmental_risk == "Moderate":
        recommendations.append("Reduce prolonged outdoor exposure during periods of elevated pollution.")
        recommendations.append("Monitor symptoms.")
        recommendations.append("Follow existing medical advice.")
    else:  # Low
        recommendations.append("Maintain standard outdoor activities while remaining informed of local air quality trends.")

    # 2. Smoking-Cessation Guidance
    if patient.smoking_status == "current":
        recommendations.append("Seek smoking-cessation guidance and support programs to protect long-term respiratory health.")

    # 3. Skin Guidance based on Pollution-Associated Skin Risk
    if skin_environmental_risk == "High":
        recommendations.append("Reduce direct skin exposure during periods of elevated pollution.")
        recommendations.append("Monitor skin symptoms.")
        recommendations.append("Seek professional medical advice if skin symptoms persist or worsen.")
    elif skin_environmental_risk == "Moderate":
        recommendations.append("Consider gentle cleansing and barrier protection following outdoor pollution exposure.")

    # Remove duplicates while preserving order
    unique_recs: List[str] = []
    for rec in recommendations:
        if rec not in unique_recs:
            unique_recs.append(rec)

    return unique_recs
