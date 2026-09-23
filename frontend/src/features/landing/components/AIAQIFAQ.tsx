import { FaqAccordion, type FaqItem } from "@/components/ui/faq-accordion";
import { LightLines } from "@/components/ui/light-lines";
import { HelpCircle } from "lucide-react";

const FAQ_ITEMS: FaqItem[] = [
  {
    question: "What is AI-AQI?",
    answer:
      "AI-AQI is an environmental intelligence platform that combines real-time air-quality sensing, environmental data, deep-learning forecasting, spatial risk analysis, and environmental health decision support to turn air-quality observations into actionable intelligence.",
  },
  {
    question: "What data does AI-AQI use?",
    answer:
      "AI-AQI is designed to combine multiple environmental data sources, including real-time IoT sensor observations, air-quality datasets, meteorological and environmental variables, and spatial or geographic information.",
  },
  {
    question: "How does AI-AQI predict future air-quality risk?",
    answer:
      "The prediction layer uses deep-learning models to learn relationships between historical environmental conditions and air-quality behavior, producing multi-timestep forecasts that can be used for future risk assessment.",
  },
  {
    question: "What is Live Sensor Fusion?",
    answer:
      "Live Sensor Fusion combines real-time observations from the deployed environmental sensing system with relevant external environmental information to provide a current view of air-quality conditions.",
  },
  {
    question: "What does the GIS mapping layer provide?",
    answer:
      "The GIS layer provides spatial intelligence by showing how environmental and air-quality risk varies across locations, enabling district-level analysis and easier identification of areas requiring attention.",
  },
  {
    question: "What is the Environmental Health CDSS?",
    answer:
      "The Environmental Health Clinical Decision Support System connects environmental exposure information with individual vulnerability factors to provide personalized preventive health-risk guidance.",
  },
  {
    question: "Can AI-AQI be used to understand both current and future risk?",
    answer:
      "Yes. The system is designed to combine current environmental observations from sensing and external data sources with deep-learning forecasts, allowing users to examine present conditions as well as anticipated air-quality risk.",
  },
  {
    question: "Who is AI-AQI designed for?",
    answer:
      "AI-AQI is intended to support environmental monitoring, air-quality analysis, researchers, public-health and healthcare-oriented decision support, and users who need a clearer understanding of environmental health risk.",
  },
  {
    question: "How are the different AI-AQI components connected?",
    answer:
      "Environmental and sensor data are processed and transformed into structured features, which feed the intelligence and forecasting layers. The resulting information can then be presented through spatial analysis and environmental health decision-support interfaces.",
  },
  {
    question: "Is AI-AQI only an air-quality monitoring dashboard?",
    answer:
      "No. Monitoring is only one part of the system. AI-AQI is designed as an integrated environmental intelligence platform combining sensing, prediction, spatial analysis, and health-risk decision support.",
  },
];

export function AIAQIFAQ() {
  return (
    <section className="relative w-full py-24 px-4 md:px-8 lg:px-12 overflow-hidden">
      {/* LightLines Background continuation for seamless visual transition */}
      <LightLines
        className="absolute inset-0 z-0"
        gradientFrom="#7db6e6"
        gradientTo="#3876ba"
        lineColor="#ffffff"
        lightColor="#ffffff"
        linesOpacity={0.06}
        lightsOpacity={0.75}
        speedMultiplier={0.8}
      />

      {/* Section Header */}
      <div className="relative z-10 mx-auto max-w-4xl text-center mb-14">
        {/* Category Badge */}
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/15 px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-white backdrop-blur-md shadow-xs">
          <HelpCircle className="h-3.5 w-3.5 text-cyan-200" />
          <span>Platform Information & Guidance</span>
        </div>

        {/* Section Heading — WHITE */}
        <h2 className="text-3xl font-extrabold tracking-tight text-white md:text-5xl lg:text-6xl drop-shadow-md leading-[1.15]">
          Frequently Asked About <br className="hidden sm:inline" />
          <span className="bg-gradient-to-r from-white via-cyan-100 to-sky-200 bg-clip-text text-transparent">
            AI-AQI
          </span>
        </h2>

        {/* Section Subtitle — WHITE / 80% OPACITY */}
        <p className="mt-6 text-base md:text-lg font-medium text-white/80 leading-relaxed max-w-2xl mx-auto drop-shadow-xs">
          Understand how AI-AQI connects environmental sensing, deep learning, spatial intelligence, and health-risk guidance.
        </p>
      </div>

      {/* FAQ Accordion Component */}
      <div className="relative z-10 mx-auto max-w-4xl">
        <FaqAccordion items={FAQ_ITEMS} />
      </div>
    </section>
  );
}
