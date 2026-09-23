import { motion } from "motion/react";
import Balancer from "react-wrap-balancer";
import { Cloudscape } from "@/components/ui/cloudscape";
import {
  BrainCircuit,
  Radio,
  MapPinned,
  HeartPulse,
  GitMerge,
  Sparkles,
  ArrowRight,
} from "lucide-react";

interface CapabilitiesFanCard {
  id: string;
  name: string;
  category: string;
  description: string;
  href: string;
  cta: string;
  imageSrc: string;
  Icon: any;
  slot: {
    width: string;
    layout: string;
    rotate: number;
    ty: number;
  };
}

const fannedCards: CapabilitiesFanCard[] = [
  {
    id: "prediction",
    name: "Deep Learning Forecast",
    category: "AI Forecasting",
    description: "Multi-timestep AI risk forecasts using transformer neural networks.",
    href: "#prediction",
    cta: "Explore Prediction",
    imageSrc: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=900&auto=format&fit=crop",
    Icon: BrainCircuit,
    slot: { width: "w-[21%] md:w-[19%]", layout: "-mr-3 md:-mr-5 z-10", rotate: -8, ty: 20 },
  },
  {
    id: "dashboard",
    name: "Live Sensor Fusion",
    category: "IoT Ingestion",
    description: "Real-time ESP32 node observations fused with atmospheric telemetry.",
    href: "#dashboard",
    cta: "View Live Data",
    imageSrc: "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=900&auto=format&fit=crop",
    Icon: Radio,
    slot: { width: "w-[24%] md:w-[22%]", layout: "-mr-3 md:-mr-5 z-20", rotate: -4, ty: 8 },
  },
  {
    id: "gis",
    name: "Spatial Risk Mapping",
    category: "GIS Mapping",
    description: "30-District spatial risk index analysis & spatial node intelligence.",
    href: "#gis",
    cta: "Open GIS Map",
    imageSrc: "https://images.unsplash.com/photo-1524661135-423995f22d0b?q=80&w=900&auto=format&fit=crop",
    Icon: MapPinned,
    slot: { width: "w-[27%] md:w-[25%]", layout: "z-30", rotate: 0, ty: -8 },
  },
  {
    id: "cdss",
    name: "Clinical Health CDSS",
    category: "Clinical Guidance",
    description: "Personalized vulnerability stratification & preventive guidance.",
    href: "#cdss",
    cta: "Assess Risk",
    imageSrc: "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?q=80&w=900&auto=format&fit=crop",
    Icon: HeartPulse,
    slot: { width: "w-[24%] md:w-[22%]", layout: "-ml-3 md:-ml-5 z-20", rotate: 4, ty: 8 },
  },
  {
    id: "about",
    name: "Data Integration",
    category: "Data Intelligence",
    description: "Fuse particulate matter, weather, and environmental variables.",
    href: "#about",
    cta: "Explore Data",
    imageSrc: "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?q=80&w=900&auto=format&fit=crop",
    Icon: GitMerge,
    slot: { width: "w-[21%] md:w-[19%]", layout: "-ml-3 md:-ml-5 z-10", rotate: 8, ty: 20 },
  },
];

