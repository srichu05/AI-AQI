import type { CDSSAssessmentResponse } from "@/types/api";
import { Layers, Activity, Stethoscope, UserCheck } from "lucide-react";
import { SpotlightCard } from "@/components/ui/spotlight-card";

export interface ContributorsSectionProps {
  assessment: CDSSAssessmentResponse;
}

export function ContributorsSection({ assessment }: ContributorsSectionProps) {
  const envContribs = assessment.environmental_contributors || [];
  const respContribs = assessment.respiratory_contributors || [];
  const skinContribs = assessment.skin_contributors || [];
  const contextFactors = assessment.patient_context_factors || [];

  return (
    <SpotlightCard className="p-6 md:p-8 space-y-6 text-slate-950 border-white/30 bg-white/[0.06] backdrop-blur-xl shadow-xl">
      <div className="border-b border-white/20 pb-4">
        <div className="flex items-center gap-2">
          <Layers className="h-5 w-5 text-sky-800" />
          <h3 className="text-xl font-extrabold text-slate-950 tracking-tight drop-shadow-xs">
            Contributing Exposure & Vulnerability Factors
          </h3>
        </div>
        <p className="mt-1 text-xs font-bold text-slate-800">
          Specific environmental drivers and personal factors identified during CDSS rule evaluation
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* 1. Environmental Contributors */}
        <div className="space-y-3 rounded-2xl border border-white/20 bg-white/[0.04] p-4 shadow-xs backdrop-blur-md transition-all hover:border-white/40 hover:bg-white/[0.08]">
          <div className="flex items-center gap-2 text-xs font-black text-slate-950">
            <Layers className="h-4 w-4 text-sky-800" />
            <span>Environmental Pollutant Contributors</span>
          </div>
          {envContribs.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {envContribs.map((item, i) => (
                <span
                  key={i}
                  className="rounded-xl border border-white/30 bg-white/10 px-3 py-1.5 text-xs font-black text-slate-950 shadow-xs backdrop-blur-md"
                >
                  {item}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs font-bold text-slate-700 italic">No specific pollutant thresholds exceeded.</p>
          )}
        </div>

        {/* 2. Respiratory Contributors */}
        <div className="space-y-3 rounded-2xl border border-white/20 bg-white/[0.04] p-4 shadow-xs backdrop-blur-md transition-all hover:border-white/40 hover:bg-white/[0.08]">
          <div className="flex items-center gap-2 text-xs font-black text-slate-950">
            <Activity className="h-4 w-4 text-cyan-800" />
            <span>Respiratory Vulnerability Contributors</span>
          </div>
          {respContribs.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {respContribs.map((item, i) => (
                <span
                  key={i}
                  className="rounded-xl border border-white/30 bg-white/10 px-3 py-1.5 text-xs font-black text-slate-950 shadow-xs backdrop-blur-md"
                >
                  {item}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs font-bold text-slate-700 italic">No elevated respiratory risk factors identified.</p>
          )}
        </div>

        {/* 3. Skin Contributors */}
        <div className="space-y-3 rounded-2xl border border-white/20 bg-white/[0.04] p-4 shadow-xs backdrop-blur-md transition-all hover:border-white/40 hover:bg-white/[0.08]">
          <div className="flex items-center gap-2 text-xs font-black text-slate-950">
            <Stethoscope className="h-4 w-4 text-indigo-800" />
            <span>Dermatological Contributors</span>
          </div>
          {skinContribs.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {skinContribs.map((item, i) => (
                <span
                  key={i}
                  className="rounded-xl border border-white/30 bg-white/10 px-3 py-1.5 text-xs font-black text-slate-950 shadow-xs backdrop-blur-md"
                >
                  {item}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs font-bold text-slate-700 italic">No elevated dermatological risk factors identified.</p>
          )}
        </div>

        {/* 4. Patient Context Factors */}
        <div className="space-y-3 rounded-2xl border border-white/20 bg-white/[0.04] p-4 shadow-xs backdrop-blur-md transition-all hover:border-white/40 hover:bg-white/[0.08]">
          <div className="flex items-center gap-2 text-xs font-black text-slate-950">
            <UserCheck className="h-4 w-4 text-emerald-800" />
            <span>Patient Context Factors</span>
          </div>
          {contextFactors.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {contextFactors.map((item, i) => (
                <span
                  key={i}
                  className="rounded-xl border border-white/30 bg-white/10 px-3 py-1.5 text-xs font-black text-slate-950 shadow-xs backdrop-blur-md"
                >
                  {item}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs font-bold text-slate-700 italic">Standard context baseline.</p>
          )}
        </div>
      </div>
    </SpotlightCard>
  );
}
