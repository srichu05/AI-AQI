import type { ReactNode, ComponentType } from "react";
import { ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface BentoGridProps {
  children: ReactNode;
  className?: string;
}

export function BentoGrid({ children, className }: BentoGridProps) {
  return (
    <div
      className={cn(
        "grid w-full grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 auto-rows-fr",
        className
      )}
    >
      {children}
    </div>
  );
}

interface BentoCardProps {
  name: string;
  className?: string;
  Icon: ComponentType<{ className?: string }>;
  description: string;
  href: string;
  cta: string;
  category?: string;
  imageSrc?: string;
}

export function BentoCard({
  name,
  className,
  Icon,
  description,
  href,
  cta,
  category,
  imageSrc,
}: BentoCardProps) {
  return (
    <a
      href={href}
      key={name}
      className={cn(
        "group relative flex flex-col justify-between overflow-hidden rounded-3xl p-7 md:p-8 transition-all duration-500 ease-out transform-gpu hover:-translate-y-2 focus:outline-none focus:ring-2 focus:ring-cyan-300/60 min-h-[300px]",
        // Transparent Glass Base Surface
        "bg-white/[0.08] hover:bg-white/[0.16] backdrop-blur-md",
        "border border-white/30 hover:border-white/60",
        "shadow-[0_12px_40px_rgba(0,0,0,0.15)] hover:shadow-[0_20px_50px_rgba(56,189,248,0.3)]",
        className
      )}
    >
      {/* Background Image with Hover Zoom & Gradient Overlay */}
      {imageSrc && (
        <div className="absolute inset-0 z-0 overflow-hidden">
          <img
            src={imageSrc}
            alt={name}
            className="size-full object-cover opacity-40 mix-blend-overlay transition-transform duration-700 ease-out group-hover:scale-110 group-hover:opacity-60"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-sky-950/90 via-sky-900/40 to-transparent" />
        </div>
      )}

      {/* Top Header: Line Icon & Category Tag */}
      <div className="relative z-10">
        <div className="flex items-center justify-between gap-4">
          {/* Subtle Glass Icon Badge Container */}
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-white/40 bg-white/20 text-white shadow-md backdrop-blur-md transition-all duration-300 group-hover:scale-110 group-hover:bg-cyan-500 group-hover:border-white">
            <Icon className="h-6 w-6 stroke-[2.2]" />
          </div>

          {category && (
            <span className="rounded-full border border-white/40 bg-white/20 px-3.5 py-1 text-[11px] font-extrabold uppercase tracking-wider text-cyan-100 backdrop-blur-md shadow-xs">
              {category}
            </span>
          )}
        </div>

        {/* Title & Description — WHITE TYPOGRAPHY */}
        <div className="mt-6 flex flex-col gap-2.5">
          <h3 className="text-xl md:text-2xl font-black tracking-tight text-white drop-shadow-md transition-colors duration-200 group-hover:text-cyan-100">
            {name}
          </h3>
          <p className="text-sm md:text-base font-bold text-white/90 leading-relaxed drop-shadow-xs">
            {description}
          </p>
        </div>
      </div>

      {/* Footer Navigation CTA */}
      <div className="relative z-10 mt-8 flex items-center pt-2">
        <span className="inline-flex items-center gap-2 text-xs font-black uppercase tracking-wider text-cyan-100 transition-colors duration-300 group-hover:text-white">
          <span>{cta}</span>
          <ArrowRight className="h-4 w-4 transition-transform duration-300 group-hover:translate-x-2 text-cyan-200 group-hover:text-white" />
        </span>
      </div>

      {/* Subtle Glow Overlay */}
      <div className="absolute inset-0 rounded-3xl border border-transparent transition-colors duration-300 group-hover:border-cyan-300/40 pointer-events-none z-20" />
    </a>
  );
}
