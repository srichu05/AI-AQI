import { Gauge } from "@/components/ui/gauge";
import { LiquidGlassCard } from "@/components/ui/liquid-weather-glass";
import { ShieldCheck, Info } from "lucide-react";

export interface RiskGaugeSectionProps {
  aqiValue?: number;
}

export function RiskGaugeSection({ aqiValue = 42 }: RiskGaugeSectionProps) {
  const getRiskCategory = (val: number) => {
    if (val <= 50) return { label: "Good", color: "text-emerald-200", bg: "bg-emerald-500/30 border-emerald-400/50" };
    if (val <= 100) return { label: "Moderate", color: "text-amber-200", bg: "bg-amber-500/30 border-amber-400/50" };
    if (val <= 150) return { label: "Unhealthy for Sensitive", color: "text-orange-200", bg: "bg-orange-500/30 border-orange-400/50" };
    return { label: "Hazardous", color: "text-rose-200", bg: "bg-rose-500/30 border-rose-400/50" };
  };

  const risk = getRiskCategory(aqiValue);

  return (
    <LiquidGlassCard
      shadowIntensity="sm"
      glowIntensity="xs"
      borderRadius="24px"
      draggable={false}
      className="flex flex-col justify-between p-6 bg-white/[0.04] text-white backdrop-blur-md border border-white/15 h-full"
    >
      {/* Header */}
      <div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-sky-300" />
            <h3 className="text-xl font-extrabold text-white tracking-tight drop-shadow-sm">
              Environmental Risk Index
            </h3>
          </div>
          <span className={`rounded-full border px-3 py-1 text-[10px] font-black uppercase tracking-wider backdrop-blur-md shadow-xs ${risk.bg} ${risk.color}`}>
            {risk.label}
          </span>
        </div>
        <p className="mt-1 text-xs font-medium text-white/90">
          Calibrated Ground Telemetry + Open-Meteo Multi-Variable Index
        </p>
      </div>

      {/* Radial Bklit Gauge */}
      <div className="my-auto flex justify-center py-4">
        <Gauge
          value={aqiValue}
          totalNotches={36}
          size={210}
          strokeWidth={15}
          label="US EPA Scale"
          unit="AQI"
          activeColor="#38bdf8"
          inactiveColor="rgba(255, 255, 255, 0.2)"
        />
      </div>

      {/* Advisory Note */}
      <div className="rounded-2xl border border-white/15 bg-white/[0.05] p-3.5 text-[11px] font-medium text-white/95 flex items-start gap-2 backdrop-blur-md">
        <Info className="h-4 w-4 text-sky-300 shrink-0 mt-0.5" />
        <span>
          Air quality is satisfactory. Air pollution poses little or no risk to general outdoor clinical activity.
        </span>
      </div>
    </LiquidGlassCard>
  );
}

