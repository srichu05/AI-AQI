import { AlertTriangle } from "lucide-react";
import { SpotlightCard } from "@/components/ui/spotlight-card";

export interface CDSSDisclaimerProps {
  disclaimer: string;
}

export function CDSSDisclaimer({ disclaimer }: CDSSDisclaimerProps) {
  return (
    <SpotlightCard
      spotlightColor="rgba(251, 191, 36, 0.25)"
      className="border-amber-400/40 bg-amber-500/20 p-5 shadow-lg flex items-start gap-3 text-amber-950 backdrop-blur-xl"
    >
      <AlertTriangle className="h-5 w-5 text-amber-800 shrink-0 mt-0.5" />
      <div className="space-y-1">
        <h5 className="text-xs font-black uppercase tracking-wider text-amber-950">
          Non-Diagnostic Clinical & Legal Notice
        </h5>
        <p className="text-xs font-extrabold leading-relaxed text-amber-950">
          {disclaimer}
        </p>
      </div>
    </SpotlightCard>
  );
}
