import type { PatientProfile } from "@/types/api";
import { User, Activity, MapPin, Stethoscope, Sparkles } from "lucide-react";
import { SpotlightCard } from "@/components/ui/spotlight-card";

export interface PatientContextFormProps {
  patientProfile: PatientProfile;
  onChangeProfile: (profile: PatientProfile) => void;
  onEvaluate: () => void;
  isLoading: boolean;
}

export function PatientContextForm({
  patientProfile,
  onChangeProfile,
  onEvaluate,
  isLoading,
}: PatientContextFormProps) {
  // Enforce strict condition-severity alignment rules
  const handleRespiratoryConditionChange = (cond: PatientProfile["respiratory_condition"]) => {
    if (cond === "none") {
      onChangeProfile({
        ...patientProfile,
        respiratory_condition: "none",
        respiratory_severity: "none",
      });
    } else {
      const sev = patientProfile.respiratory_severity === "none" ? "moderate" : patientProfile.respiratory_severity;
      onChangeProfile({
        ...patientProfile,
        respiratory_condition: cond,
        respiratory_severity: sev,
      });
    }
  };

  const handleSkinConditionChange = (cond: PatientProfile["skin_condition"]) => {
    if (cond === "none") {
      onChangeProfile({
        ...patientProfile,
        skin_condition: "none",
        skin_severity: "none",
      });
    } else {
      const sev = patientProfile.skin_severity === "none" ? "moderate" : patientProfile.skin_severity;
      onChangeProfile({
        ...patientProfile,
        skin_condition: cond,
        skin_severity: sev,
      });
    }
  };

  return (
    <SpotlightCard className="p-6 md:p-8 space-y-6 text-slate-950 border-white/30 bg-white/[0.06] backdrop-blur-xl shadow-xl">
      <div className="border-b border-white/20 pb-4">
        <div className="flex items-center gap-2">
          <User className="h-5 w-5 text-sky-800" />
          <h3 className="text-xl font-extrabold text-slate-950 tracking-tight drop-shadow-xs">
            Personal Vulnerability & Exposure Context
          </h3>
        </div>
        <p className="mt-1 text-xs font-bold text-slate-800">
          Individual demographic, behavioral, and clinical context for personalized risk stratification
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* 1. Age & Smoking Status */}
        <div className="space-y-4 rounded-2xl border border-white/20 bg-white/[0.04] p-4 shadow-xs backdrop-blur-md transition-all hover:border-white/40 hover:bg-white/[0.08]">
          <div className="flex items-center gap-2 text-xs font-black text-slate-950">
            <User className="h-4 w-4 text-sky-800" />
            <span>Demographic & Behavioral Profile</span>
          </div>

          {/* Age Slider */}
          <div className="space-y-1">
            <div className="flex items-center justify-between text-xs font-extrabold text-slate-900">
              <label htmlFor="patient-age-input">Patient Age</label>
              <span className="font-black text-slate-950 text-sm">{patientProfile.age} yrs</span>
            </div>
            <input
              id="patient-age-input"
              type="range"
              min="0"
              max="120"
              value={patientProfile.age}
              onChange={(e) => onChangeProfile({ ...patientProfile, age: Number(e.target.value) })}
              className="w-full h-2 bg-white/20 rounded-lg appearance-none cursor-pointer accent-sky-600"
            />
          </div>

          {/* Smoking Status Pills */}
          <div className="space-y-1.5">
            <label className="text-xs font-extrabold text-slate-900">Smoking History</label>
            <div className="grid grid-cols-3 gap-2">
              {(["never", "former", "current"] as const).map((status) => (
                <button
                  key={status}
                  type="button"
                  onClick={() => onChangeProfile({ ...patientProfile, smoking_status: status })}
                  className={`rounded-xl border py-2 text-xs font-black capitalize transition-all cursor-pointer ${
                    patientProfile.smoking_status === status
                      ? "border-sky-400 bg-sky-600 text-white shadow-sm"
                      : "border-white/25 bg-white/10 text-slate-950 hover:bg-white/20 backdrop-blur-md"
                  }`}
                >
                  {status}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* 2. Geographic Location */}
        <div className="space-y-4 rounded-2xl border border-white/20 bg-white/[0.04] p-4 shadow-xs backdrop-blur-md transition-all hover:border-white/40 hover:bg-white/[0.08]">
          <div className="flex items-center gap-2 text-xs font-black text-slate-950">
            <MapPin className="h-4 w-4 text-emerald-800" />
            <span>Geographic Coordinates (GIS Node)</span>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label htmlFor="patient-lat-input" className="text-xs font-extrabold text-slate-900">Latitude</label>
              <input
                id="patient-lat-input"
                type="number"
                step="0.01"
                min="-90"
                max="90"
                value={patientProfile.latitude}
                onChange={(e) => onChangeProfile({ ...patientProfile, latitude: Number(e.target.value) })}
                className="w-full rounded-xl border border-white/25 bg-white/10 px-3 py-1.5 text-xs font-black text-slate-950 shadow-inner focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white/20"
              />
            </div>
            <div className="space-y-1">
              <label htmlFor="patient-lon-input" className="text-xs font-extrabold text-slate-900">Longitude</label>
              <input
                id="patient-lon-input"
                type="number"
                step="0.01"
                min="-180"
                max="180"
                value={patientProfile.longitude}
                onChange={(e) => onChangeProfile({ ...patientProfile, longitude: Number(e.target.value) })}
                className="w-full rounded-xl border border-white/25 bg-white/10 px-3 py-1.5 text-xs font-black text-slate-950 shadow-inner focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white/20"
              />
            </div>
          </div>
          <p className="text-[11px] font-bold text-slate-800">
            Coordinates match active GIS monitoring node for environmental exposure mapping
          </p>
        </div>

        {/* 3. Respiratory Clinical Context */}
        <div className="space-y-4 rounded-2xl border border-white/20 bg-white/[0.04] p-4 shadow-xs backdrop-blur-md transition-all hover:border-white/40 hover:bg-white/[0.08]">
          <div className="flex items-center gap-2 text-xs font-black text-slate-950">
            <Activity className="h-4 w-4 text-cyan-800" />
            <span>Respiratory Clinical Context</span>
          </div>

          <div className="space-y-1.5">
            <label htmlFor="respiratory-condition-select" className="text-xs font-extrabold text-slate-900">Pre-existing Condition</label>
            <select
              id="respiratory-condition-select"
              value={patientProfile.respiratory_condition}
              onChange={(e) => handleRespiratoryConditionChange(e.target.value as PatientProfile["respiratory_condition"])}
              className="w-full rounded-xl border border-white/25 bg-slate-900/90 text-white px-3 py-2 text-xs font-black shadow-inner focus:outline-none focus:ring-2 focus:ring-sky-500 cursor-pointer"
            >
              <option value="none">None (No pre-existing respiratory diagnosis)</option>
              <option value="asthma">Asthma</option>
              <option value="copd">COPD (Chronic Obstructive Pulmonary Disease)</option>
              <option value="other">Other Respiratory Condition</option>
            </select>
          </div>

          {/* Severity (Disabled if condition is None) */}
          <div className="space-y-1.5">
            <label className="text-xs font-extrabold text-slate-900">
              Condition Severity
              {patientProfile.respiratory_condition === "none" && (
                <span className="ml-2 text-[10px] font-bold text-slate-600">(N/A - Condition is None)</span>
              )}
            </label>
            <div className="grid grid-cols-4 gap-1.5">
              {(["none", "mild", "moderate", "severe"] as const).map((sev) => {
                const isDisabled = patientProfile.respiratory_condition === "none" ? sev !== "none" : sev === "none";
                return (
                  <button
                    key={sev}
                    type="button"
                    disabled={isDisabled}
                    onClick={() => onChangeProfile({ ...patientProfile, respiratory_severity: sev })}
                    className={`rounded-xl border py-1.5 text-[11px] font-black capitalize transition-all cursor-pointer ${
                      patientProfile.respiratory_severity === sev
                        ? "border-sky-400 bg-sky-600 text-white shadow-sm"
                        : "border-white/25 bg-white/10 text-slate-950 hover:bg-white/20 disabled:opacity-30 backdrop-blur-md"
                    }`}
                  >
                    {sev}
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* 4. Dermatological / Skin Context */}
        <div className="space-y-4 rounded-2xl border border-white/20 bg-white/[0.04] p-4 shadow-xs backdrop-blur-md transition-all hover:border-white/40 hover:bg-white/[0.08]">
          <div className="flex items-center gap-2 text-xs font-black text-slate-950">
            <Stethoscope className="h-4 w-4 text-indigo-800" />
            <span>Dermatological / Skin Context</span>
          </div>

          <div className="space-y-1.5">
            <label htmlFor="skin-condition-select" className="text-xs font-extrabold text-slate-900">Pre-existing Skin Condition</label>
            <select
              id="skin-condition-select"
              value={patientProfile.skin_condition}
              onChange={(e) => handleSkinConditionChange(e.target.value as PatientProfile["skin_condition"])}
              className="w-full rounded-xl border border-white/25 bg-slate-900/90 text-white px-3 py-2 text-xs font-black shadow-inner focus:outline-none focus:ring-2 focus:ring-sky-500 cursor-pointer"
            >
              <option value="none">None (No pre-existing dermatological diagnosis)</option>
              <option value="eczema">Eczema (Atopic Dermatitis)</option>
              <option value="dermatitis">Contact Dermatitis</option>
              <option value="other">Other Skin Condition</option>
            </select>
          </div>

          {/* Severity (Disabled if condition is None) */}
          <div className="space-y-1.5">
            <label className="text-xs font-extrabold text-slate-900">
              Condition Severity
              {patientProfile.skin_condition === "none" && (
                <span className="ml-2 text-[10px] font-bold text-slate-600">(N/A - Condition is None)</span>
              )}
            </label>
            <div className="grid grid-cols-4 gap-1.5">
              {(["none", "mild", "moderate", "severe"] as const).map((sev) => {
                const isDisabled = patientProfile.skin_condition === "none" ? sev !== "none" : sev === "none";
                return (
                  <button
                    key={sev}
                    type="button"
                    disabled={isDisabled}
                    onClick={() => onChangeProfile({ ...patientProfile, skin_severity: sev })}
                    className={`rounded-xl border py-1.5 text-[11px] font-black capitalize transition-all cursor-pointer ${
                      patientProfile.skin_severity === sev
                        ? "border-sky-400 bg-sky-600 text-white shadow-sm"
                        : "border-white/25 bg-white/10 text-slate-950 hover:bg-white/20 disabled:opacity-30 backdrop-blur-md"
                    }`}
                  >
                    {sev}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Primary Action Button */}
      <div className="pt-2 text-center">
        <button
          type="button"
          onClick={onEvaluate}
          disabled={isLoading}
          className="inline-flex items-center gap-2 rounded-2xl border border-sky-400 bg-sky-600 px-8 py-3.5 text-sm font-black uppercase tracking-wider text-white shadow-lg transition-all hover:bg-sky-700 hover:scale-[1.02] disabled:opacity-50 cursor-pointer"
        >
          <Sparkles className="h-5 w-5 text-cyan-200" />
          <span>{isLoading ? "Evaluating Rules..." : "EVALUATE ENVIRONMENTAL HEALTH RISK →"}</span>
        </button>
      </div>
    </SpotlightCard>
  );
}
