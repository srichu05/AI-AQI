import { fetchApi } from "./client";
import type { MapDataResponse, KarnatakaGeoJSONResponse } from "../types/api";


/**
 * GET /map_data
 * Fetches spatial district-wide AQI predictions for GIS rendering.
 */
export async function getMapData(): Promise<MapDataResponse> {
  return fetchApi<MapDataResponse>("/map_data");
}

/**
 * GET /api/karnataka_map_data?year={year}
 * Fetches official 30-district Karnataka polygon GeoJSON joined with ML dataset properties.
 */
export async function getKarnatakaMapData(year: number = 2025): Promise<KarnatakaGeoJSONResponse> {
  return fetchApi<KarnatakaGeoJSONResponse>(`/api/karnataka_map_data?year=${year}`);
}

