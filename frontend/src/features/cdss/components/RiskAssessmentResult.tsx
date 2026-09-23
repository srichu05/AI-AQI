import type { CDSSAssessmentResponse } from "@/types/api";
import { Gauge } from "@/components/ui/gauge";
import { Activity, ShieldAlert, Stethoscope, Sparkles } from "lucide-react";
import { SpotlightCard } from "@/components/ui/spotlight-card";

export interface RiskAssessmentResultProps {
  assessment: CDSSAssessmentResponse;
}

export function RiskAssessmentResult({ assessment }: RiskAssessmentResultProps) {
  const getBadgeStyle = (risk: string) => {
    switch (risk.toLowerCase()) {
      case "high":
        return "border-rose-400 bg-rose-500 text-white shadow-rose-900/20";
      case "moderate":
        return "border-amber-400 bg-amber-500 text-white shadow-amber-900/20";
      case "low":
      default:
        return "border-emerald-400 bg-emerald-500 text-white shadow-emerald-900/20";
    }
  };

  return (
    <SpotlightCard className="p-6 md:p-8 space-y-6 text-slate-950 border-white/30 bg-white/[0.06] backdrop-blur-xl shadow-xl">
      {/* Header Info Banner */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/20 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-sky-800" />
            <h3 className="text-xl font-extrabold text-slate-950 tracking-tight drop-shadow-xs">
              Environmental Health Risk Evaluation
            </h3>
          </div>
          <p className="mt-1 text-xs font-bold text-slate-800">
            Synthesized assessment of ambient exposure and individual vulnerability dimensions
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="inline-flex items-center gap-1.5 rounded-full border border-white/30 bg-white/10 px-3 py-1 text-xs font-black text-slate-950 backdrop-blur-md">
            <Sparkles className="h-3.5 w-3.5 text-sky-800" />
            <span>Mode: {assessment.mode === "dl_integrated" ? "DL-Integrated" : "Rule-Based"}</span>
          </div>
          {assessment.assessment_id && (
            <span className="text-xs font-black text-slate-900">
              ID: #{assessment.assessment_id}
            </span>
          )}
        </div>
      </div>

      {/* Grid: Gauge + 3 Risk Dimension Cards */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-12 items-center">
        {/* Left Column: Composite Risk Gauge */}
        <div className="md:col-span-5 rounded-2xl border border-white/20 bg-white/[0.04] p-6 shadow-xs text-center space-y-3 backdrop-blur-md transition-all hover:border-white/40 hover:bg-white/[0.08]">
          <span className="text-xs font-extrabold uppercase tracking-wider text-slate-900">
            Overall Environmental Risk Index
          </span>
          <div className="mx-auto flex justify-center py-2">
            <Gauge
              value={Math.round(assessment.environmental_risk_index || 0)}
              size={200}
              label="CDSS Risk Index"
              unit="Index"
              activeColor="#0284c7"
              inactiveColor="rgba(14, 165, 233, 0.25)"
            />
          </div>
          <div className="inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/10 px-4 py-1.5 text-xs font-black uppercase tracking-wider shadow-md backdrop-blur-md">
            <span className={`h-2.5 w-2.5 rounded-full ${
              assessment.environmental_risk === "High" ? "bg-rose-500" :
              assessment.environmental_risk === "Moderate" ? "bg-amber-500" : "bg-emerald-500"
            }`} />
            <span className="text-slate-950 font-black">Overall: {assessment.environmental_risk}</span>
          </div>
        </div>

        {/* Right Column: 3 Risk Dimension Cards */}
        <div className="md:col-span-7 space-y-3">
          {/* 1. Overall Environmental Risk */}
          <div className="flex items-center justify-between rounded-2xl border border-white/20 bg-white/[0.04] p-4 shadow-xs backdrop-blur-md transition-all hover:border-white/40 hover:bg-white/[0.08]">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-sky-500/20 border border-sky-400/30 text-sky-800 shadow-xs">
                <ShieldAlert className="h-5 w-5" />
              </div>
              <div>
                <h4 className="text-sm font-black text-slate-950">Ambient Environmental Risk</h4>
                <p className="text-[11px] font-bold text-slate-800">Primary rule-based exposure classification</p>
              </div>
            </div>
            <span className={`rounded-xl border px-3 py-1 text-xs font-black shadow-xs ${getBadgeStyle(assessment.environmental_risk)}`}>
              {assessment.environmental_risk}
            </span>
          </div>

          {/* 2. Respiratory Environmental Risk */}
          <div className="flex items-center justify-between rounded-2xl border border-white/20 bg-white/[0.04] p-4 shadow-xs backdrop-blur-md transition-all hover:border-white/40 hover:bg-white/[0.08]">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-cyan-500/20 border border-cyan-400/30 text-cyan-800 shadow-xs">
                <Activity className="h-5 w-5" />
              </div>
              <div>
                <h4 className="text-sm font-black text-slate-950">Respiratory Environmental Risk</h4>
                <p className="text-[11px] font-bold text-slate-800">Personalized respiratory vulnerability stratification</p>
              </div>
            </div>
            <span className={`rounded-xl border px-3 py-1 text-xs font-black shadow-xs ${getBadgeStyle(assessment.respiratory_environmental_risk)}`}>
              {assessment.respiratory_environmental_risk}
            </span>
          </div>

          {/* 3. Skin Environmental Risk */}
          <div className="flex items-center justify-between rounded-2xl border border-white/20 bg-white/[0.04] p-4 shadow-xs backdrop-blur-md transition-all hover:border-white/40 hover:bg-white/[0.08]">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-500/20 border border-indigo-400/30 text-indigo-800 shadow-xs">
                <Stethoscope className="h-5 w-5" />
              </div>
              <div>
                <h4 className="text-sm font-black text-slate-950">Dermatological Skin Risk</h4>
                <p className="text-[11px] font-bold text-slate-800">Pollution-associated skin vulnerability stratification</p>
              </div>
            </div>
            <span className={`rounded-xl border px-3 py-1 text-xs font-black shadow-xs ${getBadgeStyle(assessment.skin_environmental_risk)}`}>
              {assessment.skin_environmental_risk}
            </span>
          </div>
        </div>
      </div>
    </SpotlightCard>
  );
}
