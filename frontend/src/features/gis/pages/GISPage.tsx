import { useState, useEffect } from "react";
import { GradientBackground } from "@/components/ui/bloom-field-gradient";
import { GISHeader } from "../components/GISHeader";
import { GISSummaryCards } from "../components/GISSummaryCards";
import { GISLayerControls, type ActiveLayer } from "../components/GISLayerControls";
import { GISMap } from "../components/GISMap";
import { SelectedDistrictPanel } from "../components/SelectedDistrictPanel";
import { NextActionsNav } from "@/features/cdss/components/NextActionsNav";
import { getKarnatakaMapData } from "@/api/map";
import type { KarnatakaGeoJSONResponse, KarnatakaDistrictProperties } from "@/types/api";
import { AlertCircle, RefreshCw } from "lucide-react";

export function GISPage() {
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [selectedYear, setSelectedYear] = useState<number>(2025);
  const [activeLayer, setActiveLayer] = useState<ActiveLayer>("risk_class");
  const [geoJsonData, setGeoJsonData] = useState<KarnatakaGeoJSONResponse | null>(null);
  const [selectedDistrict, setSelectedDistrict] = useState<KarnatakaDistrictProperties | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchKarnatakaData = async (year: number) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const data = await getKarnatakaMapData(year);
      if (data && data.features && data.features.length > 0) {
        setGeoJsonData(data);
      } else {
        setErrorMessage("GIS API returned zero Karnataka district polygon features.");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load Karnataka GIS district polygon map data.";
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchKarnatakaData(selectedYear);
  }, [selectedYear]);

  const districtPropsList: KarnatakaDistrictProperties[] =
    geoJsonData?.features.map((f) => f.properties) || [];

  return (
    <div className="relative min-h-screen w-full bg-gradient-to-b from-[#3876ba] via-[#528dcb] to-[#7db6e6] text-sky-950 font-sans overflow-x-hidden pt-20 pb-6 md:pt-24 md:pb-10">
      {/* 1. Global Atmosphere (Bloom Field Gradient) */}
      <div className="absolute inset-0 z-0 opacity-50 pointer-events-none">
        <GradientBackground />
      </div>

      {/* 2. Page Container Surface */}
      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 space-y-6">
        {/* Header Banner */}
        <GISHeader />

        {/* Error Alert Banner */}
        {errorMessage && (
          <div className="rounded-3xl border border-rose-400 bg-rose-100/90 p-4 text-rose-950 shadow-md flex items-center justify-between gap-3 text-xs font-bold">
            <div className="flex items-center gap-3">
              <AlertCircle className="h-5 w-5 text-rose-700 shrink-0" />
              <span>GIS API Error: {errorMessage}</span>
            </div>
            <button
              type="button"
              onClick={() => fetchKarnatakaData(selectedYear)}
              className="inline-flex items-center gap-1.5 rounded-xl bg-rose-700 px-3 py-1.5 text-white font-black hover:bg-rose-800"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Retry
            </button>
          </div>
        )}

        {/* Loading State */}
        {isLoading ? (
          <div className="rounded-3xl border border-white/40 bg-white/20 p-12 text-center backdrop-blur-3xl shadow-xl space-y-4 animate-pulse">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl border border-sky-300 bg-sky-600 text-white shadow-lg">
              <RefreshCw className="h-8 w-8 animate-spin" />
            </div>
            <h4 className="text-xl font-black text-sky-950">
              Loading Karnataka GIS Spatial Risk Intelligence...
            </h4>
            <p className="text-xs font-bold text-sky-900">
              Joining 30 Karnataka district boundary polygons with ML dataset features ({selectedYear} snapshot)...
            </p>
          </div>
        ) : !geoJsonData || geoJsonData.features.length === 0 ? (
          <div className="rounded-3xl border border-white/40 bg-white/20 p-8 text-center backdrop-blur-3xl text-sky-950 font-bold text-sm">
            No spatial data available for the selected snapshot.
          </div>
        ) : (
          <div className="space-y-6 animate-fadeIn">
            {/* Dynamic Spatial Summary Strip */}
            <GISSummaryCards
              districtProps={districtPropsList}
              selectedYear={selectedYear}
            />

            {/* Interactive Layer & Snapshot Year Controls */}
            <GISLayerControls
              activeLayer={activeLayer}
              onLayerChange={setActiveLayer}
              selectedYear={selectedYear}
              onYearChange={setSelectedYear}
            />

            {/* Main Karnataka 30-District Polygon Choropleth Map */}
            <GISMap
              geoJsonData={geoJsonData}
              activeLayer={activeLayer}
              selectedDistrict={selectedDistrict}
              onSelectDistrict={setSelectedDistrict}
            />

            {/* Selected District Intelligence Drawer */}
            <SelectedDistrictPanel selectedDistrict={selectedDistrict} />

            {/* System Actions Navigation */}
            <NextActionsNav />
          </div>
        )}
      </div>
    </div>
  );
}
