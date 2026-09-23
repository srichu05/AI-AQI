import { fetchApi } from "./client";
import type { LatestTelemetryResponse, TelemetryHistoryResponse } from "../types/api";

/**
 * GET /api/telemetry/latest
 * Fetches the latest persisted hardware sensor telemetry reading.
 */
export async function getLatestTelemetry(): Promise<LatestTelemetryResponse> {
  return fetchApi<LatestTelemetryResponse>("/api/telemetry/latest");
}

/**
 * GET /api/telemetry/history?limit=30
 * Fetches the most recent N persisted hardware sensor telemetry readings.
 */
export async function getTelemetryHistory(limit: number = 30): Promise<TelemetryHistoryResponse> {
  return fetchApi<TelemetryHistoryResponse>(`/api/telemetry/history?limit=${limit}`);
}

