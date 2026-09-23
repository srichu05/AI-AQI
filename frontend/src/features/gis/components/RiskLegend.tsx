import type { ActiveLayer } from "./GISLayerControls";

export interface GISLegendProps {
  activeLayer: ActiveLayer;
}

export function RiskLegend({ activeLayer }: GISLegendProps) {
  if (activeLayer === "risk_class") {
    const legendItems = [
      { label: "Low (Class 0)", color: "bg-emerald-500", border: "border-emerald-600" },
      { label: "Moderate (Class 1)", color: "bg-amber-500", border: "border-amber-600" },
      { label: "High / Unhealthy (Class 2)", color: "bg-orange-500", border: "border-orange-600" },
      { label: "Very High (Class 3)", color: "bg-rose-500", border: "border-rose-600" },
      { label: "Severe (Class 4)", color: "bg-purple-500", border: "border-purple-600" },
    ];

    return (
      <div className="rounded-2xl border border-slate-200/80 bg-white/95 p-3 shadow-xl backdrop-blur-md space-y-1.5 text-slate-900 min-w-[170px]">
        <span className="text-[10px] font-black uppercase tracking-wider text-sky-800 block border-b border-slate-200 pb-1">
          AI Risk Scale
        </span>
        <div className="space-y-1">
          {legendItems.map((item, i) => (
            <div key={i} className="flex items-center gap-2 text-[11px] font-extrabold text-slate-800">
              <span className={`h-2.5 w-2.5 rounded-full border ${item.color} ${item.border} shadow-xs shrink-0`} />
              <span>{item.label}</span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // Continuous measurement legend for PM2.5 Z-Score, PM10 Z-Score, Exposure Index
  const titles: Record<string, string> = {
    pm25_ground: "PM2.5 Z-Score Scale",
    pm10_ground: "PM10 Z-Score Scale",
    exposure_index: "Exposure Index Scale",
  };

  const isZScoreLayer = activeLayer === "pm25_ground" || activeLayer === "pm10_ground";

  return (
    <div className="rounded-2xl border border-slate-200/80 bg-white/95 p-3 shadow-xl backdrop-blur-md space-y-2 text-slate-900 min-w-[180px]">
      <span className="text-[10px] font-black uppercase tracking-wider text-sky-800 block border-b border-slate-200 pb-1">
        {titles[activeLayer] || "Intensity Scale"}
      </span>
      <div className="h-3 w-full rounded-full bg-gradient-to-r from-emerald-500 via-amber-500 via-orange-500 to-purple-600 border border-slate-300" />
      {isZScoreLayer ? (
        <div className="flex justify-between text-[9px] font-black text-slate-700">
          <span>Below Mean (Z &lt; 0)</span>
          <span>Z = 0 (Mean)</span>
          <span>Above Mean (Z &gt; 0)</span>
        </div>
      ) : (
        <div className="flex justify-between text-[10px] font-black text-slate-700">
          <span>Lower Index</span>
          <span>Higher Index</span>
        </div>
      )}
    </div>
  );
}
