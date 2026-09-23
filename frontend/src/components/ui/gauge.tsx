import { motion } from "motion/react";
import { cn } from "@/lib/utils";

export interface GaugeProps {
  value: number; // 0 - 100
  totalNotches?: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
  unit?: string;
  activeColor?: string;
  inactiveColor?: string;
  className?: string;
}

export function Gauge({
  value,
  totalNotches = 36,
  size = 220,
  strokeWidth = 16,
  label = "US EPA Scale",
  unit = "AQI",
  activeColor = "#0284c7",
  inactiveColor = "rgba(14, 165, 233, 0.25)",
  className,
}: GaugeProps) {
  const radius = (size - strokeWidth) / 2;
  const activeNotches = Math.round((Math.min(100, Math.max(0, value)) / 100) * totalNotches);

  return (
    <div
      className={cn(
        "relative flex flex-col items-center justify-center p-2",
        className
      )}
      style={{ width: size, height: size * 0.65 }}
    >
      <svg
        width={size}
        height={size * 0.6}
        viewBox={`0 0 ${size} ${size / 2 + 20}`}
        className="overflow-visible"
      >
        <g transform={`translate(${size / 2}, ${size / 2})`}>
          {Array.from({ length: totalNotches }).map((_, i) => {
            const angle = -180 + (i / (totalNotches - 1)) * 180;
            const rad = (angle * Math.PI) / 180;
            const rInner = radius - strokeWidth;
            const rOuter = radius;
            const x1 = Math.cos(rad) * rInner;
            const y1 = Math.sin(rad) * rInner;
            const x2 = Math.cos(rad) * rOuter;
            const y2 = Math.sin(rad) * rOuter;
            const isActive = i < activeNotches;

            return (
              <motion.line
                key={i}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke={isActive ? activeColor : inactiveColor}
                strokeWidth={3.5}
                strokeLinecap="round"
                initial={{ opacity: 0, scale: 0.85 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.35, delay: i * 0.012 }}
              />
            );
          })}
        </g>
      </svg>
      {/* Center Value Stack — High Visibility Blue Contrast */}
      <div className="absolute bottom-2 flex flex-col items-center text-center">
        <span className="text-4xl font-black tracking-tight text-sky-950 drop-shadow-xs font-sans">
          {Math.round(value)}
        </span>
        <span className="mt-0.5 text-[11px] font-bold uppercase tracking-wider text-sky-900">
          {unit} • {label}
        </span>
      </div>
    </div>
  );
}
