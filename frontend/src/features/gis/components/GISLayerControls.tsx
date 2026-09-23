import { Layers, Calendar } from "lucide-react";

export type ActiveLayer = "risk_class" | "pm25_ground" | "pm10_ground" | "exposure_index";

export interface GISLayerControlsProps {
  activeLayer: ActiveLayer;
  onLayerChange: (layer: ActiveLayer) => void;
  selectedYear: number;
  onYearChange: (year: number) => void;
}

export function GISLayerControls({
  activeLayer,
  onLayerChange,
  selectedYear,
  onYearChange,
}: GISLayerControlsProps) {
  const layerButtons: { key: ActiveLayer; label: string }[] = [
    { key: "risk_class", label: "Environmental Risk" },
    { key: "pm25_ground", label: "PM2.5 Z-Score" },
    { key: "pm10_ground", label: "PM10 Z-Score" },
    { key: "exposure_index", label: "Exposure Index" },
  ];

  const years = [2025, 2024, 2023, 2022, 2021, 2020];

  return (
    <div className="rounded-2xl border border-white/60 bg-white/80 p-3 backdrop-blur-2xl shadow-xl flex flex-wrap items-center justify-between gap-3 text-slate-900">
      {/* Layer Selector */}
      <div className="flex flex-wrap items-center gap-1.5">
        <div className="flex items-center gap-1.5 text-xs font-black uppercase text-sky-900 mr-1">
          <Layers className="h-4 w-4 text-sky-700" />
          <span>Layer:</span>
        </div>
        {layerButtons.map((b) => (
          <button
            key={b.key}
            type="button"
            onClick={() => onLayerChange(b.key)}
            className={`rounded-xl px-3.5 py-1.5 text-xs font-black transition-all ${
              activeLayer === b.key
                ? "bg-sky-600 text-white shadow-md border border-sky-400"
                : "bg-white/80 text-sky-950 border border-sky-300/80 hover:bg-white hover:border-sky-400"
            }`}
          >
            {b.label}
          </button>
        ))}
      </div>

      {/* Temporal Year Selector */}
      <div className="flex items-center gap-2">
        <div className="flex items-center gap-1.5 text-xs font-black uppercase text-sky-900">
          <Calendar className="h-4 w-4 text-emerald-700" />
          <span>Snapshot Year:</span>
        </div>
        <select
          value={selectedYear}
          onChange={(e) => onYearChange(Number(e.target.value))}
          className="rounded-xl border border-sky-300/80 bg-white/90 px-3 py-1.5 text-xs font-black text-sky-950 focus:outline-none focus:ring-2 focus:ring-sky-500 shadow-xs"
        >
          {years.map((y) => (
            <option key={y} value={y} className="bg-white text-slate-900">
              {y}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
