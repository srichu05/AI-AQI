import { Activity, Cpu, Layers } from "lucide-react";

export interface SensorMetricsRowProps {
  pm25?: number;
  pm10?: number;
  pm1?: number;
  isStale?: boolean;
}

export function SensorMetricsRow({
  pm25,
  pm10,
  pm1,
  isStale,
}: SensorMetricsRowProps) {
  const pm25Str = typeof pm25 === "number" ? `${pm25.toFixed(1)} µg/m³` : "-- µg/m³";
  const pm10Str = typeof pm10 === "number" ? `${pm10.toFixed(1)} µg/m³` : "-- µg/m³";
  const pm1Str = typeof pm1 === "number" ? `${pm1.toFixed(1)} µg/m³` : "-- µg/m³";

  const pmMetrics = [
    {
      label: "Ground PM2.5",
      value: pm25Str,
      status: typeof pm25 !== "number" ? "No Data" : isStale ? "Stale" : pm25 <= 12 ? "Good" : pm25 <= 35 ? "Moderate" : "Unhealthy",
      statusColor: typeof pm25 !== "number" ? "bg-slate-500/30 text-slate-200 border-slate-400/40" : isStale ? "bg-amber-400/30 text-amber-100 border-amber-400/40 font-black" : "bg-emerald-400/30 text-emerald-100 border-emerald-400/40 font-black",
      icon: Activity,
      iconColor: "text-sky-300",
      rot: -12,
    },
    {
      label: "Ground PM10",
      value: pm10Str,
      status: typeof pm10 !== "number" ? "No Data" : isStale ? "Stale" : pm10 <= 50 ? "Good" : "Moderate",
      statusColor: typeof pm10 !== "number" ? "bg-slate-500/30 text-slate-200 border-slate-400/40" : isStale ? "bg-amber-400/30 text-amber-100 border-amber-400/40 font-black" : "bg-emerald-400/30 text-emerald-100 border-emerald-400/40 font-black",
      icon: Cpu,
      iconColor: "text-indigo-300",
      rot: 2,
    },
    {
      label: "Ground PM1.0",
      value: pm1Str,
      status: typeof pm1 !== "number" ? "No Data" : isStale ? "Stale" : "Calibrated",
      statusColor: typeof pm1 !== "number" ? "bg-slate-500/30 text-slate-200 border-slate-400/40" : isStale ? "bg-amber-400/30 text-amber-100 border-amber-400/40 font-black" : "bg-teal-400/30 text-teal-100 border-teal-400/40 font-black",
      icon: Layers,
      iconColor: "text-teal-300",
      rot: 14,
    },
  ];

  return (
    <div className="w-full flex items-center justify-center py-2">
      {/* 3 Ground PM Cards Stack (Using exact user card design with hover fan & glass styling) */}
      <div className="group relative flex items-center justify-center py-4 px-2 w-full max-w-4xl">
        {pmMetrics.map((item, idx) => {
          const Icon = item.icon;
          return (
            <div
              key={idx}
              style={{ "--r": item.rot } as React.CSSProperties}
              className="group/card relative flex flex-col justify-between w-[220px] sm:w-[240px] h-[210px] sm:h-[225px] rounded-2xl border border-white/25 bg-gradient-to-b from-white/20 via-white/10 to-transparent shadow-[0_25px_25px_rgba(0,0,0,0.25)] backdrop-blur-md transition-all duration-500 hover:z-40 hover:scale-105 -mx-8 sm:-mx-10 md:-mx-12 rotate-[calc(var(--r)*1deg)] group-hover:rotate-0 group-hover:mx-2 md:group-hover:mx-3 shrink-0 overflow-hidden cursor-pointer"
            >
              {/* SVG Animated Line Border Feature */}
              <svg className="absolute inset-0 size-full pointer-events-none z-30" xmlns="http://www.w3.org/2000/svg">
                <line x1="0" y1="0" x2="100%" y2="0" className="stroke-white/40 stroke-[4] transition-transform duration-700 ease-in-out group-hover/card:-translate-x-full" />
                <line x1="0" y1="0" x2="0" y2="100%" className="stroke-white/40 stroke-[4] transition-transform duration-700 ease-in-out group-hover/card:translate-y-full" />
                <line x1="0" y1="100%" x2="100%" y2="100%" className="stroke-white/40 stroke-[4] transition-transform duration-700 ease-in-out group-hover/card:translate-x-full" />
                <line x1="100%" y1="0" x2="100%" y2="100%" className="stroke-white/40 stroke-[4] transition-transform duration-700 ease-in-out group-hover/card:-translate-y-full" />
              </svg>

              {/* Upper Icon & Content */}
              <div className="p-4 flex flex-col items-center justify-center text-center h-full gap-2">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/20 bg-white/10 text-white shadow-md backdrop-blur-md">
                  <Icon className={`h-5 w-5 ${item.iconColor}`} />
                </div>
                <div>
                  <p className="text-2xl sm:text-3xl font-black text-white tracking-tight drop-shadow-md">
                    {item.value}
                  </p>
                </div>
              </div>

              {/* Bottom Glass Strip (data-text banner matching snippet style) */}
              <div className="relative w-full h-[44px] bg-white/10 border-t border-white/15 backdrop-blur-md px-3.5 flex items-center justify-between">
                <span className="text-[11px] sm:text-xs font-extrabold text-white tracking-wide">
                  {item.label}
                </span>
                <span className={`rounded-full border px-2 py-0.5 text-[9px] font-black uppercase tracking-wider backdrop-blur-md shadow-xs ${item.statusColor}`}>
                  {item.status}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
