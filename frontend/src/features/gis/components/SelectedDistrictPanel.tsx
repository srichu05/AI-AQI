import type { KarnatakaDistrictProperties } from "@/types/api";
import { BrainCircuit, MapPin, MousePointerClick, Stethoscope, Wind, Thermometer, Droplets, Gauge } from "lucide-react";

export interface SelectedDistrictPanelProps {
  selectedDistrict: KarnatakaDistrictProperties | null;
}

export function SelectedDistrictPanel({ selectedDistrict }: SelectedDistrictPanelProps) {
  const navigateTo = (hash: string) => {
    window.location.hash = hash;
  };

  if (!selectedDistrict) {
    return (
      <div className="rounded-2xl border border-white/60 bg-white/70 px-5 py-4 backdrop-blur-2xl text-center flex items-center justify-center gap-3 shadow-lg">
        <MousePointerClick className="h-5 w-5 text-sky-700 shrink-0 animate-bounce" />
        <span className="text-xs font-bold text-sky-950">
          Click any Karnataka district polygon on the choropleth map above to inspect its dataset environmental risk measurements.
        </span>
      </div>
    );
  }

  const getBadgeStyle = (riskClass: number | null | undefined) => {
    switch (riskClass) {
      case 4:
        return "border-purple-400 bg-purple-600 text-white shadow-purple-900/20";
      case 3:
        return "border-rose-400 bg-rose-600 text-white shadow-rose-900/20";
      case 2:
        return "border-orange-400 bg-orange-600 text-white shadow-orange-900/20";
      case 1:
        return "border-amber-400 bg-amber-600 text-white shadow-amber-900/20";
      case 0:
        return "border-emerald-400 bg-emerald-600 text-white shadow-emerald-900/20";
      default:
        return "border-slate-400 bg-slate-600 text-white shadow-slate-900/20";
    }
  };

  return (
    <div className="rounded-3xl border border-white/60 bg-white/85 p-5 md:p-6 backdrop-blur-3xl shadow-2xl space-y-4 text-slate-900 animate-fadeIn">
      {/* Header Info */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-600/90 text-white shadow-md">
            <MapPin className="h-5 w-5" />
          </div>
          <div>
            <h3 className="text-xl font-black text-sky-950 tracking-tight">
              {selectedDistrict.district_name} District
            </h3>
            <p className="text-[11px] font-bold text-sky-900">
              Dataset Snapshot: Year {selectedDistrict.year} · dataset_ml_ready.csv
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className={`rounded-xl border px-3.5 py-1 text-xs font-black shadow-sm ${getBadgeStyle(selectedDistrict.risk_class)}`}>
            {selectedDistrict.risk_label} {typeof selectedDistrict.risk_class === "number" ? `(Class ${selectedDistrict.risk_class})` : ""}
          </span>
        </div>
      </div>

      {/* Grid of Verified Environmental Measurements */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {/* PM2.5 Z-Score */}
        <div className="rounded-xl border border-sky-200/80 bg-white/90 p-3 space-y-1 shadow-xs">
          <div className="flex items-center gap-1.5 text-[10px] font-black uppercase text-sky-700">
            <Wind className="h-3.5 w-3.5" />
            <span>PM2.5 Z-Score</span>
          </div>
          <div className="text-lg font-black text-sky-950">
            {typeof selectedDistrict.pm25_ground === "number"
              ? `${selectedDistrict.pm25_ground >= 0 ? "+" : ""}${selectedDistrict.pm25_ground.toFixed(2)}`
              : "No Data"}
          </div>
        </div>

        {/* PM10 Z-Score */}
        <div className="rounded-xl border border-amber-200/80 bg-white/90 p-3 space-y-1 shadow-xs">
          <div className="flex items-center gap-1.5 text-[10px] font-black uppercase text-amber-700">
            <Wind className="h-3.5 w-3.5" />
            <span>PM10 Z-Score</span>
          </div>
          <div className="text-lg font-black text-sky-950">
            {typeof selectedDistrict.pm10_ground === "number"
              ? `${selectedDistrict.pm10_ground >= 0 ? "+" : ""}${selectedDistrict.pm10_ground.toFixed(2)}`
              : "No Data"}
          </div>
        </div>

        {/* Exposure Index */}
        <div className="rounded-xl border border-rose-200/80 bg-white/90 p-3 space-y-1 shadow-xs">
          <div className="flex items-center gap-1.5 text-[10px] font-black uppercase text-rose-700">
            <Gauge className="h-3.5 w-3.5" />
            <span>Exposure Index</span>
          </div>
          <div className="text-lg font-black text-sky-950">
            {typeof selectedDistrict.exposure_index === "number"
              ? selectedDistrict.exposure_index.toFixed(2)
              : "No Data"}
          </div>
        </div>

        {/* Temperature Z-Score */}
        <div className="rounded-xl border border-emerald-200/80 bg-white/90 p-3 space-y-1 shadow-xs">
          <div className="flex items-center gap-1.5 text-[10px] font-black uppercase text-emerald-700">
            <Thermometer className="h-3.5 w-3.5" />
            <span>Temp Z-Score</span>
          </div>
          <div className="text-lg font-black text-sky-950">
            {typeof selectedDistrict.temperature_C === "number"
              ? `${selectedDistrict.temperature_C >= 0 ? "+" : ""}${selectedDistrict.temperature_C.toFixed(2)}`
              : "No Data"}
          </div>
        </div>

        {/* Relative Humidity Z-Score */}
        <div className="rounded-xl border border-indigo-200/80 bg-white/90 p-3 space-y-1 shadow-xs">
          <div className="flex items-center gap-1.5 text-[10px] font-black uppercase text-indigo-700">
            <Droplets className="h-3.5 w-3.5" />
            <span>Humidity Z-Score</span>
          </div>
          <div className="text-lg font-black text-sky-950">
            {typeof selectedDistrict.relative_humidity === "number"
              ? `${selectedDistrict.relative_humidity >= 0 ? "+" : ""}${selectedDistrict.relative_humidity.toFixed(2)}`
              : "No Data"}
          </div>
        </div>
      </div>

      {/* Action CTAs */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-200 pt-3">
        <span className="text-[11px] font-bold text-sky-900">
          Source: Verified ML Dataset Feature Extraction
        </span>

        <div className="flex flex-wrap items-center gap-2">
          <button
            type="button"
            onClick={() => navigateTo("prediction")}
            className="inline-flex items-center gap-1.5 rounded-xl border border-sky-400 bg-sky-600 px-3.5 py-1.5 text-xs font-black uppercase tracking-wider text-white shadow-md transition-all hover:bg-sky-700"
          >
            <BrainCircuit className="h-3.5 w-3.5" />
            <span>Run AI Prediction</span>
          </button>

          <button
            type="button"
            onClick={() => navigateTo("cdss")}
            className="inline-flex items-center gap-1.5 rounded-xl border border-indigo-400 bg-indigo-600 px-3.5 py-1.5 text-xs font-black uppercase tracking-wider text-white shadow-md transition-all hover:bg-indigo-700"
          >
            <Stethoscope className="h-3.5 w-3.5" />
            <span>Assess Health Risk</span>
          </button>
        </div>
      </div>
    </div>
  );
}
