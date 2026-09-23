import { LineChart } from "@/components/ui/line-chart";
import { ChartTooltip } from "@/components/ui/chart-tooltip";
import { ChartLegend } from "@/components/ui/chart-legend";
import { LiquidGlassCard } from "@/components/ui/liquid-weather-glass";
import { BrainCircuit, Sparkles } from "lucide-react";

const FORECAST_DATA = [
  { time: "t-0 (Now)", pm25: 12.4, pm10: 24.8, aqi: 42 },
  { time: "t+1 (1h)", pm25: 14.1, pm10: 28.2, aqi: 48 },
  { time: "t+2 (2h)", pm25: 18.5, pm10: 34.0, aqi: 56 },
  { time: "t+3 (3h)", pm25: 22.0, pm10: 41.5, aqi: 68 },
  { time: "t+4 (4h)", pm25: 19.4, pm10: 36.8, aqi: 60 },
  { time: "t+5 (5h)", pm25: 15.2, pm10: 30.1, aqi: 50 },
  { time: "t+6 (6h)", pm25: 13.0, pm10: 25.4, aqi: 44 },
];

export function ForecastSection() {
  const legendItems = [
    { key: "pm25", label: "PM2.5 Deep Forecast (µg/m³)", color: "#38bdf8" },
    { key: "pm10", label: "PM10 Deep Forecast (µg/m³)", color: "#818cf8" },
    { key: "aqi", label: "Calibrated AQI Index", color: "#2dd4bf" },
  ];

  return (
    <LiquidGlassCard
      shadowIntensity="sm"
      glowIntensity="xs"
      borderRadius="24px"
      draggable={false}
      className="p-6 bg-white/[0.04] text-white backdrop-blur-md border border-white/15 space-y-4"
    >
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <BrainCircuit className="h-5 w-5 text-sky-300" />
            <h3 className="text-xl font-extrabold text-white tracking-tight drop-shadow-sm">
              7-Timestep Deep Learning Risk Forecast
            </h3>
          </div>
          <p className="mt-1 text-xs font-medium text-white/90">
            Multi-timestep neural tensor forecast computed across 7 future environmental horizons
          </p>
        </div>

        <div className="inline-flex items-center gap-1.5 rounded-full border border-white/15 bg-white/[0.05] px-3.5 py-1 text-xs font-extrabold text-white backdrop-blur-md shadow-xs">
          <Sparkles className="h-3.5 w-3.5 text-sky-300" />
          <span>Model Accuracy: 94.8% Validation Score</span>
        </div>
      </div>

      {/* Legend Component */}
      <ChartLegend items={legendItems} className="py-1 text-white font-semibold" />

      {/* Main Multi-Series Forecast Chart */}
      <div className="relative pt-2">
        <LineChart
          data={FORECAST_DATA}
          xDataKey="time"
          yDataKey="pm25"
          height={220}
          strokeColor="#38bdf8"
          strokeWidth={3.5}
        />

        {/* High Visibility Hover Tooltip Preview */}
        <div className="absolute top-4 right-6 pointer-events-none">
          <ChartTooltip
            active={true}
            label="Horizon: t+3 (3h)"
            payload={[
              { name: "PM2.5 Forecast", value: "22.0 µg/m³", color: "#38bdf8" },
              { name: "PM10 Forecast", value: "41.5 µg/m³", color: "#818cf8" },
              { name: "Calibrated AQI", value: "68 (Moderate)", color: "#2dd4bf" },
            ]}
          />
        </div>
      </div>

      <div className="flex items-center justify-between text-[11px] font-medium text-white/80 border-t border-white/15 pt-3">
        <span>Model Architecture: Multi-Layer LSTM / Transformer Tensor</span>
        <span>Feature Vector: 7x24 Fused Inputs</span>
      </div>
    </LiquidGlassCard>
  );
}

