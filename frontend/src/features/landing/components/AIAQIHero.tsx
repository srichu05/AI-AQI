import { useState, useRef, useEffect, useCallback } from "react";
import { CloudShader } from "@/components/ui/cloud-shader";
import type { TargetSample } from "@/components/ui/cloud-shader";
import { Sparkles, ArrowRight, ShieldCheck, Activity, MapPin, Stethoscope } from "lucide-react";

export function AIAQIHero() {
  const heroRef = useRef<HTMLElement>(null);
  const paragraphRef = useRef<HTMLParagraphElement>(null);
  const buttonRef = useRef<HTMLAnchorElement>(null);
  
  // Independent refs for the 4 micro-feature items
  const featCDSSRef = useRef<HTMLSpanElement>(null);
  const featESPRef = useRef<HTMLSpanElement>(null);
  const featGISRef = useRef<HTMLSpanElement>(null);
  const featHealthRef = useRef<HTMLSpanElement>(null);

  const [samples, setSamples] = useState<TargetSample[]>([]);
  const [brightnessMap, setBrightnessMap] = useState<Record<string, boolean>>({});

  // Recalculate normalized element coordinates for instant localized cloud edge detection
  const updateSamplePoints = useCallback(() => {
    const heroEl = heroRef.current;
    if (!heroEl) return;
    const heroRect = heroEl.getBoundingClientRect();
    if (heroRect.width === 0 || heroRect.height === 0) return;

    const newSamples: TargetSample[] = [];

    // 1. Paragraph multi-point sampling (5 points across width for instant edge detection)
    if (paragraphRef.current) {
      const r = paragraphRef.current.getBoundingClientRect();
      const relY = (r.top + r.height * 0.5 - heroRect.top) / heroRect.height;
      newSamples.push(
        { id: "p1", x: (r.left + r.width * 0.15 - heroRect.left) / heroRect.width, y: relY },
        { id: "p2", x: (r.left + r.width * 0.325 - heroRect.left) / heroRect.width, y: relY },
        { id: "p3", x: (r.left + r.width * 0.50 - heroRect.left) / heroRect.width, y: relY },
        { id: "p4", x: (r.left + r.width * 0.675 - heroRect.left) / heroRect.width, y: relY },
        { id: "p5", x: (r.left + r.width * 0.85 - heroRect.left) / heroRect.width, y: relY }
      );
    }

    // 2. Secondary CTA Button sampling (left and right edge points)
    if (buttonRef.current) {
      const r = buttonRef.current.getBoundingClientRect();
      const relY = (r.top + r.height * 0.5 - heroRect.top) / heroRect.height;
      newSamples.push(
        { id: "btn1", x: (r.left + r.width * 0.3 - heroRect.left) / heroRect.width, y: relY },
        { id: "btn2", x: (r.left + r.width * 0.7 - heroRect.left) / heroRect.width, y: relY }
      );
    }

    // Micro-features sampling (center points of each feature item)
    const getRelCenter = (el: HTMLElement | null) => {
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return {
        x: (r.left + r.width * 0.5 - heroRect.left) / heroRect.width,
        y: (r.top + r.height * 0.5 - heroRect.top) / heroRect.height,
      };
    };

    const cdssPos = getRelCenter(featCDSSRef.current);
    if (cdssPos) newSamples.push({ id: "cdss", x: cdssPos.x, y: cdssPos.y });

    const espPos = getRelCenter(featESPRef.current);
    if (espPos) newSamples.push({ id: "esp", x: espPos.x, y: espPos.y });

    const gisPos = getRelCenter(featGISRef.current);
    if (gisPos) newSamples.push({ id: "gis", x: gisPos.x, y: gisPos.y });

    const healthPos = getRelCenter(featHealthRef.current);
    if (healthPos) newSamples.push({ id: "health", x: healthPos.x, y: healthPos.y });

    setSamples(newSamples);
  }, []);

  useEffect(() => {
    updateSamplePoints();
    window.addEventListener("resize", updateSamplePoints);
    return () => window.removeEventListener("resize", updateSamplePoints);
  }, [updateSamplePoints]);

  const handleBrightnessResult = useCallback((results: Record<string, boolean>) => {
    setBrightnessMap(results);
  }, []);

  // Derived states: instant trigger if any point under paragraph or button detects cloud
  const isParagraphBright = !!(
    brightnessMap.p1 ||
    brightnessMap.p2 ||
    brightnessMap.p3 ||
    brightnessMap.p4 ||
    brightnessMap.p5
  );
  const isButtonBright = !!(brightnessMap.btn1 || brightnessMap.btn2);

  return (
    <section ref={heroRef} className="relative min-h-[90vh] w-full overflow-hidden flex flex-col justify-between">
      {/* Animated Atmospheric WebGL Cloud Shader Background */}
      <CloudShader
        className="absolute inset-0"
        speed={0.7}
        count={6}
        cloudColor="#fbf8f2"
        skyTopColor="#3876ba"
        skyBottomColor="#8cbfe8"
        samples={samples}
        onBrightnessResult={handleBrightnessResult}
      />

      {/* Hero Core Content */}
      <div className="relative z-10 mx-auto flex max-w-5xl flex-col items-center px-4 pt-24 pb-16 text-center md:pt-28 md:pb-24">
        {/* Scientific Badge */}
        <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-white/40 bg-white/15 px-3.5 py-1.5 text-xs font-semibold text-white backdrop-blur-md shadow-sm">
          <Sparkles className="h-3.5 w-3.5 text-sky-200" />
          <span>Hybrid Deep Learning & Environmental Health CDSS</span>
        </div>

        {/* Main Heading */}
        <h1 className="text-4xl font-extrabold tracking-tight text-white drop-shadow-lg md:text-6xl lg:text-7xl max-w-4xl leading-[1.15]">
          Understand the Air. <br className="hidden sm:inline" />
          <span className="bg-gradient-to-r from-white via-sky-100 to-sky-200 bg-clip-text text-transparent">
            Predict the Risk.
          </span>{" "}
          Protect Health.
        </h1>

        {/* 1. Subtitle / Value Proposition Paragraph */}
        <p
          ref={paragraphRef}
          className={`mt-6 max-w-2xl text-base md:text-lg leading-relaxed transition-colors duration-300 ease-out ${
            isParagraphBright
              ? "text-sky-950 font-semibold drop-shadow-[0_1px_2px_rgba(255,255,255,0.9)]"
              : "text-white/95 font-normal drop-shadow-md"
          }`}
        >
          AI-AQI fuses real-time IoT sensor telemetry, district-level GIS mapping, and 
          multi-timestep deep learning to deliver calibrated air quality forecasts and personalized clinical risk guidance.
        </p>

        {/* Call to Actions */}
        <div className="mt-8 flex flex-col items-center gap-3.5 sm:flex-row">
          {/* Primary CTA (Static white background, dark text - unchanged) */}
          <a
            href="#prediction"
            className="group inline-flex items-center gap-2 rounded-full bg-white px-7 py-3 text-sm font-bold text-sky-900 shadow-xl transition-all duration-200 hover:-translate-y-0.5 hover:bg-white/95 hover:shadow-2xl focus:outline-none focus:ring-2 focus:ring-white"
          >
            <span>Explore AI-AQI System</span>
            <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
          </a>

          {/* 2. Secondary CTA Button ("View Live Sensor Stream") */}
          <a
            ref={buttonRef}
            href="#dashboard"
            className={`inline-flex items-center gap-2 rounded-full border px-7 py-3 text-sm font-semibold backdrop-blur-md transition-all duration-300 ease-out focus:outline-none focus:ring-2 ${
              isButtonBright
                ? "text-sky-950 font-bold border-sky-900/60 bg-white/70 shadow-lg focus:ring-sky-900"
                : "text-white border-white/40 bg-white/10 hover:bg-white/20 focus:ring-white/60"
            }`}
          >
            <Activity className={`h-4 w-4 transition-colors duration-300 ${isButtonBright ? "text-sky-950 stroke-[2.5]" : "text-sky-200"}`} />
            <span>View Live Sensor Stream</span>
          </a>
        </div>

        {/* 3-6. Supporting Micro-Features Bar (Independent local sampling per feature item) */}
        <div className="mt-12 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-xs font-medium">
          {/* Feature 1 */}
          <span
            ref={featCDSSRef}
            className={`flex items-center gap-1.5 transition-colors duration-300 ease-out ${
              brightnessMap.cdss
                ? "text-sky-950 font-semibold drop-shadow-[0_1px_1px_rgba(255,255,255,0.8)]"
                : "text-white/80 drop-shadow-sm"
            }`}
          >
            <ShieldCheck className={`h-3.5 w-3.5 transition-colors duration-300 ${brightnessMap.cdss ? "text-emerald-800 stroke-[2.5]" : "text-emerald-300"}`} />
            Clinical Decision Support
          </span>

          <span className="hidden sm:inline text-white/40">•</span>

          {/* Feature 2 */}
          <span
            ref={featESPRef}
            className={`flex items-center gap-1.5 transition-colors duration-300 ease-out ${
              brightnessMap.esp
                ? "text-sky-950 font-semibold drop-shadow-[0_1px_1px_rgba(255,255,255,0.8)]"
                : "text-white/80 drop-shadow-sm"
            }`}
          >
            <Activity className={`h-3.5 w-3.5 transition-colors duration-300 ${brightnessMap.esp ? "text-sky-900 stroke-[2.5]" : "text-sky-200"}`} />
            ESP32 Sensor Fusion
          </span>

          <span className="hidden sm:inline text-white/40">•</span>

          {/* Feature 3 */}
          <span
            ref={featGISRef}
            className={`flex items-center gap-1.5 transition-colors duration-300 ease-out ${
              brightnessMap.gis
                ? "text-sky-950 font-semibold drop-shadow-[0_1px_1px_rgba(255,255,255,0.8)]"
                : "text-white/80 drop-shadow-sm"
            }`}
          >
            <MapPin className={`h-3.5 w-3.5 transition-colors duration-300 ${brightnessMap.gis ? "text-amber-900 stroke-[2.5]" : "text-amber-200"}`} />
            30 District GIS Mapping
          </span>

          <span className="hidden sm:inline text-white/40">•</span>

          {/* Feature 4 */}
          <span
            ref={featHealthRef}
            className={`flex items-center gap-1.5 transition-colors duration-300 ease-out ${
              brightnessMap.health
                ? "text-sky-950 font-semibold drop-shadow-[0_1px_1px_rgba(255,255,255,0.8)]"
                : "text-white/80 drop-shadow-sm"
            }`}
          >
            <Stethoscope className={`h-3.5 w-3.5 transition-colors duration-300 ${brightnessMap.health ? "text-indigo-900 stroke-[2.5]" : "text-indigo-200"}`} />
            Individualized Health Risk
          </span>
        </div>
      </div>

      {/* Decorative Bottom Horizon Fader */}
      <div className="relative z-10 h-12 w-full bg-gradient-to-b from-transparent to-sky-900/10 pointer-events-none" />
    </section>
  );
}
