import type { CDSSAssessmentResponse } from "@/types/api";
import { CheckCircle2, ShieldAlert } from "lucide-react";
import { SpotlightCard } from "@/components/ui/spotlight-card";

export interface RecommendationsSectionProps {
  assessment: CDSSAssessmentResponse;
}

export function RecommendationsSection({ assessment }: RecommendationsSectionProps) {
  const recommendations = assessment.recommendations || [];

  return (
    <SpotlightCard className="p-6 md:p-8 space-y-6 text-slate-950 border-white/30 bg-white/[0.06] backdrop-blur-xl shadow-xl">
      <div className="border-b border-white/20 pb-4">
        <div className="flex items-center gap-2">
          <ShieldAlert className="h-5 w-5 text-sky-800" />
          <h3 className="text-xl font-extrabold text-slate-950 tracking-tight drop-shadow-xs">
            Actionable Preventive Environmental Guidance
          </h3>
        </div>
        <p className="mt-1 text-xs font-bold text-slate-800">
          Non-prescriptive preventive recommendations tailored to active environmental risk dimensions
        </p>
      </div>

      <div className="space-y-3">
        {recommendations.length > 0 ? (
          recommendations.map((rec, i) => (
            <div
              key={i}
              className="flex items-start gap-3 rounded-2xl border border-white/20 bg-white/[0.04] p-4 shadow-xs transition-all hover:border-white/40 hover:bg-white/[0.08] backdrop-blur-md"
            >
              <CheckCircle2 className="h-5 w-5 text-emerald-700 shrink-0 mt-0.5" />
              <p className="text-xs font-black text-slate-950 leading-relaxed">
                {rec}
              </p>
            </div>
          ))
        ) : (
          <div className="rounded-2xl border border-white/20 bg-white/[0.04] p-4 text-xs font-bold text-slate-950 text-center backdrop-blur-md">
            No specific preventive actions required. Maintain standard activities while observing local air quality.
          </div>
        )}
      </div>
    </SpotlightCard>
  );
}
