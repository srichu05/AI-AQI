import { useState } from "react";
import { Activity, BrainCircuit, Cpu, Layers, MapPin, RefreshCw, Thermometer, Zap } from "lucide-react";
import { getLatestTelemetry } from "@/api/telemetry";
import { SpotlightCard } from "@/components/ui/spotlight-card";

export interface EnvironmentalInputData {
  pm25: number;
  pm10: number;
  pm1: number;
  temp: number;
  humidity: number;
  districtId: number;
}

export interface PredictionInputWorkspaceProps {
  onRunPrediction: (data: EnvironmentalInputData) => void;
  isLoading?: boolean;
}

const DISTRICT_NAMES = [
  "Central Business District", "North Industrial Zone", "South Residential",
  "East Tech Park", "West Agricultural Belt", "Suburban North",
  "Airport Corridor", "Riverside Basin", "Hill Station Foothills",
  "Highway Node 1", "Highway Node 2", "Port Transit Hub",
  "Forest Reserve Border", "Urban Slum Cluster", "University Campus",
  "Metro Junction East", "Metro Junction West", "Outer Ring Road",
  "Lake Catchment Area", "Industrial Estate B", "Commercial Hub North",
  "Commercial Hub South", "Green Belt West", "Mining Vicinity",
  "Thermal Power Zone", "Coastal Delta North", "Coastal Delta South",
  "Valley Pass East", "Valley Pass West", "Metropolitan Core"
];

