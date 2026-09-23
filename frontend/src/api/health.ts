import { fetchApi } from "./client";
import type { HealthStatusResponse } from "../types/api";

/**
 * GET /health
 * Checks AI-AQI model health, version, and diagnostic readiness.
 */
export async function getHealth(): Promise<HealthStatusResponse> {
  return fetchApi<HealthStatusResponse>("/health");
}
