import { ShieldCheck, Stethoscope } from "lucide-react";
import { SpotlightCard } from "@/components/ui/spotlight-card";

export function CDSSHeader() {
  return (
    <SpotlightCard className="p-6 md:p-8 space-y-3 text-slate-950 border-white/30 bg-white/[0.06] backdrop-blur-xl shadow-xl">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-sky-400 bg-sky-600 text-white shadow-md">
            <Stethoscope className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-3xl font-black tracking-tight text-slate-950 md:text-4xl drop-shadow-sm">
              Environmental Health Risk Assessment
            </h1>
            <p className="text-xs font-extrabold text-slate-900 mt-0.5">
              Combine environmental exposure with individual vulnerability factors to generate personalized preventive guidance
            </p>
          </div>
        </div>

        <div className="inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/10 px-4 py-1.5 text-xs font-black text-slate-950 backdrop-blur-md shadow-xs">
          <ShieldCheck className="h-4 w-4 text-sky-800" />
          <span>POST /cdss/assess REST API • CDSS Rule Engine</span>
        </div>
      </div>
    </SpotlightCard>
  );
}
