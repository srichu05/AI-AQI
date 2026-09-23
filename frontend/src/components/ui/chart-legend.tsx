import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface ChartLegendItem {
  key: string;
  label: string;
  color: string;
}

export interface ChartLegendProps {
  items: ChartLegendItem[];
  className?: string;
  children?: ReactNode;
}

export function ChartLegend({ items, className }: ChartLegendProps) {
  if (!items?.length) return null;

  return (
    <div
      className={cn(
        "flex flex-wrap items-center justify-center gap-4 text-xs font-semibold text-slate-300",
        className
      )}
    >
      {items.map((item) => (
        <div key={item.key} className="flex items-center gap-1.5">
          <span
            className="h-2.5 w-2.5 rounded-full"
            style={{ backgroundColor: item.color }}
          />
          <span>{item.label}</span>
        </div>
      ))}
    </div>
  );
}
