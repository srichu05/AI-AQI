import { Globe, Database } from "lucide-react";

export function GISHeader() {
  return (
    <div className="rounded-3xl border border-white/30 bg-white/15 p-6 md:p-7 backdrop-blur-3xl shadow-xl shadow-sky-950/10 space-y-2">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-sky-300/40 bg-sky-600/90 text-white shadow-md">
            <Globe className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-2xl font-black tracking-tight text-sky-950 md:text-3xl drop-shadow-xs">
              GIS Spatial Environmental Risk Intelligence
            </h1>
            <p className="text-xs font-bold text-sky-900 mt-0.5">
              Karnataka-wide spatial risk distribution backed by the AI-AQI ML dataset
            </p>
          </div>
        </div>

        <div className="inline-flex items-center gap-2 rounded-full border border-sky-300/60 bg-white/40 px-3.5 py-1.5 text-xs font-black text-sky-950 backdrop-blur-md shadow-xs">
          <Database className="h-3.5 w-3.5 text-sky-700" />
          <span>dataset_ml_ready.csv • 65,760 Records • 30 Districts</span>
        </div>
      </div>
    </div>
  );
}