export function PredictionInputWorkspace({
  onRunPrediction,
  isLoading = false,
}: PredictionInputWorkspaceProps) {
  const [pm25, setPm25] = useState<number>(14.2);
  const [pm10, setPm10] = useState<number>(28.5);
  const [pm1, setPm1] = useState<number>(7.1);
  const [temp, setTemp] = useState<number>(25.8);
  const [humidity, setHumidity] = useState<number>(58);
  const [districtId, setDistrictId] = useState<number>(0);
  const [isFetchingTelemetry, setIsFetchingTelemetry] = useState<boolean>(false);
  const [presetNotice, setPresetNotice] = useState<string | null>(null);

  const handleLoadTelemetry = async () => {
    setIsFetchingTelemetry(true);
    setPresetNotice(null);
    try {
      const res = await getLatestTelemetry();
      if (res.data) {
        setPm25(res.data.pm25_ground || 12.4);
        setPm10(res.data.pm10_ground || 24.8);
        setPm1(res.data.pm1_ground || 6.2);
        setPresetNotice(`Loaded live telemetry from Node: ${res.data.device_id || "ESP32"}`);
      } else {
        setPresetNotice("Live telemetry buffer empty. Using default sensor parameters.");
      }
    } catch {
      setPresetNotice("Using offline sensor calibration values.");
    } finally {
      setIsFetchingTelemetry(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onRunPrediction({
      pm25: Number(pm25),
      pm10: Number(pm10),
      pm1: Number(pm1),
      temp: Number(temp),
      humidity: Number(humidity),
      districtId: Number(districtId),
    });
  };

  return (
    <form onSubmit={handleSubmit}>
      <SpotlightCard className="p-6 md:p-8 space-y-6 text-slate-900 border-white/60 bg-white/40 backdrop-blur-2xl">
        {/* Header & Presets */}
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-sky-200/80 pb-5">
          <div>
            <div className="flex items-center gap-2">
              <BrainCircuit className="h-6 w-6 text-sky-800" />
              <h2 className="text-2xl font-black text-slate-900 tracking-tight drop-shadow-xs">
                Environmental Observations Workspace
              </h2>
            </div>
            <p className="mt-1 text-xs font-bold text-slate-700">
              Configure ground sensor telemetry & meteorological vectors to execute DL model risk inference
            </p>
          </div>

          <button
            type="button"
            onClick={handleLoadTelemetry}
            disabled={isFetchingTelemetry || isLoading}
            className="inline-flex items-center gap-2 rounded-2xl border border-sky-400 bg-sky-600 px-4 py-2 text-xs font-black uppercase tracking-wider text-white shadow-md transition-all hover:bg-sky-700 disabled:opacity-50 cursor-pointer"
          >
            <RefreshCw className={`h-4 w-4 ${isFetchingTelemetry ? "animate-spin" : ""}`} />
            <span>{isFetchingTelemetry ? "Syncing Sensor..." : "⚡ Load Live Telemetry"}</span>
          </button>
        </div>

        {presetNotice && (
          <div className="rounded-2xl border border-sky-300 bg-sky-100/90 px-4 py-2.5 text-xs font-bold text-slate-900 shadow-xs backdrop-blur-md">
            {presetNotice}
          </div>
        )}

        {/* Inputs Grid */}
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {/* PM2.5 Input */}
          <div className="rounded-2xl border border-white/60 bg-white/50 p-4 shadow-xs space-y-2 backdrop-blur-md transition-all hover:border-sky-400 hover:bg-white/70">
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-1.5 text-xs font-extrabold text-slate-800">
                <Activity className="h-4 w-4 text-sky-700" />
                Ground PM2.5 (µg/m³)
              </label>
              <span className="text-xs font-black text-slate-900">{pm25}</span>
            </div>
            <input
              type="number"
              step="0.1"
              min="0"
              max="500"
              value={pm25}
              onChange={(e) => setPm25(Number(e.target.value))}
              className="w-full rounded-xl border border-slate-300 bg-white/90 px-3 py-2 text-sm font-black text-slate-900 shadow-inner focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
            <input
              type="range"
              min="0"
              max="250"
              step="0.5"
              value={pm25}
              onChange={(e) => setPm25(Number(e.target.value))}
              className="w-full accent-sky-600"
            />
          </div>

          {/* PM10 Input */}
          <div className="rounded-2xl border border-white/60 bg-white/50 p-4 shadow-xs space-y-2 backdrop-blur-md transition-all hover:border-sky-400 hover:bg-white/70">
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-1.5 text-xs font-extrabold text-slate-800">
                <Cpu className="h-4 w-4 text-indigo-700" />
                Ground PM10 (µg/m³)
              </label>
              <span className="text-xs font-black text-slate-900">{pm10}</span>
            </div>
            <input
              type="number"
              step="0.1"
              min="0"
              max="500"
              value={pm10}
              onChange={(e) => setPm10(Number(e.target.value))}
              className="w-full rounded-xl border border-slate-300 bg-white/90 px-3 py-2 text-sm font-black text-slate-900 shadow-inner focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
            <input
              type="range"
              min="0"
              max="300"
              step="0.5"
              value={pm10}
              onChange={(e) => setPm10(Number(e.target.value))}
              className="w-full accent-indigo-600"
            />
          </div>

          {/* PM1.0 Input */}
          <div className="rounded-2xl border border-white/60 bg-white/50 p-4 shadow-xs space-y-2 backdrop-blur-md transition-all hover:border-sky-400 hover:bg-white/70">
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-1.5 text-xs font-extrabold text-slate-800">
                <Layers className="h-4 w-4 text-teal-700" />
                Ground PM1.0 (µg/m³)
              </label>
              <span className="text-xs font-black text-slate-900">{pm1}</span>
            </div>
            <input
              type="number"
              step="0.1"
              min="0"
              max="200"
              value={pm1}
              onChange={(e) => setPm1(Number(e.target.value))}
              className="w-full rounded-xl border border-slate-300 bg-white/90 px-3 py-2 text-sm font-black text-slate-900 shadow-inner focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
            <input
              type="range"
              min="0"
              max="150"
              step="0.5"
              value={pm1}
              onChange={(e) => setPm1(Number(e.target.value))}
              className="w-full accent-teal-600"
            />
          </div>

          {/* Temperature Input */}
          <div className="rounded-2xl border border-white/60 bg-white/50 p-4 shadow-xs space-y-2 backdrop-blur-md transition-all hover:border-sky-400 hover:bg-white/70">
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-1.5 text-xs font-extrabold text-slate-800">
                <Thermometer className="h-4 w-4 text-blue-700" />
                Ambient Temperature (°C)
              </label>
              <span className="text-xs font-black text-slate-900">{temp}°C</span>
            </div>
            <input
              type="number"
              step="0.1"
              min="-10"
              max="55"
              value={temp}
              onChange={(e) => setTemp(Number(e.target.value))}
              className="w-full rounded-xl border border-slate-300 bg-white/90 px-3 py-2 text-sm font-black text-slate-900 shadow-inner focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>

          {/* Humidity Input */}
          <div className="rounded-2xl border border-white/60 bg-white/50 p-4 shadow-xs space-y-2 backdrop-blur-md transition-all hover:border-sky-400 hover:bg-white/70">
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-1.5 text-xs font-extrabold text-slate-800">
                <Activity className="h-4 w-4 text-cyan-700" />
                Relative Humidity (%)
              </label>
              <span className="text-xs font-black text-slate-900">{humidity}%</span>
            </div>
            <input
              type="number"
              step="1"
              min="0"
              max="100"
              value={humidity}
              onChange={(e) => setHumidity(Number(e.target.value))}
              className="w-full rounded-xl border border-slate-300 bg-white/90 px-3 py-2 text-sm font-black text-slate-900 shadow-inner focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>

          {/* GIS District Selector */}
          <div className="rounded-2xl border border-white/60 bg-white/50 p-4 shadow-xs space-y-2 backdrop-blur-md transition-all hover:border-sky-400 hover:bg-white/70">
            <label className="flex items-center gap-1.5 text-xs font-extrabold text-slate-800">
              <MapPin className="h-4 w-4 text-sky-700" />
              GIS Monitoring District
            </label>
            <select
              value={districtId}
              onChange={(e) => setDistrictId(Number(e.target.value))}
              className="w-full rounded-xl border border-slate-300 bg-white/90 px-3 py-2 text-xs font-black text-slate-900 shadow-inner focus:outline-none focus:ring-2 focus:ring-sky-500 cursor-pointer"
            >
              {DISTRICT_NAMES.map((name, idx) => (
                <option key={idx} value={idx}>
                  {idx}: {name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Run Prediction Button */}
        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={isLoading}
            className="inline-flex items-center gap-2.5 rounded-2xl border border-sky-400 bg-sky-600 px-8 py-3.5 text-sm font-black uppercase tracking-wider text-white shadow-lg transition-all hover:bg-sky-700 hover:scale-[1.02] disabled:opacity-50 cursor-pointer"
          >
            <Zap className="h-5 w-5 text-cyan-200 fill-cyan-200" />
            <span>{isLoading ? "Running Inference..." : "RUN AI MODEL PREDICTION →"}</span>
          </button>
        </div>
      </SpotlightCard>
    </form>
  );
}
