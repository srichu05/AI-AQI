import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface ChartTooltipProps {
  active?: boolean;
  payload?: Array<{
    name?: string;
    value?: string | number;
    color?: string;
    dataKey?: string;
  }>;
  label?: string | number;
  className?: string;
  children?: ReactNode;
}

export function ChartTooltip({
  active,
  payload,
  label,
  className,
}: ChartTooltipProps) {
  if (!active || !payload?.length) {
    return null;
  }

  return (
    <div
      className={cn(
        "rounded-xl border border-white/20 bg-slate-900/90 p-3 text-xs text-white shadow-xl backdrop-blur-md",
        className
      )}
    >
      {label && <div className="mb-1.5 font-bold text-slate-200">{label}</div>}
      <div className="space-y-1">
        {payload.map((item, idx) => (
          <div key={idx} className="flex items-center justify-between gap-4">
            <span className="flex items-center gap-1.5 text-slate-300">
              <span
                className="h-2 w-2 rounded-full"
                style={{ backgroundColor: item.color || "#38bdf8" }}
              />
              {item.name || item.dataKey}:
            </span>
            <span className="font-mono font-bold text-white">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
