import { useEffect, useRef } from "react";
import type { KarnatakaGeoJSONResponse, KarnatakaDistrictProperties } from "@/types/api";
import type { ActiveLayer } from "./GISLayerControls";
import { MapContainer, TileLayer, GeoJSON, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import { RiskLegend } from "./RiskLegend";

export interface GISMapProps {
  geoJsonData: KarnatakaGeoJSONResponse | null;
  activeLayer: ActiveLayer;
  selectedDistrict: KarnatakaDistrictProperties | null;
  onSelectDistrict: (district: KarnatakaDistrictProperties) => void;
}

// 5-class color palette for Environmental Risk
function getRiskColor(riskClass: number): string {
  switch (riskClass) {
    case 4:
      return "#a855f7"; // Severe (Purple)
    case 3:
      return "#ef4444"; // Very High (Rose/Red)
    case 2:
      return "#f97316"; // High / Unhealthy (Orange)
    case 1:
      return "#f59e0b"; // Moderate (Amber)
    case 0:
    default:
      return "#10b981"; // Low (Emerald)
  }
}

// Continuous color scale for numeric measurement layers
function getContinuousColor(val: number, minVal: number, maxVal: number): string {
  const norm = Math.max(0, Math.min(1, (val - minVal) / (maxVal - minVal || 1)));
  if (norm < 0.25) return "#10b981";
  if (norm < 0.5) return "#f59e0b";
  if (norm < 0.75) return "#f97316";
  return "#a855f7";
}

// Map helper to automatically fit Leaflet bounds to full Karnataka state boundaries
function AutoFitStateBounds({ geoJsonData }: { geoJsonData: KarnatakaGeoJSONResponse | null }) {
  const map = useMap();

  useEffect(() => {
    if (geoJsonData && geoJsonData.features && geoJsonData.features.length > 0) {
      try {
        const geoJsonLayer = L.geoJSON(geoJsonData as any);
        const bounds = geoJsonLayer.getBounds();
        if (bounds.isValid()) {
          map.fitBounds(bounds, { padding: [30, 30] });
        }
      } catch (err) {
        console.warn("Failed to fit Karnataka bounds:", err);
      }
    }
  }, [geoJsonData, map]);

  return null;
}

export function GISMap({
  geoJsonData,
  activeLayer,
  selectedDistrict,
  onSelectDistrict,
}: GISMapProps) {
  // Center of Karnataka State (~ Lat 14.5°N, Lon 75.8°E)
  const karnatakaCenter: [number, number] = [14.5, 75.8];
  const geoJsonRef = useRef<L.GeoJSON | null>(null);

  // Compute min/max for active continuous layer across all features
  let minVal = 0;
  let maxVal = 1;
  if (geoJsonData && geoJsonData.features) {
    const vals = geoJsonData.features.map((f) => (f.properties as any)[activeLayer] || 0);
    minVal = Math.min(...vals);
    maxVal = Math.max(...vals);
  }

  // Polygon styling function
  const styleFeature = (feature: any) => {
    const props: KarnatakaDistrictProperties = feature.properties;
    const isSelected = selectedDistrict?.district_name === props.district_name;

    if (props.has_data === false || props.risk_class === null || props.risk_class === undefined) {
      return {
        fillColor: "#94a3b8",
        fillOpacity: 0.4,
        weight: isSelected ? 3 : 1.5,
        color: isSelected ? "#0f172a" : "#cbd5e1",
      };
    }

    let fillColor = getRiskColor(props.risk_class);
    if (activeLayer !== "risk_class") {
      const numVal = (props as any)[activeLayer];
      if (typeof numVal === "number") {
        fillColor = getContinuousColor(numVal, minVal, maxVal);
      } else {
        fillColor = "#94a3b8";
      }
    }

    return {
      fillColor,
      fillOpacity: isSelected ? 0.9 : 0.75,
      weight: isSelected ? 3 : 1.5,
      color: isSelected ? "#0f172a" : "#ffffff",
    };
  };

  // Event handlers per district polygon
  const onEachFeature = (feature: any, layer: L.Layer) => {
    const props: KarnatakaDistrictProperties = feature.properties;

    let tooltipContent = "";
    if (props.has_data === false || props.risk_class === null || props.risk_class === undefined) {
      tooltipContent = `<div class="text-xs font-black text-slate-900">${props.district_name} · No data available for ${props.year || 2025}</div>`;
    } else if (activeLayer === "risk_class") {
      tooltipContent = `<div class="text-xs font-black text-slate-900">${props.district_name} · Risk: ${props.risk_label} (Class ${props.risk_class})</div>`;
    } else if (activeLayer === "pm25_ground") {
      const val = typeof props.pm25_ground === "number" ? `${props.pm25_ground >= 0 ? "+" : ""}${props.pm25_ground.toFixed(2)}` : "N/A";
      tooltipContent = `<div class="text-xs font-black text-slate-900">${props.district_name} · PM2.5 Z-Score: ${val}</div>`;
    } else if (activeLayer === "pm10_ground") {
      const val = typeof props.pm10_ground === "number" ? `${props.pm10_ground >= 0 ? "+" : ""}${props.pm10_ground.toFixed(2)}` : "N/A";
      tooltipContent = `<div class="text-xs font-black text-slate-900">${props.district_name} · PM10 Z-Score: ${val}</div>`;
    } else if (activeLayer === "exposure_index") {
      const val = typeof props.exposure_index === "number" ? props.exposure_index.toFixed(2) : "N/A";
      tooltipContent = `<div class="text-xs font-black text-slate-900">${props.district_name} · Exposure Index: ${val}</div>`;
    }

    // Hover tooltip
    layer.bindTooltip(
      tooltipContent,
      { className: "custom-gis-tooltip", direction: "top", opacity: 0.98 }
    );

    // Click handler
    layer.on({
      mouseover: (e: any) => {
        const l = e.target;
        l.setStyle({ fillOpacity: 0.92, weight: 2.5, color: "#0f172a" });
      },
      mouseout: (e: any) => {
        if (geoJsonRef.current) {
          geoJsonRef.current.resetStyle(e.target);
        }
      },
      click: () => {
        onSelectDistrict(props);
      },
    });
  };

  return (
    <div className="relative h-[600px] md:h-[650px] w-full rounded-3xl overflow-hidden border border-white/60 shadow-2xl bg-slate-50">
      {/* Inject custom light theme Leaflet tooltip styling */}
      <style>{`
        .leaflet-container {
          background-color: #f8fafc !important;
        }
        .custom-gis-tooltip {
          background: rgba(255, 255, 255, 0.95) !important;
          border: 1px solid rgba(148, 163, 184, 0.5) !important;
          color: #0f172a !important;
          border-radius: 0.75rem !important;
          padding: 6px 10px !important;
          font-weight: 800 !important;
          font-size: 11px !important;
          box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.12) !important;
          backdrop-filter: blur(12px) !important;
        }
      `}</style>

      <MapContainer
        center={karnatakaCenter}
        zoom={7}
        scrollWheelZoom={true}
        className="h-full w-full z-0 bg-slate-50"
      >
        {/* OpenStreetMap Public Tile Layer (No API Key Required) */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Auto fit bounds to Karnataka state bounds */}
        <AutoFitStateBounds geoJsonData={geoJsonData} />

        {/* Real Karnataka 30-District Polygon GeoJSON Choropleth */}
        {geoJsonData && (
          <GeoJSON
            key={`${activeLayer}-${geoJsonData.features.length}`}
            ref={geoJsonRef as any}
            data={geoJsonData as any}
            style={styleFeature}
            onEachFeature={onEachFeature}
          />
        )}
      </MapContainer>

      {/* Floating Risk Legend (Top Right) */}
      <div className="absolute top-4 right-4 z-[400] pointer-events-auto">
        <RiskLegend activeLayer={activeLayer} />
      </div>
    </div>
  );
}
