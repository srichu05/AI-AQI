import { fetchApi } from "./client";
import type { CDSSAssessmentRequest, CDSSAssessmentResponse } from "../types/api";

/**
 * POST /cdss/assess
 * Evaluates clinical health risk under rule_based or dl_integrated mode.
 */
export async function assessCDSSRisk(
  payload: CDSSAssessmentRequest
): Promise<CDSSAssessmentResponse> {
  return fetchApi<CDSSAssessmentResponse>("/cdss/assess", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
