"""Data Validation Schemas for the AI-AQI Clinical Decision Support System (CDSS).

Enforces structural, range, and categorical integrity on patient context and environmental input data.
"""

from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field, model_validator


SmokingStatus = Literal["never", "former", "current"]
RespiratoryCondition = Literal["none", "asthma", "copd", "other"]
ConditionSeverity = Literal["none", "mild", "moderate", "severe"]
SkinCondition = Literal["none", "eczema", "dermatitis", "other"]


class PatientContext(BaseModel):
    """Schema for validated patient/context information."""

    age: int = Field(
        ...,
        ge=0,
        le=120,
        description="Patient age in years [0-120]"
    )
    smoking_status: SmokingStatus = Field(
        ...,
        description="Smoking history status: 'never', 'former', or 'current'"
    )
    respiratory_condition: RespiratoryCondition = Field(
        ...,
        description="Pre-existing respiratory condition: 'none', 'asthma', 'copd', or 'other'"
    )
    respiratory_severity: ConditionSeverity = Field(
        ...,
        description="Severity of respiratory condition: 'none', 'mild', 'moderate', or 'severe'"
    )
    skin_condition: SkinCondition = Field(
        ...,
        description="Pre-existing skin condition: 'none', 'eczema', 'dermatitis', or 'other'"
    )
    skin_severity: ConditionSeverity = Field(
        ...,
        description="Severity of skin condition: 'none', 'mild', 'moderate', or 'severe'"
    )
    latitude: float = Field(
        ...,
        ge=-90.0,
        le=90.0,
        description="Geographic latitude coordinate [-90.0 to 90.0]"
    )
    longitude: float = Field(
        ...,
        ge=-180.0,
        le=180.0,
        description="Geographic longitude coordinate [-180.0 to 180.0]"
    )

    @model_validator(mode="after")
    def validate_condition_severity_alignment(self) -> "PatientContext":
        """Ensures severity is 'none' when no condition is specified, and non-none when a condition is present."""
        if self.respiratory_condition == "none" and self.respiratory_severity != "none":
            raise ValueError("respiratory_severity must be 'none' when respiratory_condition is 'none'")
        if self.respiratory_condition != "none" and self.respiratory_severity == "none":
            raise ValueError("respiratory_severity must be specified (mild, moderate, severe) when a respiratory condition exists")

        if self.skin_condition == "none" and self.skin_severity != "none":
            raise ValueError("skin_severity must be 'none' when skin_condition is 'none'")
        if self.skin_condition != "none" and self.skin_severity == "none":
            raise ValueError("skin_severity must be specified (mild, moderate, severe) when a skin condition exists")

        return self


class EnvironmentalInput(BaseModel):
    """Schema for ambient air pollution environmental data."""

    pm25: float = Field(
        ...,
        ge=0.0,
        description="PM2.5 fine particulate concentration in µg/m³"
    )
    pm10: float = Field(
        ...,
        ge=0.0,
        description="PM10 coarse particulate concentration in µg/m³"
    )
    no2: float = Field(
        ...,
        ge=0.0,
        description="Nitrogen Dioxide concentration in µg/m³"
    )
    o3: float = Field(
        ...,
        ge=0.0,
        description="Ozone concentration in µg/m³"
    )
    so2: float = Field(
        ...,
        ge=0.0,
        description="Sulfur Dioxide concentration in µg/m³"
    )
    co: float = Field(
        ...,
        ge=0.0,
        description="Carbon Monoxide concentration in mg/m³"
    )
    model_predicted_risk: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional pre-computed AI-AQI model prediction payload"
    )
