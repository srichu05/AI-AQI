/**
 * TypeScript API contracts matching AI-AQI backend FastAPI service (deployment/api.py).
 */

// ------------------------------------------------------------------
// 1. GET /health
// ------------------------------------------------------------------

export interface HealthStatusResponse {
  status: "healthy" | string;
  model_loaded: boolean;
  model_version: string;
  model_path: string;
  thresholds: number[];
}

// ------------------------------------------------------------------
// 2. POST /predict
// ------------------------------------------------------------------

export interface DynamicFeatures {
  /** 7x24 matrix: 7 daily timesteps of 24 dynamic features */
  data: number[][];
}

export interface StaticNumFeatures {
  /** 16 continuous static numerical features */
  data: number[];
}

export interface StaticCatFeatures {
  /** 3 categorical indices: [district_id (0-29), land_use_id (0-5), urban_rural_id (0-2)] */
  data: number[];
}

export interface PredictionRequest {
  dynamic: DynamicFeatures;
  static_num: StaticNumFeatures;
  static_cat: StaticCatFeatures;
  feature_vector_id?: number;
  device_id?: string;
}

export interface SinglePredictionResult {
  prediction_id?: number;
  feature_vector_id?: number;
  sample_index?: number;
  risk_class: number;
  risk_label: string;
  probabilities: number[];
  applied_thresholds?: number[];
  model_version: string;
  timestamp: string;
}

export interface PredictionResponse {
  success: boolean;
  prediction: SinglePredictionResult;
}

// ------------------------------------------------------------------
// 3. GET /map_data
// ------------------------------------------------------------------

export interface DistrictPrediction {
  district_id: number;
  district_name: string;
  lat: number;
  lon: number;
  risk_class: number;
  risk_label: string;
  probabilities: number[];
  timestamp: string;
}

export interface MapDataResponse {
  success: boolean;
  district_count: number;
  districts: DistrictPrediction[];
}

export interface KarnatakaDistrictProperties {
  district_name: string;
  has_data?: boolean;
  risk_class: number | null;
  risk_label: string;
  pm25_ground: number | null;
  pm10_ground: number | null;
  exposure_index: number | null;
  temperature_C: number | null;
  relative_humidity: number | null;
  year: number;
}

export interface KarnatakaDistrictFeature {
  type: "Feature";
  geometry: any;
  properties: KarnatakaDistrictProperties;
}

export interface KarnatakaGeoJSONResponse {
  type: "FeatureCollection";
  features: KarnatakaDistrictFeature[];
}


// ------------------------------------------------------------------
// 4. POST /cdss/assess
// ------------------------------------------------------------------

export type SmokingStatus = "never" | "former" | "current";
export type RespiratoryCondition = "none" | "asthma" | "copd" | "other";
export type ConditionSeverity = "none" | "mild" | "moderate" | "severe";
export type SkinCondition = "none" | "eczema" | "dermatitis" | "other";

export interface PatientProfile {
  age: number;
  smoking_status: SmokingStatus;
  respiratory_condition: RespiratoryCondition;
  respiratory_severity: ConditionSeverity;
  skin_condition: SkinCondition;
  skin_severity: ConditionSeverity;
  latitude: number;
  longitude: number;
}

export interface EnvironmentalReadings {
  pm25: number;
  pm10: number;
  no2: number;
  o3: number;
  so2: number;
  co: number;
}

export interface PredictionFeaturesRequest {
  dynamic?: DynamicFeatures;
  static_num?: StaticNumFeatures;
  static_cat?: StaticCatFeatures;
  feature_vector_id?: number;
  device_id?: string;
}

export interface CDSSAssessmentRequest {
  patient: PatientProfile;
  environmental: EnvironmentalReadings;
  prediction_features?: PredictionFeaturesRequest;
}

export interface CDSSAssessmentResponse {
  mode: "rule_based" | "dl_integrated";
  assessment_id?: number;
  environmental_risk_index?: number;
  rule_based_environmental_risk?: string;
  model_environmental_risk?: string;
  model_risk_class?: number;
  model_risk_label?: string;
  model_probabilities?: number[];
  respiratory_environmental_risk: string;
  skin_environmental_risk: string;
  environmental_risk: string;
  environmental_contributors?: string[];
  respiratory_contributors?: string[];
  skin_contributors?: string[];
  patient_context_factors?: string[];
  recommendations: string[];
  disclaimer: string;
}


// ------------------------------------------------------------------
// 5. GET /api/telemetry/latest
// ------------------------------------------------------------------

export interface TelemetryRecord {
  id?: number;
  device_id: string;
  pm1_ground: number;
  pm25_ground: number;
  pm10_ground: number;
  timestamp_utc: string | null;
  source: string;
  created_at?: string | null;
}

export interface LatestTelemetryResponse {
  status: string;
  message?: string;
  data: TelemetryRecord | null;
}

export interface TelemetryHistoryResponse {
  status: string;
  message?: string;
  data: TelemetryRecord[];
}

