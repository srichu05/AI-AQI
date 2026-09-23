import { useState, useEffect, useCallback } from "react";
import { GradientBackground } from "@/components/ui/bloom-field-gradient";
import { LiquidGlassCard } from "@/components/ui/liquid-weather-glass";
import { SensorMetricsRow } from "../components/SensorMetricsRow";
import { LiveTelemetrySection } from "../components/LiveTelemetrySection";
import { RiskGaugeSection } from "../components/RiskGaugeSection";
import { ForecastSection } from "../components/ForecastSection";
import { getLatestTelemetry, getTelemetryHistory } from "@/api/telemetry";
import type { TelemetryRecord } from "@/types/api";
import type { TelemetryPoint } from "@/components/ui/telemetry-area-chart";
import {
  Activity,
  ArrowLeft,
  ShieldCheck,
  UserCheck,
  MapPin,
  Cloud,
  CloudSun,
  CloudRain,
  CloudSunRain,
  Thermometer,
} from "lucide-react";


export interface DashboardPageProps {
  onBackToLanding?: () => void;
}

export function DashboardPage({ onBackToLanding }: DashboardPageProps) {
  const [timeStr, setTimeStr] = useState<string>("");
  const [dateStr, setDateStr] = useState<string>("");

  // Real Telemetry State
  const [latestRecord, setLatestRecord] = useState<TelemetryRecord | null>(null);
  const [telemetryHistory, setTelemetryHistory] = useState<TelemetryPoint[]>([]);
  const [telemetryState, setTelemetryState] = useState<"connected" | "waiting" | "error" | "stale">("waiting");
  const [lastUpdatedText, setLastUpdatedText] = useState<string>("");

  const formatPointTime = (timestampStr: string | null | undefined): string => {
    if (!timestampStr) return "00:00:00";
    try {
      const d = new Date(timestampStr);
      if (isNaN(d.getTime())) return "00:00:00";
      return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });
    } catch {
      return "00:00:00";
    }
  };

  const transformRecordToPoint = (r: TelemetryRecord): TelemetryPoint => ({
    id: r.id,
    time: formatPointTime(r.timestamp_utc || r.created_at),
    timestamp_raw: r.timestamp_utc || r.created_at,
    pm1: Number(r.pm1_ground || 0),
    pm25: Number(r.pm25_ground || 0),
    pm10: Number(r.pm10_ground || 0),
  });

  const checkStaleness = useCallback((record: TelemetryRecord | null) => {
    if (!record || (!record.timestamp_utc && !record.created_at)) return "waiting";
    const ts = new Date(record.timestamp_utc || record.created_at || "").getTime();
    if (isNaN(ts)) return "connected";
    const diffSec = (Date.now() - ts) / 1000;
    if (diffSec > 300) {
      const mins = Math.floor(diffSec / 60);
      setLastUpdatedText(`${mins}m ago`);
      return "stale";
    }
    return "connected";
  }, []);

  const pollLatest = useCallback(async () => {
    try {
      const res = await getLatestTelemetry();
      if (res && res.data) {
        const rec = res.data;
        setLatestRecord(rec);
        const st = checkStaleness(rec);
        setTelemetryState(st);

        const newPoint = transformRecordToPoint(rec);
        setTelemetryHistory((prev) => {
          if (prev.length === 0) return [newPoint];
          const last = prev[prev.length - 1];
          if (rec.id && last.id === rec.id) return prev;
          if (rec.timestamp_utc && last.timestamp_raw === rec.timestamp_utc) return prev;

          const updated = [...prev, newPoint];
          return updated.slice(-30);
        });
      } else {
        if (telemetryHistory.length === 0) {
          setTelemetryState("waiting");
        }
      }
    } catch {
      if (telemetryHistory.length === 0) {
        setTelemetryState("error");
      }
    }
  }, [checkStaleness, telemetryHistory.length]);

  const loadInitialHistory = useCallback(async () => {
    try {
      const res = await getTelemetryHistory(30);
      if (res && res.data && res.data.length > 0) {
        const points = res.data.map(transformRecordToPoint);
        setTelemetryHistory(points);
        const lastRec = res.data[res.data.length - 1];
        setLatestRecord(lastRec);
        setTelemetryState(checkStaleness(lastRec));
      } else {
        pollLatest();
      }
    } catch {
      pollLatest();
    }
  }, [checkStaleness, pollLatest]);

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      setTimeStr(
        now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      );
      setDateStr(
        now.toLocaleDateString("en-US", {
          weekday: "short",
          month: "short",
          day: "numeric",
        })
      );
    };
    updateTime();
    const timeInterval = setInterval(updateTime, 1000);

    loadInitialHistory();
    const pollInterval = setInterval(pollLatest, 5000);
    return () => {
      clearInterval(timeInterval);
      clearInterval(pollInterval);
    };
  }, [loadInitialHistory, pollLatest]);

  return (
    <div
      className="relative min-h-screen w-full text-white font-sans overflow-x-hidden pt-20 pb-6 md:pt-24 md:pb-10 bg-slate-900"
      style={{
        background:
          'linear-gradient(rgba(15, 23, 42, 0.4), rgba(15, 23, 42, 0.5)), url("https://images.unsplash.com/photo-1590867286251-8e26d9f255c0?q=80&w=2000&auto=format&fit=crop") center / cover no-repeat fixed',
      }}
    >
      {/* Dynamic Ambient Bloom Background */}
      <div className="absolute inset-0 z-0 opacity-40 pointer-events-none">
        <GradientBackground />
      </div>

      {/* Main Glassmorphic Container */}
      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 space-y-6">
        
        {/* Header Bar */}
        <LiquidGlassCard
          shadowIntensity="md"
          glowIntensity="sm"
          borderRadius="28px"
          draggable={false}
          className="bg-white/[0.04] p-6 md:p-8 text-white backdrop-blur-md border border-white/15"
        >
          <header className="flex flex-wrap items-center justify-between gap-4 border-b border-white/15 pb-6">
            {/* Navigation & Node Indicator */}
            <div className="flex flex-wrap items-center gap-3">
              <button
                type="button"
                onClick={onBackToLanding}
                className="inline-flex items-center gap-2 rounded-2xl border border-white/20 bg-white/10 px-4 py-2 text-xs font-black uppercase tracking-wider text-white hover:bg-white/20 transition-all shadow-xs backdrop-blur-md cursor-pointer"
              >
                <ArrowLeft className="h-4 w-4 text-sky-200" />
                <span>Back to Overview</span>
              </button>

              <div className="h-5 w-px bg-white/20 hidden sm:block" />

              <div className="flex items-center gap-2 rounded-full border border-emerald-400/40 bg-emerald-500/15 px-3.5 py-1.5 text-xs font-bold text-emerald-200 backdrop-blur-md shadow-xs">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <span>Node: AI_AQI_NODE_01 (ONLINE)</span>
              </div>
            </div>

            {/* Status Badges */}
            <div className="flex items-center gap-3">
              <div className="hidden md:flex items-center gap-2 text-xs font-semibold text-white/90">
                <Activity className="h-4 w-4 text-sky-300" />
                <span>Live Sensor Ingestion Active</span>
              </div>

              <div className="flex items-center gap-2 rounded-2xl border border-white/20 bg-white/10 px-3.5 py-1.5 text-xs font-bold text-white shadow-xs backdrop-blur-md">
                <UserCheck className="h-4 w-4 text-sky-300" />
                <span>Authenticated Session</span>
              </div>
            </div>
          </header>

          {/* Title & Banner */}
          <div className="mt-6 flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-black tracking-tight text-white md:text-4xl drop-shadow-md">
                AI-AQI Live Intelligence Dashboard
              </h1>
              <p className="mt-1.5 text-sm font-semibold text-sky-100/90">
                Real-time ESP32 sensor telemetry, Open-Meteo fusion, and deep-learning AQI forecasts
              </p>
            </div>

            <div className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-1.5 text-xs font-bold text-white backdrop-blur-md shadow-xs">
              <ShieldCheck className="h-4 w-4 text-sky-300" />
              <span>FastAPI JWT Verified • PostgreSQL Storage</span>
            </div>
          </div>
        </LiquidGlassCard>

        {/* Liquid Weather & Ambient Widgets Row (4 Cards Placed in a Line) */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* 1. Hourly Atmospheric Forecast Card */}
          <LiquidGlassCard
            shadowIntensity="xs"
            borderRadius="24px"
            glowIntensity="none"
            draggable={false}
            className="p-6 text-white bg-white/[0.04] backdrop-blur-md border border-white/15 flex flex-col justify-between"
          >
            <h4 className="text-xs font-bold uppercase tracking-wider text-white/80 mb-3">Hourly Forecast</h4>
            <div className="grid grid-cols-6 gap-1 text-xs font-medium text-center">
              <div className="flex flex-col items-center gap-1.5 p-1 rounded-xl bg-white/[0.03]">
                <span className="text-[10px] text-white/80">16:00</span>
                <Cloud className="h-4 w-4 fill-white text-white" />
                <span className="font-bold text-[11px]">+18°</span>
              </div>
              <div className="flex flex-col items-center gap-1.5 p-1 rounded-xl bg-white/[0.03]">
                <span className="text-[10px] text-white/80">17:00</span>
                <Cloud className="h-4 w-4 fill-white text-white" />
                <span className="font-bold text-[11px]">+18°</span>
              </div>
              <div className="flex flex-col items-center gap-1.5 p-1 rounded-xl bg-white/[0.03]">
                <span className="text-[10px] text-white/80">18:00</span>
                <CloudRain className="h-4 w-4 text-sky-300" />
                <span className="font-bold text-[11px]">+16°</span>
              </div>
              <div className="flex flex-col items-center gap-1.5 p-1 rounded-xl bg-white/[0.03]">
                <span className="text-[10px] text-white/80">19:00</span>
                <CloudRain className="h-4 w-4 text-sky-300" />
                <span className="font-bold text-[11px]">+14°</span>
              </div>
              <div className="flex flex-col items-center gap-1.5 p-1 rounded-xl bg-white/[0.03]">
                <span className="text-[10px] text-white/80">20:00</span>
                <CloudSun className="h-4 w-4 fill-white text-white" />
                <span className="font-bold text-[11px]">+15°</span>
              </div>
              <div className="flex flex-col items-center gap-1.5 p-1 rounded-xl bg-white/[0.03]">
                <span className="text-[10px] text-white/80">21:00</span>
                <CloudSunRain className="h-4 w-4 text-sky-300" />
                <span className="font-bold text-[11px]">+14°</span>
              </div>
            </div>
          </LiquidGlassCard>

          {/* 2. Current Weather & AQI Summary Card */}
          <LiquidGlassCard
            shadowIntensity="xs"
            borderRadius="24px"
            glowIntensity="none"
            draggable={false}
            className="p-6 text-white bg-white/[0.04] backdrop-blur-md border border-white/15 flex flex-col items-start justify-center"
          >
            <div className="flex items-baseline gap-2.5">
              <span className="text-4xl font-black tracking-tight">+18°C</span>
              <span className="rounded-full bg-emerald-500/25 border border-emerald-400/40 px-2.5 py-0.5 text-[11px] font-bold text-emerald-200">
                AQI 42 • Good
              </span>
            </div>
            <div className="mt-2 text-xs text-white/90 font-medium flex items-center gap-2">
              <CloudSun className="h-4 w-4 text-sky-200" />
              <span>Partly Cloudy • High +18° / Low +5°</span>
            </div>
          </LiquidGlassCard>

          {/* 3. Time & Location Station Card */}
          <LiquidGlassCard
            shadowIntensity="xs"
            borderRadius="24px"
            glowIntensity="none"
            draggable={false}
            className="p-6 text-white bg-white/[0.04] backdrop-blur-md border border-white/15 flex flex-col items-start justify-center"
          >
            <div className="text-4xl font-black tracking-tight">{timeStr || "15:10"}</div>
            <div className="text-xs font-medium text-white/90 mt-1">{dateStr || "Wed, Aug 26"}</div>
            <button className="mt-2.5 inline-flex items-center gap-1 rounded-full bg-white/10 backdrop-blur-md px-2.5 py-1 text-[10px] font-bold text-white border border-white/20">
              <MapPin className="h-3 w-3 text-sky-300" />
              <span className="truncate">Node Station • Bengaluru</span>
            </button>
          </LiquidGlassCard>

          {/* 4. Ambient Temp & RH Card (Moved Next to Time Card in 4-Card Line) */}
          <LiquidGlassCard
            shadowIntensity="xs"
            borderRadius="24px"
            glowIntensity="none"
            draggable={false}
            className="p-6 text-white bg-white/[0.04] backdrop-blur-md border border-white/15 flex flex-col justify-between"
          >
            <div className="flex items-center justify-between">
              <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/20 bg-white/10 text-white shadow-xs backdrop-blur-md">
                <Thermometer className="h-5 w-5 text-sky-300" />
              </div>
              <span className="rounded-full border border-sky-400/40 bg-sky-400/30 px-3 py-1 text-[10px] font-black uppercase tracking-wider text-sky-100 backdrop-blur-md shadow-xs">
                Normal
              </span>
            </div>

            <div>
              <p className="text-xs font-black uppercase tracking-wider text-white/80">Ambient Temp & RH</p>
              <p className="text-2xl lg:text-3xl font-black text-white tracking-tight drop-shadow-sm mt-1">26.5 °C / 62%</p>
            </div>
          </LiquidGlassCard>
        </div>

        {/* 1. Live Sensor Metric Cards */}
        <SensorMetricsRow
          pm25={latestRecord?.pm25_ground}
          pm10={latestRecord?.pm10_ground}
          pm1={latestRecord?.pm1_ground}
          isStale={telemetryState === "stale"}
        />

        {/* 2. Middle Row: Live Stream Chart + AQI Gauge */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <LiveTelemetrySection
              telemetryHistory={telemetryHistory}
              telemetryState={telemetryState}
              latestRecord={latestRecord}
              lastUpdatedText={lastUpdatedText}
              deviceId={latestRecord?.device_id || "AI_AQI_NODE_01"}
              onRetry={loadInitialHistory}
            />
          </div>
          <div className="lg:col-span-1">
            <RiskGaugeSection aqiValue={latestRecord ? Math.round(latestRecord.pm25_ground * 2.5) : 42} />
          </div>
        </div>

        {/* 3. Bottom Row: 7-Timestep Deep Forecast */}
        <ForecastSection />

      </div>
    </div>
  );
}
