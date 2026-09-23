import { Stethoscope } from "lucide-react";
import { SpotlightCard } from "@/components/ui/spotlight-card";

export function CDSSProcessingState() {
  return (
    <SpotlightCard className="p-8 text-center space-y-4 animate-pulse text-slate-950 border-white/30 bg-white/[0.06] backdrop-blur-xl shadow-xl">
      <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl border border-sky-400 bg-sky-600 text-white shadow-lg">
        <Stethoscope className="h-8 w-8 animate-bounce" />
      </div>
      <div className="space-y-1">
        <h4 className="text-xl font-black text-slate-950 drop-shadow-xs">
          Evaluating CDSS Environmental Health Risk Rules
        </h4>
        <p className="text-xs font-bold text-slate-800">
          Synthesizing environmental exposure, respiratory vulnerability, and skin stratification...
        </p>
      </div>

      <div className="mx-auto max-w-md space-y-2 pt-2">
        <div className="flex items-center justify-between text-[11px] font-black text-slate-900">
          <span>1. Reading environmental pollutant matrix</span>
          <span className="text-emerald-800 font-black">✓ Done</span>
        </div>
        <div className="flex items-center justify-between text-[11px] font-black text-slate-900">
          <span>2. Stratifying personal respiratory & skin rules</span>
          <span className="text-sky-800 font-black">Evaluating...</span>
        </div>
        <div className="flex items-center justify-between text-[11px] font-black text-slate-900">
          <span>3. Assembling non-prescriptive preventive guidance</span>
          <span className="text-slate-700 font-bold">Pending</span>
        </div>
      </div>
    </SpotlightCard>
  );
}
