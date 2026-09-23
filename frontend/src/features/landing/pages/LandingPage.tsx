import { AIAQIHero } from "../components/AIAQIHero";
import { AIAQICapabilities } from "../components/AIAQICapabilities";

export function LandingPage() {
  return (
    <div className="min-h-screen w-full bg-gradient-to-b from-[#3876ba] via-[#528dcb] to-[#7db6e6] text-slate-900 font-sans overflow-x-hidden">
      {/* 1. Hero Section */}
      <AIAQIHero />

      {/* 2. AI-AQI Bento Capabilities Section */}
      <AIAQICapabilities />
    </div>
  );
}
