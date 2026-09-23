import { BrainCircuit, Loader2, Sparkles } from "lucide-react";
import { SpotlightCard } from "@/components/ui/spotlight-card";

export function PredictionProcessingState() {
  return (
    <SpotlightCard className="p-12 text-center space-y-6 text-slate-900 border-white/60 bg-white/40 backdrop-blur-2xl flex flex-col items-center justify-center">
      <div className="relative flex items-center justify-center">
        <div className="absolute h-24 w-24 rounded-full border-4 border-sky-400/40 animate-ping" />
        <div className="flex h-20 w-20 items-center justify-center rounded-full border border-sky-300 bg-sky-600 text-white shadow-lg">
          <BrainCircuit className="h-10 w-10 animate-pulse" />
        </div>
      </div>

      <div className="space-y-2 max-w-md">
        <h3 className="text-2xl font-black text-slate-900 tracking-tight drop-shadow-xs">
          Executing Neural Risk Model Inference
        </h3>
        <p className="text-xs font-bold text-slate-700">
          Constructing 7x24 dynamic temporal tensor matrix & evaluating calibrated risk thresholds...
        </p>
      </div>

      <div className="flex items-center gap-2 rounded-full border border-slate-300 bg-white/70 px-4 py-1.5 text-xs font-extrabold text-slate-900 shadow-xs backdrop-blur-md">
        <Loader2 className="h-4 w-4 animate-spin text-sky-700" />
        <span>Evaluating /predict REST pipeline...</span>
      </div>

      <div className="text-[11px] font-bold text-slate-700 border-t border-sky-200/80 pt-4 flex items-center gap-1.5">
        <Sparkles className="h-3.5 w-3.5 text-sky-700" />
        <span>Frozen Model Checkpoint: FINAL_OFFICIAL_DL_MODEL_v1.0</span>
      </div>
    </SpotlightCard>
  );
}
