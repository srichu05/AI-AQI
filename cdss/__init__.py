"""AI-AQI Clinical Decision Support System (CDSS) Package.

Modular environmental health-risk support system providing personalized rule-based
respiratory and skin risk stratification, DL prediction adaptation, and preventive recommendations.
"""

from cdss.cdss_service import CDSSService, DISCLAIMER_TEXT
from cdss.dl_adapter import DL_TO_CDSS_RISK_MAP, adapt_dl_prediction
from cdss.environmental_risk import evaluate_environmental_risk
from cdss.recommendation_engine import generate_recommendations
from cdss.respiratory_rules import evaluate_respiratory_risk
from cdss.schemas import EnvironmentalInput, PatientContext
from cdss.skin_rules import evaluate_skin_risk

__all__ = [
    "PatientContext",
    "EnvironmentalInput",
    "evaluate_environmental_risk",
    "evaluate_respiratory_risk",
    "evaluate_skin_risk",
    "generate_recommendations",
    "CDSSService",
    "DISCLAIMER_TEXT",
    "adapt_dl_prediction",
    "DL_TO_CDSS_RISK_MAP",
]
