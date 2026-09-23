import { useEffect, useState } from "react";
import { LineChart, type LineChartProps } from "./line-chart";
import { cn } from "@/lib/utils";

export interface LiveLineChartProps extends LineChartProps {
  refreshIntervalMs?: number;
  maxPoints?: number;
  onFetchPoint?: () => { time: string; value: number };
}

export function LiveLineChart({
  data: initialData = [],
  xDataKey = "time",
  yDataKey = "value",
  refreshIntervalMs = 2000,
  maxPoints = 20,
  onFetchPoint,
  className,
  ...props
}: LiveLineChartProps) {
  const [data, setData] = useState<Record<string, unknown>[]>(initialData);

  useEffect(() => {
    if (!onFetchPoint) return;

    const interval = setInterval(() => {
      const newPoint = onFetchPoint();
      setData((prev) => {
        const next = [...prev, newPoint];
        return next.slice(-maxPoints);
      });
    }, refreshIntervalMs);

    return () => clearInterval(interval);
  }, [onFetchPoint, refreshIntervalMs, maxPoints]);

  return (
    <div className={cn("relative w-full", className)}>
      <div className="absolute top-2 right-2 flex items-center gap-1.5 z-10 rounded-full bg-emerald-500/20 px-2.5 py-0.5 text-[10px] font-extrabold text-emerald-300 border border-emerald-400/30">
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
        </span>
        LIVE STREAM
      </div>
      <LineChart data={data} xDataKey={xDataKey} yDataKey={yDataKey} {...props} />
    </div>
  );
}
