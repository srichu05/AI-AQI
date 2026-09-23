"""Deep Learning Model Adapter for AI-AQI CDSS.

Adapts 5-class DL AQI risk predictions (from AQIInferenceEngine.predict_single)
into 3-tier CDSS-compatible environmental risk categories without altering raw predictions.

5-CLASS -> 3-TIER MAPPING:
    DL Class 0 ("Low")            -> CDSS model_environmental_risk: "Low"
    DL Class 1 ("Moderate")       -> CDSS model_environmental_risk: "Moderate"
    DL Class 2 ("Unhealthy")      -> CDSS model_environmental_risk: "High"
    DL Class 3 ("Very Unhealthy") -> CDSS model_environmental_risk: "High"
    DL Class 4 ("Severe")         -> CDSS model_environmental_risk: "High"
"""

from typing import Any, Dict, List

# Standard 5-class DL label dictionary
VALID_DL_LABELS = {
    0: "Low",
    1: "Moderate",
    2: "Unhealthy",
    3: "Very Unhealthy",
    4: "Severe",
}

# 5-Class to 3-Tier CDSS Environmental Risk Mapping
DL_TO_CDSS_RISK_MAP: Dict[int, str] = {
    0: "Low",
    1: "Moderate",
    2: "High",
    3: "High",
    4: "High",
}


def adapt_dl_prediction(prediction: Dict[str, Any]) -> Dict[str, Any]:
    """Validates raw DL prediction payload and returns CDSS-compatible payload.

    Args:
        prediction: Prediction payload dictionary returned by AQIInferenceEngine.predict_single().

    Returns:
        Dict[str, Any]: Validated adapter dictionary preserving raw DL outputs and adding model_environmental_risk.

    Raises:
        ValueError: If risk_class, risk_label, or probabilities fail integrity checks.
    """
    if not isinstance(prediction, dict):
        raise ValueError("DL prediction payload must be a dictionary.")

    # 1. Validate risk_class
    if "risk_class" not in prediction or not isinstance(prediction["risk_class"], int):
        raise ValueError("DL prediction payload missing valid integer 'risk_class'.")

    risk_class = prediction["risk_class"]
    if risk_class not in DL_TO_CDSS_RISK_MAP:
        raise ValueError(f"Invalid risk_class value '{risk_class}'. Must be an integer between 0 and 4.")

    # 2. Validate risk_label consistency if present
    if "risk_label" in prediction:
        expected_label = VALID_DL_LABELS[risk_class]
        actual_label = prediction["risk_label"]
        if actual_label != expected_label:
            raise ValueError(
                f"Inconsistent risk_label '{actual_label}' for risk_class {risk_class}. Expected '{expected_label}'."
            )

    # 3. Validate probabilities if present
    if "probabilities" in prediction:
        probs = prediction["probabilities"]
        if not isinstance(probs, (list, tuple)) or len(probs) != 5:
            raise ValueError(f"Invalid 'probabilities' field. Expected list of 5 floats, got {probs}.")
        if any(not isinstance(p, (int, float)) or p < 0.0 for p in probs):
            raise ValueError("All probability values must be non-negative numbers.")

    # 4. Perform 5-class to 3-tier mapping
    mapped_environmental_risk = DL_TO_CDSS_RISK_MAP[risk_class]

    # 5. Return preserved raw output + mapped category
    return {
        "model_risk_class": risk_class,
        "model_risk_label": prediction.get("risk_label", VALID_DL_LABELS[risk_class]),
        "model_probabilities": list(prediction.get("probabilities", [])),
        "applied_thresholds": list(prediction.get("applied_thresholds", [])),
        "model_version": prediction.get("model_version", "UNKNOWN"),
        "model_environmental_risk": mapped_environmental_risk,
    }
