import { fetchApi } from "./client";
import type { PredictionRequest, PredictionResponse } from "../types/api";

/**
 * POST /predict
 * Triggers DL model inference for single or batch feature vectors.
 */
export async function predictAQI(
  payload: PredictionRequest
): Promise<PredictionResponse> {
  return fetchApi<PredictionResponse>("/predict", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
