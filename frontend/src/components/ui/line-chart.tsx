import type { ReactNode } from "react";
import { ParentSize } from "@visx/responsive";
import { scaleLinear, scalePoint } from "@visx/scale";
import { LinePath } from "@visx/shape";
import { curveMonotoneX } from "@visx/curve";
import { motion } from "motion/react";
import { cn } from "@/lib/utils";

export interface LineChartProps {
  data: Record<string, unknown>[];
  xDataKey?: string;
  yDataKey?: string;
  height?: number;
  strokeColor?: string;
  strokeWidth?: number;
  className?: string;
  children?: ReactNode;
}

export function LineChart({
  data = [],
  xDataKey = "time",
  yDataKey = "value",
  height = 200,
  strokeColor = "#38bdf8",
  strokeWidth = 2.5,
  className,
}: LineChartProps) {
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
              <motion.g initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.6 }}>
                <LinePath
                  data={data}
                  x={(d) => xScale(String(d[xDataKey] ?? "")) ?? 0}
                  y={(d) => yScale(Number(d[yDataKey] ?? 0))}
                  stroke={strokeColor}
                  strokeWidth={strokeWidth}
                  curve={curveMonotoneX}
                />
                {data.map((d, i) => {
                  const cx = xScale(String(d[xDataKey] ?? "")) ?? 0;
                  const cy = yScale(Number(d[yDataKey] ?? 0));
                  return (
                    <circle
                      key={i}
                      cx={cx}
                      cy={cy}
                      r={4}
                      fill={strokeColor}
                      className="transition-transform hover:scale-150"
                    />
                  );
                })}
              </motion.g>
            </svg>
          );
        }}
      </ParentSize>
    </div>
  );
}
