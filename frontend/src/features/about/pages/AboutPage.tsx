import { AIAQIFAQ } from "@/features/landing/components/AIAQIFAQ";

export function AboutPage() {
  return (
    <div className="min-h-screen w-full bg-gradient-to-b from-[#3876ba] via-[#528dcb] to-[#7db6e6] text-slate-900 font-sans overflow-x-hidden">
      {/* Frequently Asked About AI-AQI Page Content */}
      <main className="pt-20 pb-16 md:pt-24">
        <AIAQIFAQ />
      </main>
    </div>
  );
}

export default AboutPage;
