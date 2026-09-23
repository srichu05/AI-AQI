import { useState } from "react";
import { ShaderBackground } from "@/components/ui/oceanic-currents";
import { SpotlightCard } from "@/components/ui/spotlight-card";
import { PredictionInputWorkspace, type EnvironmentalInputData } from "../components/PredictionInputWorkspace";
import { PredictionProcessingState } from "../components/PredictionProcessingState";
import { PredictionResultWorkspace } from "../components/PredictionResultWorkspace";
import { predictAQI } from "@/api/predict";
import type { PredictionRequest, SinglePredictionResult } from "@/types/api";
import { AlertCircle, BrainCircuit, ShieldCheck } from "lucide-react";

export function PredictionPage() {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [predictionResult, setPredictionResult] = useState<SinglePredictionResult | null>(null);
  const [lastInput, setLastInput] = useState<EnvironmentalInputData | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleRunPrediction = async (inputData: EnvironmentalInputData) => {
    setIsLoading(true);
    setErrorMessage(null);
    setPredictionResult(null);
    setLastInput(inputData);

    try {
      // 1. Cyclical temporal encodings for dynamic features (indices 14..21)
      const now = new Date();
      const startOfYear = new Date(now.getFullYear(), 0, 0);
      const diff = now.getTime() - startOfYear.getTime();
      const doy = Math.floor(diff / (1000 * 60 * 60 * 24)) || 180;
      const month = now.getMonth() + 1;
      const dow = now.getDay();
      const hour = now.getHours();

      const doySin = Math.sin((2 * Math.PI * doy) / 365.25);
      const doyCos = Math.cos((2 * Math.PI * doy) / 365.25);
      const monSin = Math.sin((2 * Math.PI * month) / 12.0);
      const monCos = Math.cos((2 * Math.PI * month) / 12.0);
      const dowSin = Math.sin((2 * Math.PI * dow) / 7.0);
      const dowCos = Math.cos((2 * Math.PI * dow) / 7.0);

      // 2. Build canonical 24-feature vector per timestep matching data/dl/feature_groups.json
      const buildDynamicTimestep = (tIndex: number) => {
        const delta = (tIndex - 6) * 0.4;
        const tHour = (hour + (tIndex - 6) + 24) % 24;
        const hSin = Math.sin((2 * Math.PI * tHour) / 24.0);
        const hCos = Math.cos((2 * Math.PI * tHour) / 24.0);

        return [
          Math.max(0.5, inputData.pm25 + delta),      // 0: PM2.5 (µg/m³)
          Math.max(1.0, inputData.pm10 + delta * 1.5),// 1: PM10 (µg/m³)
          18.4,                                       // 2: NO2 (µg/m³)
          6.2,                                        // 3: SO2 (µg/m³)
          0.65,                                       // 4: CO (mg/m³)
          32.1,                                       // 5: O3 (µg/m³)
          0.28,                                       // 6: AOD (0 to 1)
          0.45,                                       // 7: NDVI (-1 to 1)
          inputData.temp,                             // 8: Temperature (°C)
          Math.max(0, Math.min(100, inputData.humidity)),// 9: Humidity (%)
          1012.5,                                     // 10: Pressure (hPa)
          3.2,                                        // 11: Wind_Speed (m/s)
          180.0,                                      // 12: Wind_Direction (0-360)
          0.0,                                        // 13: Rainfall (mm)
          doySin,                                     // 14: sin_day_of_year
          doyCos,                                     // 15: cos_day_of_year
          monSin,                                     // 16: sin_month
          monCos,                                     // 17: cos_month
          dowSin,                                     // 18: sin_day_of_week
          dowCos,                                     // 19: cos_day_of_week
          hSin,                                       // 20: sin_hour
          hCos,                                       // 21: cos_hour
          1.0,                                        // 22: boundary_flag
          1.0,                                        // 23: quality_score
        ];
      };

      const dynamicData = Array.from({ length: 7 }, (_, t) => buildDynamicTimestep(t));

      // 3. Derive GIS district coordinates & 16 static numerical features matching feature_groups.json
      const districtId = Math.max(0, Math.min(29, inputData.districtId));
      const lat = 12.80 + (districtId % 6) * 0.08;
      const lon = 77.45 + Math.floor(districtId / 6) * 0.08;
      const landUseId = districtId % 6;
      const urbanRuralId = districtId % 3;

      const staticNumData = [
        lat,                          // 0: latitude
        lon,                          // 1: longitude
        1.5,                          // 2: district_area
        20.0,                         // 3: population_density
        4.0,                          // 4: road_density
        0.35,                         // 5: green_cover (ratio 0-1)
        900.0,                        // 6: elevation (meters)
        landUseId === 1 ? 0.25 : 0.08,// 7: industrial_ratio (ratio 0-1)
        landUseId === 0 ? 0.35 : 0.12,// 8: commercial_ratio (ratio 0-1)
        landUseId === 2 ? 0.45 : 0.25,// 9: residential_ratio (ratio 0-1)
        0.08,                         // 10: water_body_ratio (ratio 0-1)
        1200.0,                       // 11: mean_annual_temp (°C)
        24.5,                         // 12: mean_annual_rain (mm)
        950.0,                        // 13: coastal_distance (km)
        250.0,                        // 14: forest_ratio (ratio 0-1)
        0.15,                         // 15: avg_traffic_volume
      ];

      const staticCatData = [districtId, landUseId, urbanRuralId];

      // 4. Pre-flight tensor contract assertions
      if (dynamicData.length !== 7 || dynamicData.some((row) => row.length !== 24)) {
        throw new Error("Pre-flight error: dynamic tensor must be shape (7, 24)");
      }
      if (staticNumData.length !== 16) {
        throw new Error("Pre-flight error: static_num array must contain 16 features");
      }
      if (staticCatData.length !== 3) {
        throw new Error("Pre-flight error: static_cat array must contain 3 categories");
      }

      const payload: PredictionRequest = {
        dynamic: { data: dynamicData },
        static_num: { data: staticNumData },
        static_cat: { data: staticCatData },
        device_id: "AI_AQI_NODE_01",
      };

      const response = await predictAQI(payload);
      if (response.success && response.prediction) {
        setPredictionResult(response.prediction);
      } else {
        setErrorMessage("Model returned an invalid response format.");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to execute DL model prediction.";
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen w-full bg-gradient-to-b from-[#528dcb] via-[#7db6e6] to-[#a4d2f5] text-white font-sans overflow-x-hidden pt-20 pb-6 md:pt-24 md:pb-10">
      {/* 1. Global Oceanic Currents WebGL Shader Background */}
      <ShaderBackground className="absolute inset-0 z-0 h-full w-full pointer-events-none" />

      {/* 2. Page Container Surface */}
      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Header Banner */}
        <SpotlightCard className="p-6 md:p-8 space-y-3 text-slate-900 border-white/60 bg-white/40 backdrop-blur-2xl">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-center gap-3.5">
              <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-sky-300 bg-sky-600 text-white shadow-md">
                <BrainCircuit className="h-6 w-6" />
              </div>
              <div>
                <h1 className="text-3xl font-black tracking-tight text-slate-900 md:text-4xl drop-shadow-xs">
                  AI Environmental Risk Prediction
                </h1>
                <p className="text-xs font-bold text-slate-700 mt-0.5">
                  Execute the official deep-learning AQI risk model against ground telemetry & meteorological inputs
                </p>
              </div>
            </div>

            <div className="inline-flex items-center gap-2 rounded-full border border-slate-300 bg-white/70 px-4 py-1.5 text-xs font-extrabold text-slate-800 backdrop-blur-md shadow-xs">
              <ShieldCheck className="h-4 w-4 text-sky-700" />
              <span>POST /predict REST API • Keras Checkpoint</span>
            </div>
          </div>
        </SpotlightCard>

        {/* Error Alert Banner if endpoint fails */}
        {errorMessage && (
          <div className="rounded-3xl border border-rose-400 bg-rose-100/90 p-4 text-rose-950 shadow-md flex items-center gap-3 text-xs font-bold">
            <AlertCircle className="h-5 w-5 text-rose-700 shrink-0" />
            <span>Prediction Error: {errorMessage}</span>
          </div>
        )}

        {/* Input Workspace */}
        <PredictionInputWorkspace
          onRunPrediction={handleRunPrediction}
          isLoading={isLoading}
        />

        {/* Processing Loading State */}
        {isLoading && <PredictionProcessingState />}

        {/* Results Workspace */}
        {predictionResult && !isLoading && (
          <PredictionResultWorkspace
            prediction={predictionResult}
            inputSummary={lastInput || undefined}
          />
        )}
      </div>
    </div>
  );
}
