import type { ReactNode } from "react";
import { ParentSize } from "@visx/responsive";
import { scaleLinear, scalePoint } from "@visx/scale";
import { AreaClosed, LinePath } from "@visx/shape";
import { LinearGradient } from "@visx/gradient";
import { curveMonotoneX } from "@visx/curve";
import { motion } from "motion/react";
import { cn } from "@/lib/utils";

export interface AreaChartProps {
  data: Record<string, unknown>[];
  xDataKey?: string;
  yDataKey?: string;
  height?: number;
  gradientFrom?: string;
  gradientTo?: string;
  strokeColor?: string;
  strokeWidth?: number;
  className?: string;
  children?: ReactNode;
}

export function AreaChart({
  data = [],
  xDataKey = "time",
  yDataKey = "value",
  height = 200,
  gradientFrom = "rgba(56, 189, 248, 0.4)",
  gradientTo = "rgba(56, 189, 248, 0.0)",
  strokeColor = "#38bdf8",
  strokeWidth = 2.5,
  className,
}: AreaChartProps) {
  const gradientId = "area-gradient-id";

  return (
    <div className={cn("relative w-full overflow-hidden", className)} style={{ height }}>
      <ParentSize>
        {({ width, height: h }) => {
          if (width < 10 || h < 10 || !data.length) return null;

          const xValues = data.map((d) => String(d[xDataKey] ?? ""));
          const yValues = data.map((d) => Number(d[yDataKey] ?? 0));

          const xScale = scalePoint<string>({
            domain: xValues,
            range: [10, width - 10],
          });

          const minY = Math.min(...yValues);
          const maxY = Math.max(...yValues);
          const yScale = scaleLinear<number>({
            domain: [minY * 0.9, maxY * 1.1 || 100],
            range: [h - 20, 10],
          });

          return (
            <svg width={width} height={h} className="overflow-visible">
              <defs>
                <LinearGradient
                  id={gradientId}
                  from={gradientFrom}
                  to={gradientTo}
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="1"
                />
              </defs>
              <motion.g initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6 }}>
                <AreaClosed
                  data={data}
                  x={(d) => xScale(String(d[xDataKey] ?? "")) ?? 0}
                  y={(d) => yScale(Number(d[yDataKey] ?? 0))}
                  yScale={yScale}
                  fill={`url(#${gradientId})`}
                  curve={curveMonotoneX}
                />
                <LinePath
                  data={data}
                  x={(d) => xScale(String(d[xDataKey] ?? "")) ?? 0}
                  y={(d) => yScale(Number(d[yDataKey] ?? 0))}
                  stroke={strokeColor}
                  strokeWidth={strokeWidth}
                  curve={curveMonotoneX}
                />
              </motion.g>
            </svg>
          );
        }}
      </ParentSize>
    </div>
  );
}
