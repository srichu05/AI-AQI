"""CDSS Service Layer for AI-AQI.

High-level orchestrator class for the Clinical Decision Support System (CDSS).
Combines Patient Context, Environmental Input, Environmental Risk Classification,
DL Model Adaptation, Respiratory & Skin Risk Stratification, and Recommendation Generation.
"""

from typing import Any, Dict, Optional, Union

from cdss.dl_adapter import adapt_dl_prediction
from cdss.environmental_risk import evaluate_environmental_risk
from cdss.recommendation_engine import generate_recommendations
from cdss.respiratory_rules import evaluate_respiratory_risk
from cdss.schemas import EnvironmentalInput, PatientContext
from cdss.skin_rules import evaluate_skin_risk

DISCLAIMER_TEXT = (
    "This system provides environmental health-risk information and preventive guidance. "
    "It does not diagnose disease or replace professional clinical judgment."
)


class CDSSService:
    """Orchestrates environmental health-risk evaluation and preventive decision support."""

    def assess_patient(
        self,
        patient_data: Union[PatientContext, Dict[str, Any]],
        environmental_data: Union[EnvironmentalInput, Dict[str, Any]],
        model_prediction: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Runs the complete CDSS evaluation workflow for a patient.

        Workflow steps:
            1. Validate patient and environmental inputs against Pydantic schemas.
            2. Evaluate Rule-Based Environmental Risk (High/Moderate/Low + environmental_risk_index + Pollutants).
            3. Process DL model prediction payload through dl_adapter if supplied.
            4. Evaluate Personalized Respiratory Environmental Risk using primary environmental risk.
            5. Evaluate Pollution-Associated Skin Environmental Risk.
            6. Generate Non-Prescriptive Preventive Recommendations.
            7. Assemble structured output payload with non-diagnostic legal disclaimer.

        Args:
            patient_data: PatientContext instance or dict matching PatientContext schema.
            environmental_data: EnvironmentalInput instance or dict matching EnvironmentalInput schema.
            model_prediction: Optional dictionary containing pre-computed AI-AQI model predictions.

        Returns:
            Dict[str, Any]: Structured CDSS result payload.
        """
        # Step 1: Input Parsing and Schema Validation
        if isinstance(patient_data, dict):
            patient = PatientContext(**patient_data)
        else:
            patient = patient_data

        if isinstance(environmental_data, dict):
            env = EnvironmentalInput(**environmental_data)
        else:
            env = environmental_data

        # Explicit prediction override if provided
        dl_payload = model_prediction if model_prediction is not None else env.model_predicted_risk

        # Step 2: Rule-Based Environmental Risk Engine
        env_result = evaluate_environmental_risk(env)
        rule_env_risk = env_result["environmental_risk"]
        env_index = env_result["environmental_risk_index"]
        environmental_contributors = env_result["environmental_contributors"]

        # Step 3: Deep Learning Model Adapter Integration
        adapted_dl: Optional[Dict[str, Any]] = None
        if dl_payload is not None:
            adapted_dl = adapt_dl_prediction(dl_payload)
            primary_env_risk = adapted_dl["model_environmental_risk"]
        else:
            primary_env_risk = rule_env_risk

        # Step 4: Respiratory Risk Engine
        resp_result = evaluate_respiratory_risk(primary_env_risk, environmental_contributors, patient)
        resp_risk = resp_result["respiratory_environmental_risk"]
        respiratory_contributors = resp_result["respiratory_contributors"]
        patient_context_factors = resp_result["patient_context_factors"]

        # Step 5: Skin Risk Engine
        skin_result = evaluate_skin_risk(env, patient)
        skin_risk = skin_result["skin_environmental_risk"]
        skin_contributors = skin_result["skin_contributors"]

        # Step 6: Recommendation Engine
        recommendations = generate_recommendations(
            environmental_risk=primary_env_risk,
            respiratory_environmental_risk=resp_risk,
            skin_environmental_risk=skin_risk,
            patient=patient,
        )

        # Step 7: Assemble Output Payload with strict backward compatibility
        result: Dict[str, Any] = {}

        if adapted_dl is not None:
            # Dual-source reporting structure when DL model prediction is present
            result["rule_based_environmental_risk"] = rule_env_risk
            result["environmental_risk_index"] = env_index
            result["environmental_contributors"] = environmental_contributors
            result["model_risk_class"] = adapted_dl["model_risk_class"]
            result["model_risk_label"] = adapted_dl["model_risk_label"]
            result["model_environmental_risk"] = adapted_dl["model_environmental_risk"]
            result["model_probabilities"] = adapted_dl["model_probabilities"]
            result["model_version"] = adapted_dl["model_version"]
        else:
            # Standalone rule-based mode matching exact previous payload schema
            result["environmental_risk"] = rule_env_risk
            result["environmental_risk_index"] = env_index
            result["environmental_contributors"] = environmental_contributors

        result["respiratory_environmental_risk"] = resp_risk
        result["respiratory_contributors"] = respiratory_contributors
        result["skin_environmental_risk"] = skin_risk
        result["skin_contributors"] = skin_contributors
        result["patient_context_factors"] = patient_context_factors
        result["recommendations"] = recommendations
        result["disclaimer"] = DISCLAIMER_TEXT

        return result
