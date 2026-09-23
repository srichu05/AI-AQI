import type { KarnatakaDistrictProperties } from "@/types/api";
import { Activity, AlertTriangle, Calendar } from "lucide-react";

export interface GISSummaryCardsProps {
  districtProps: KarnatakaDistrictProperties[];
  selectedYear: number;
}

export function GISSummaryCards({ districtProps, selectedYear }: GISSummaryCardsProps) {
  const totalDistricts = districtProps.length;

  // Calculate dominant risk class distribution dynamically
  const counts: Record<number, number> = { 0: 0, 1: 0, 2: 0, 3: 0, 4: 0 };
  districtProps.forEach((p) => {
    if (typeof p.risk_class === "number" && counts[p.risk_class] !== undefined) {
      counts[p.risk_class] += 1;
    }
  });

  const highRiskCount = (counts[2] || 0) + (counts[3] || 0) + (counts[4] || 0);

  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
      {/* 1. Monitored Districts */}
      <div className="rounded-2xl border border-white/60 bg-white/80 px-4 py-3.5 shadow-md backdrop-blur-xl flex items-center justify-between text-slate-900">
        <div>
          <span className="text-[10px] font-black uppercase tracking-wider text-sky-900">
            Monitored Districts
          </span>
          <div className="text-xl font-black text-sky-950 mt-0.5">{totalDistricts} Karnataka Districts</div>
        </div>
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-sky-600/90 text-white shadow-sm">
          <Activity className="h-4.5 w-4.5" />
        </div>
      </div>

      {/* 2. High / Severe Risk Status */}
      <div className="rounded-2xl border border-white/60 bg-white/80 px-4 py-3.5 shadow-md backdrop-blur-xl flex items-center justify-between text-slate-900">
        <div>
          <span className="text-[10px] font-black uppercase tracking-wider text-orange-800">
            High / Severe Risk Status
          </span>
          <div className="text-xl font-black text-orange-700 mt-0.5">{highRiskCount} / {totalDistricts} Districts</div>
          <p className="text-[9px] text-slate-600 font-bold">Class ≥ 2 (High, Very High, Severe)</p>
        </div>
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-orange-600/90 text-white shadow-sm">
          <AlertTriangle className="h-4.5 w-4.5" />
        </div>
      </div>

      {/* 3. Dataset Snapshot */}
      <div className="rounded-2xl border border-white/60 bg-white/80 px-4 py-3.5 shadow-md backdrop-blur-xl flex items-center justify-between text-slate-900">
        <div>
          <span className="text-[10px] font-black uppercase tracking-wider text-emerald-800">
            Dataset Snapshot
          </span>
          <div className="text-xl font-black text-emerald-800 mt-0.5">Year {selectedYear}</div>
          <p className="text-[9px] text-slate-600 font-bold">Latest ML dataset daily record</p>
        </div>
        <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-600/90 text-white shadow-sm">
          <Calendar className="h-4.5 w-4.5" />
        </div>
      </div>
    </div>
  );
}
