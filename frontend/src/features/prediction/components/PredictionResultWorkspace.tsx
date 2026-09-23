import type { SinglePredictionResult } from "@/types/api";
import { Gauge } from "@/components/ui/gauge";
import { Activity, ArrowRight, ShieldAlert, ShieldCheck, Sparkles, MapPin } from "lucide-react";
import type { EnvironmentalInputData } from "./PredictionInputWorkspace";
import { SpotlightCard } from "@/components/ui/spotlight-card";

export interface PredictionResultWorkspaceProps {
  prediction: SinglePredictionResult;
  inputSummary?: EnvironmentalInputData;
}

const CLASS_NAMES = ["Low", "Moderate", "Unhealthy", "Very Unhealthy", "Severe"];

export function PredictionResultWorkspace({
  prediction,
  inputSummary,
}: PredictionResultWorkspaceProps) {
  const probabilities = prediction.probabilities || [0.8, 0.15, 0.03, 0.02];
  const maxProb = Math.max(...probabilities);
  const confidencePercent = Math.round(maxProb * 100);

  const getRiskBadge = (label: string) => {
    const l = label.toLowerCase();
    if (l.includes("low") || l.includes("good")) {
      return { bg: "bg-emerald-300/80 border-emerald-500/60 text-emerald-950", icon: ShieldCheck };
    }
    if (l.includes("mod")) {
      return { bg: "bg-amber-300/80 border-amber-500/60 text-amber-950", icon: Activity };
    }
    return { bg: "bg-rose-300/80 border-rose-500/60 text-rose-950", icon: ShieldAlert };
  };

  const badge = getRiskBadge(prediction.risk_label);

  return (
    <SpotlightCard className="p-6 md:p-8 space-y-8 animate-in fade-in duration-300 text-slate-900 border-white/60 bg-white/40 backdrop-blur-2xl">
      {/* 1. Result Title & Badges */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-sky-200/80 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-sky-800" />
            <h2 className="text-2xl font-black text-slate-900 tracking-tight drop-shadow-xs">
              AI Prediction Output
            </h2>
          </div>
          <p className="mt-1 text-xs font-bold text-slate-700">
            Validated DL model risk class, probability distribution & confidence evaluation
          </p>
        </div>

        <div className="flex items-center gap-2">
          <span className={`rounded-full border px-4 py-1.5 text-xs font-black uppercase tracking-wider backdrop-blur-md shadow-xs ${badge.bg}`}>
            {prediction.risk_label}
          </span>
          <span className="rounded-full border border-sky-300 bg-sky-100/90 px-3.5 py-1.5 text-xs font-black text-slate-900">
            Class {prediction.risk_class}
          </span>
        </div>
      </div>

      {/* 2. Middle Row: Gauge Confidence + Probability Distribution */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Risk Confidence Gauge */}
        <div className="flex flex-col items-center justify-center rounded-3xl border border-white/60 bg-white/50 p-6 shadow-md text-center backdrop-blur-md transition-all hover:border-sky-400 hover:bg-white/70">
          <h4 className="text-xs font-extrabold text-slate-800 uppercase tracking-wider mb-2">
            Model Confidence
          </h4>
          <Gauge
            value={confidencePercent}
            totalNotches={36}
            size={200}
            strokeWidth={15}
            label="Model Confidence"
            unit="%"
            activeColor="#0284c7"
            inactiveColor="rgba(14, 165, 233, 0.25)"
          />
          <p className="mt-2 text-[11px] font-black text-slate-900">
            Top Class Probability: {confidencePercent}%
          </p>
        </div>

        {/* Probability Breakdown */}
        <div className="lg:col-span-2 rounded-3xl border border-white/60 bg-white/50 p-6 shadow-md space-y-4 backdrop-blur-md transition-all hover:border-sky-400 hover:bg-white/70">
          <h4 className="text-xs font-extrabold text-slate-800 uppercase tracking-wider">
            Calibrated Class Probabilities
          </h4>

          <div className="space-y-3">
            {probabilities.map((prob, idx) => {
              const label = CLASS_NAMES[idx] || `Class ${idx}`;
              const pct = (prob * 100).toFixed(1);
              const isSelected = idx === prediction.risk_class;

              return (
                <div key={idx} className="space-y-1">
                  <div className="flex items-center justify-between text-xs font-bold">
                    <span className={isSelected ? "text-slate-900 font-black" : "text-slate-700 font-medium"}>
                      {label} {isSelected && "(Predicted)"}
                    </span>
                    <span className="text-slate-900 font-mono font-bold">{pct}%</span>
                  </div>
                  <div className="h-2.5 w-full overflow-hidden rounded-full bg-sky-100/80 border border-sky-300/60">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        isSelected ? "bg-sky-600 shadow-sm" : "bg-sky-400/60"
                      }`}
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* 3. Factual Environmental Input Summary Table */}
      {inputSummary && (
        <div className="rounded-3xl border border-white/60 bg-white/50 p-6 shadow-md space-y-3 backdrop-blur-md transition-all hover:border-sky-400 hover:bg-white/70">
          <h4 className="text-xs font-extrabold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
            <Activity className="h-4 w-4 text-sky-700" />
            Environmental Inputs Executed
          </h4>

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6 text-center">
            <div className="rounded-2xl border border-sky-300/80 bg-white/70 p-3">
              <p className="text-[10px] font-bold text-slate-700">PM2.5</p>
              <p className="text-base font-black text-slate-900">{inputSummary.pm25} µg/m³</p>
            </div>
            <div className="rounded-2xl border border-sky-300/80 bg-white/70 p-3">
              <p className="text-[10px] font-bold text-slate-700">PM10</p>
              <p className="text-base font-black text-slate-900">{inputSummary.pm10} µg/m³</p>
            </div>
            <div className="rounded-2xl border border-sky-300/80 bg-white/70 p-3">
              <p className="text-[10px] font-bold text-slate-700">PM1.0</p>
              <p className="text-base font-black text-slate-900">{inputSummary.pm1} µg/m³</p>
            </div>
            <div className="rounded-2xl border border-sky-300/80 bg-white/70 p-3">
              <p className="text-[10px] font-bold text-slate-700">Temperature</p>
              <p className="text-base font-black text-slate-900">{inputSummary.temp} °C</p>
            </div>
            <div className="rounded-2xl border border-sky-300/80 bg-white/70 p-3">
              <p className="text-[10px] font-bold text-slate-700">Humidity</p>
              <p className="text-base font-black text-slate-900">{inputSummary.humidity} %</p>
            </div>
            <div className="rounded-2xl border border-sky-300/80 bg-white/70 p-3">
              <p className="text-[10px] font-bold text-slate-700">District ID</p>
              <p className="text-base font-black text-slate-900 flex items-center justify-center gap-1">
                <MapPin className="h-3.5 w-3.5 text-sky-700" />
                {inputSummary.districtId}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 4. Transition to Next System Actions */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-t border-sky-200/80 pt-6">
        <div>
          <h4 className="text-sm font-black text-slate-900">Next System Actions</h4>
          <p className="text-xs font-bold text-slate-700">
            Explore live sensor streams or evaluate clinical health risk decision support
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <a
            href="#dashboard"
            className="inline-flex items-center gap-2 rounded-2xl border border-sky-300/80 bg-white/60 px-4 py-2 text-xs font-black uppercase tracking-wider text-slate-900 hover:bg-white/80 transition-all shadow-xs backdrop-blur-md"
          >
            <span>Live Dashboard</span>
          </a>
          <a
            href="#cdss"
            className="inline-flex items-center gap-2 rounded-2xl border border-sky-400 bg-sky-600 px-5 py-2 text-xs font-black uppercase tracking-wider text-white shadow-md hover:bg-sky-700 transition-all backdrop-blur-md"
          >
            <span>Continue to Environmental Health Risk →</span>
            <ArrowRight className="h-4 w-4" />
          </a>
        </div>
      </div>
    </SpotlightCard>
  );
}
