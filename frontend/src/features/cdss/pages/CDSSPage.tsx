import { useState } from "react";
import WavyBackground from "@/components/ui/blue-meshy-background";
import { GradientBackground } from "@/components/ui/bloom-field-gradient";
import { CDSSHeader } from "../components/CDSSHeader";
import { EnvironmentalExposureSummary } from "../components/EnvironmentalExposureSummary";
import { PatientContextForm } from "../components/PatientContextForm";
import { CDSSProcessingState } from "../components/CDSSProcessingState";
import { RiskAssessmentResult } from "../components/RiskAssessmentResult";
import { ContributorsSection } from "../components/ContributorsSection";
import { RecommendationsSection } from "../components/RecommendationsSection";
import { CDSSDisclaimer } from "../components/CDSSDisclaimer";
import { NextActionsNav } from "../components/NextActionsNav";
import { assessCDSSRisk } from "@/api/cdss";
import type {
  CDSSAssessmentRequest,
  CDSSAssessmentResponse,
  EnvironmentalReadings,
  PatientProfile,
} from "@/types/api";
import { AlertCircle } from "lucide-react";

export function CDSSPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [assessmentResult, setAssessmentResult] = useState<CDSSAssessmentResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Environmental Exposure State
  const [environmentalData, setEnvironmentalData] = useState<EnvironmentalReadings>({
    pm25: 24.5,
    pm10: 48.2,
    no2: 18.4,
    o3: 32.1,
    so2: 6.2,
    co: 0.65,
  });

  // Patient Context Profile State
  const [patientProfile, setPatientProfile] = useState<PatientProfile>({
    age: 45,
    smoking_status: "never",
    respiratory_condition: "asthma",
    respiratory_severity: "moderate",
    skin_condition: "none",
    skin_severity: "none",
    latitude: 12.97,
    longitude: 77.59,
  });

  const handleEvaluateCDSS = async () => {
    setIsLoading(true);
    setErrorMessage(null);
    setAssessmentResult(null);

    // Client-side condition-severity alignment validation before HTTP POST
    if (patientProfile.respiratory_condition === "none" && patientProfile.respiratory_severity !== "none") {
      setErrorMessage("Respiratory severity must be 'none' when respiratory condition is 'none'.");
      setIsLoading(false);
      return;
    }
    if (patientProfile.respiratory_condition !== "none" && patientProfile.respiratory_severity === "none") {
      setErrorMessage("Please select a respiratory severity (mild, moderate, severe) for your condition.");
      setIsLoading(false);
      return;
    }
    if (patientProfile.skin_condition === "none" && patientProfile.skin_severity !== "none") {
      setErrorMessage("Skin severity must be 'none' when skin condition is 'none'.");
      setIsLoading(false);
      return;
    }
    if (patientProfile.skin_condition !== "none" && patientProfile.skin_severity === "none") {
      setErrorMessage("Please select a skin severity (mild, moderate, severe) for your condition.");
      setIsLoading(false);
      return;
    }

    try {
      const payload: CDSSAssessmentRequest = {
        patient: patientProfile,
        environmental: environmentalData,
      };

      const res = await assessCDSSRisk(payload);
      setAssessmentResult(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to execute CDSS assessment.";
      setErrorMessage(msg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <WavyBackground className="min-h-screen w-full bg-gradient-to-b from-[#1b365d] via-[#3876ba] to-[#528dcb] text-white font-sans pt-20 pb-6 md:pt-24 md:pb-10">
      {/* Atmosphere Bloom Layer */}
      <div className="absolute inset-0 z-0 opacity-40 pointer-events-none">
        <GradientBackground />
      </div>

      {/* Page Container Surface */}
      <div className="relative z-10 mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Header */}
        <CDSSHeader />

        {/* Error Alert Banner */}
        {errorMessage && (
          <div className="rounded-3xl border border-rose-400 bg-rose-100/90 p-4 text-rose-950 shadow-md flex items-center gap-3 text-xs font-bold">
            <AlertCircle className="h-5 w-5 text-rose-700 shrink-0" />
            <span>Assessment Validation / System Error: {errorMessage}</span>
          </div>
        )}

        {/* Environmental Exposure Summary */}
        <EnvironmentalExposureSummary
          environmentalData={environmentalData}
          onChangeEnvironmentalData={setEnvironmentalData}
        />

        {/* Patient Vulnerability Context Form */}
        <PatientContextForm
          patientProfile={patientProfile}
          onChangeProfile={setPatientProfile}
          onEvaluate={handleEvaluateCDSS}
          isLoading={isLoading}
        />

        {/* Loading Processing State */}
        {isLoading && <CDSSProcessingState />}

        {/* Results Workspace */}
        {assessmentResult && !isLoading && (
          <div className="space-y-8 animate-fadeIn">
            {/* Risk Category Dimensions & Gauge */}
            <RiskAssessmentResult assessment={assessmentResult} />

            {/* Contributing Risk Factors */}
            <ContributorsSection assessment={assessmentResult} />

            {/* Personalized Recommendations */}
            <RecommendationsSection assessment={assessmentResult} />

            {/* Legal Non-Diagnostic Notice */}
            <CDSSDisclaimer disclaimer={assessmentResult.disclaimer} />

            {/* Navigation Actions */}
            <NextActionsNav />
          </div>
        )}
      </div>
    </WavyBackground>
  );
}
