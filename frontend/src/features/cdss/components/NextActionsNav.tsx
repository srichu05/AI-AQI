import { ArrowLeft, BrainCircuit, Activity } from "lucide-react";
import { SpotlightCard } from "@/components/ui/spotlight-card";

export function NextActionsNav() {
  const navigateTo = (hash: string) => {
    window.location.hash = hash;
  };

  return (
    <SpotlightCard className="p-6 flex flex-wrap items-center justify-between gap-4 text-slate-950 border-white/30 bg-white/[0.06] backdrop-blur-xl shadow-xl">
      <button
        type="button"
        onClick={() => navigateTo("")}
        className="inline-flex items-center gap-2 rounded-2xl border border-white/30 bg-white/10 px-4 py-2.5 text-xs font-black text-slate-950 shadow-xs transition-all hover:bg-white/20 cursor-pointer backdrop-blur-md"
      >
        <ArrowLeft className="h-4 w-4 text-sky-800" />
        <span>Back to Landing Page</span>
      </button>

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => navigateTo("dashboard")}
          className="inline-flex items-center gap-2 rounded-2xl border border-sky-400 bg-sky-600 px-5 py-2.5 text-xs font-black text-white shadow-md transition-all hover:bg-sky-700 cursor-pointer backdrop-blur-md"
        >
          <Activity className="h-4 w-4" />
          <span>Live Telemetry Dashboard</span>
        </button>

        <button
          type="button"
          onClick={() => navigateTo("prediction")}
          className="inline-flex items-center gap-2 rounded-2xl border border-indigo-400 bg-indigo-600 px-5 py-2.5 text-xs font-black text-white shadow-md transition-all hover:bg-indigo-700 cursor-pointer backdrop-blur-md"
        >
          <BrainCircuit className="h-4 w-4" />
          <span>AI Deep-Learning Prediction</span>
        </button>
      </div>
    </SpotlightCard>
  );
}