export function AIAQICapabilities() {
  return (
    <section className="relative w-full py-20 px-4 md:px-8 lg:px-12 overflow-hidden min-h-[90vh] flex flex-col justify-center">
      {/* 1. WebGL Cloudscape Background Shader — 100% SEAMLESS HERO BLENDING */}
      <Cloudscape
        className="absolute inset-0 z-0"
        colorTop="#8cbfe8"
        colorMid="#9fd2f6"
        colorBottom="#64a3e3"
        speed={1.0}
        height="100%"
      />

      {/* Top Seam Seamless Gradient Blending Layer */}
      <div className="absolute top-0 inset-x-0 h-32 bg-gradient-to-b from-[#8cbfe8] via-[#8cbfe8]/70 to-transparent z-[1] pointer-events-none" />

      {/* 2. Section Header Overlay */}
      <div className="relative z-10 mx-auto max-w-4xl text-center mb-10 md:mb-14">
        {/* Category Pill */}
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/15 px-4 py-1.5 text-xs font-bold uppercase tracking-widest text-white backdrop-blur-md shadow-xs">
          <Sparkles className="h-3.5 w-3.5 text-cyan-200" />
          <span>Core AI-AQI Capabilities</span>
        </div>

        {/* Heading — WHITE TYPOGRAPHY WITH BALANCER */}
        <h2 className="text-3xl font-extrabold tracking-tight text-white md:text-5xl lg:text-6xl drop-shadow-md leading-[1.15]">
          <Balancer>
            One Intelligence Layer. <br className="hidden sm:inline" />
            <span className="bg-gradient-to-r from-white via-cyan-100 to-sky-200 bg-clip-text text-transparent">
              Multiple Environmental Signals.
            </span>
          </Balancer>
        </h2>

        {/* Supporting Paragraph — WHITE / 80% OPACITY WITH BALANCER */}
        <p className="mt-4 text-base md:text-lg font-medium text-white/80 leading-relaxed max-w-2xl mx-auto drop-shadow-xs">
          <Balancer>
            AI-AQI brings together live environmental sensing, deep-learning forecasts, spatial risk intelligence, 
            and personalized clinical guidance into ready-to-deploy intelligence cards.
          </Balancer>
        </p>

      </div>

      {/* 3. 5-Card Fanned Stack Layout (Light Glass Card Design) */}
      <div className="relative z-10 mx-auto w-full max-w-6xl">
        <div className="relative flex w-full items-center justify-center py-6">
          {fannedCards.map((card) => {
            const { slot, Icon } = card;
            return (
              <motion.a
                key={card.id}
                href={card.href}
                style={{
                  rotate: slot.rotate,
                  translateY: slot.ty,
                }}
                whileHover={{
                  scale: 1.1,
                  rotate: 0,
                  translateY: -20,
                  zIndex: 50,
                  transition: { duration: 0.3, ease: "easeOut" },
                }}
                className={`group relative shrink-0 overflow-hidden rounded-3xl shadow-2xl border border-white/40 bg-slate-900/70 backdrop-blur-xl transition-all duration-300 aspect-4/5 ${slot.width} ${slot.layout}`}
              >
                {/* Full Vivid Color Background Image */}
                <img
                  src={card.imageSrc}
                  alt={card.name}
                  className="absolute inset-0 size-full object-cover opacity-80 transition-all duration-700 group-hover:scale-110 group-hover:opacity-100"
                />

                {/* Dark Gradient Overlay for Crisp Text Readability at Bottom */}
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/70 to-slate-900/20" />

                {/* Card Content Overlay — CRISP WHITE TYPOGRAPHY */}
                <div className="relative z-10 flex h-full flex-col justify-between p-4 md:p-6 text-white">
                  {/* Top Badge & Icon */}
                  <div className="flex items-center justify-between gap-1.5">
                    <div className="flex h-9 w-9 md:h-11 md:w-11 items-center justify-center rounded-2xl border border-white/40 bg-sky-600/90 text-white shadow-md backdrop-blur-md transition-all group-hover:bg-cyan-500 group-hover:scale-110">
                      <Icon className="h-4 w-4 md:h-5 md:w-5 stroke-[2.2]" />
                    </div>
                    <span className="rounded-full border border-white/30 bg-slate-900/80 px-2.5 py-1 text-[8px] md:text-[10px] font-black uppercase tracking-wider text-cyan-200 backdrop-blur-md shadow-xs">
                      {card.category}
                    </span>
                  </div>

                  {/* Title & Description */}
                  <div className="space-y-1 md:space-y-1.5">
                    <h3 className="text-sm md:text-lg font-black text-white drop-shadow-md group-hover:text-cyan-200 transition-colors leading-snug">
                      {card.name}
                    </h3>
                    <p className="text-[10px] md:text-xs font-bold text-white/90 line-clamp-2 leading-relaxed drop-shadow-xs">
                      {card.description}
                    </p>

                    <div className="pt-1.5 flex items-center gap-1 text-[9px] md:text-[11px] font-black uppercase tracking-wider text-cyan-300 group-hover:text-white transition-colors">
                      <span>{card.cta}</span>
                      <ArrowRight className="h-3 w-3 transition-transform group-hover:translate-x-1.5 text-cyan-300 group-hover:text-white" />
                    </div>
                  </div>
                </div>

                {/* Glass Highlight Border */}
                <div className="absolute inset-0 rounded-3xl border border-transparent transition-colors duration-300 group-hover:border-cyan-400/60 pointer-events-none" />
              </motion.a>
            );
          })}
        </div>
      </div>
    </section>
  );
}
