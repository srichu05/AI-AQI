import { useState } from "react";
import { LiquidGlassCard } from "@/components/ui/liquid-weather-glass";
import { TelemetryAreaChart, type TelemetryPoint } from "@/components/ui/telemetry-area-chart";
import type { TelemetryRecord } from "@/types/api";
import { Radio, Layers, AlertCircle, RefreshCw, Clock } from "lucide-react";

export interface LiveTelemetrySectionProps {
  telemetryHistory: TelemetryPoint[];
  telemetryState: "connected" | "waiting" | "error" | "stale";
  latestRecord?: TelemetryRecord | null;
  lastUpdatedText?: string;
  deviceId?: string;
  onRetry?: () => void;
}

export function LiveTelemetrySection({
  telemetryHistory = [],
  telemetryState = "waiting",
  latestRecord,
  lastUpdatedText,
  deviceId = "AI_AQI_NODE_01",
  onRetry,
}: LiveTelemetrySectionProps) {
  const [mode, setMode] = useState<"live" | "area">("live");

  return (
    <LiquidGlassCard
      shadowIntensity="sm"
      glowIntensity="xs"
      borderRadius="24px"
      draggable={false}
      className="flex flex-col justify-between p-6 bg-white/[0.04] text-white backdrop-blur-md border border-white/15 h-full"
    >
      {/* Header Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
        <div>
          <div className="flex items-center gap-2">
            <Radio className="h-5 w-5 text-sky-300" />
            <h3 className="text-xl font-extrabold text-white tracking-tight drop-shadow-sm">
              Real-Time Particulate Telemetry
            </h3>
          </div>
          <p className="mt-1 text-xs font-medium text-white/90">
            Hardware PMS3003 particulate telemetry from Node {latestRecord?.device_id || deviceId}
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Status Indicator Badge */}
          {telemetryState === "connected" && (
            <div className="inline-flex items-center gap-1.5 rounded-full border border-emerald-400/40 bg-emerald-500/20 px-3 py-1 text-[11px] font-extrabold text-emerald-300 backdrop-blur-md shadow-xs">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span>LIVE STREAM</span>
            </div>
          )}

          {telemetryState === "stale" && (
            <div className="inline-flex items-center gap-1.5 rounded-full border border-amber-400/40 bg-amber-500/20 px-3 py-1 text-[11px] font-extrabold text-amber-200 backdrop-blur-md shadow-xs">
              <Clock className="h-3.5 w-3.5 text-amber-300" />
              <span>STALE ({lastUpdatedText || "Old reading"})</span>
            </div>
          )}

          {telemetryState === "waiting" && (
            <div className="inline-flex items-center gap-1.5 rounded-full border border-sky-400/40 bg-sky-500/20 px-3 py-1 text-[11px] font-extrabold text-sky-200 backdrop-blur-md shadow-xs">
              <RefreshCw className="h-3.5 w-3.5 animate-spin text-sky-300" />
              <span>WAITING FOR SENSOR</span>
            </div>
          )}

          {telemetryState === "error" && (
            <div className="inline-flex items-center gap-1.5 rounded-full border border-rose-400/40 bg-rose-500/20 px-3 py-1 text-[11px] font-extrabold text-rose-200 backdrop-blur-md shadow-xs">
              <AlertCircle className="h-3.5 w-3.5 text-rose-300" />
              <span>TELEMETRY UNREACHABLE</span>
            </div>
          )}

          {/* Chart View Selector */}
          <div className="flex items-center gap-1 rounded-2xl border border-white/15 bg-white/[0.05] p-1 backdrop-blur-md">
            <button
              type="button"
              onClick={() => setMode("live")}
              className={`rounded-xl px-3 py-1.5 text-xs font-bold transition-all ${
                mode === "live"
                  ? "bg-white text-sky-950 shadow-md"
                  : "text-white/80 hover:text-white"
              }`}
            >
              Live Stream
            </button>
            <button
              type="button"
              onClick={() => setMode("area")}
              className={`rounded-xl px-3 py-1.5 text-xs font-bold transition-all ${
                mode === "area"
                  ? "bg-white text-sky-950 shadow-md"
                  : "text-white/80 hover:text-white"
              }`}
            >
              Gradient View
            </button>
          </div>
        </div>
      </div>

      {/* 3-Series Legend Bar */}
      <div className="flex flex-wrap items-center gap-4 mb-3 px-1 text-xs font-bold">
        <span className="flex items-center gap-1.5 text-teal-300">
          <span className="h-2.5 w-2.5 rounded-full bg-[#2dd4bf] shadow-xs" />
          PM1.0 (µg/m³)
        </span>
        <span className="flex items-center gap-1.5 text-sky-300">
          <span className="h-2.5 w-2.5 rounded-full bg-[#38bdf8] shadow-xs" />
          PM2.5 (µg/m³)
        </span>
        <span className="flex items-center gap-1.5 text-purple-300">
          <span className="h-2.5 w-2.5 rounded-full bg-[#a855f7] shadow-xs" />
          PM10 (µg/m³)
        </span>
      </div>

      {/* Main Chart Area or Conditional State Overlays */}
      <div className="w-full pt-1 min-h-[240px] flex flex-col justify-center">
        {telemetryState === "error" ? (
          <div className="rounded-2xl border border-rose-500/30 bg-rose-950/20 p-8 text-center backdrop-blur-md space-y-3">
            <AlertCircle className="mx-auto h-8 w-8 text-rose-400" />
            <h4 className="text-base font-extrabold text-rose-100">Telemetry Service Unavailable</h4>
            <p className="text-xs font-medium text-rose-200/80 max-w-md mx-auto">
              Unable to connect to backend telemetry service. Please ensure FastAPI server is active.
            </p>
            {onRetry && (
              <button
                type="button"
                onClick={onRetry}
                className="mt-2 inline-flex items-center gap-1.5 rounded-xl bg-rose-600 px-4 py-1.5 text-xs font-bold text-white hover:bg-rose-500 transition-all shadow-md"
              >
                <RefreshCw className="h-3.5 w-3.5" />
                Retry Connection
              </button>
            )}
          </div>
        ) : telemetryState === "waiting" || telemetryHistory.length === 0 ? (
          <div className="rounded-2xl border border-white/20 bg-white/[0.03] p-8 text-center backdrop-blur-md space-y-3">
            <RefreshCw className="mx-auto h-8 w-8 text-sky-300 animate-spin" />
            <h4 className="text-base font-extrabold text-white">Waiting for PMS3003 Sensor Telemetry...</h4>
            <p className="text-xs font-medium text-sky-100/80 max-w-md mx-auto">
              Hardware node is not transmitting readings. Power on the ESP32 node to stream real sensor data.
            </p>
          </div>
        ) : (
          <TelemetryAreaChart data={telemetryHistory} height={240} />
        )}
      </div>

      {/* Footer Info */}
      <div className="mt-4 flex items-center justify-between border-t border-white/15 pt-3 text-[11px] font-medium text-white/80">
        <span className="flex items-center gap-1">
          <Layers className="h-3.5 w-3.5 text-sky-300" />
          Sampling Rate: 5.0s (Live PostgreSQL Stream)
        </span>
        <span>Sensor: PMS3003 Laser Scatter</span>
      </div>
    </LiquidGlassCard>
  );
}
