import { useState, useCallback } from "react";
import { ParentSize } from "@visx/responsive";
import { scaleLinear, scalePoint } from "@visx/scale";
import { AreaClosed, LinePath } from "@visx/shape";
import { LinearGradient } from "@visx/gradient";
import { curveMonotoneX } from "@visx/curve";
import { motion } from "motion/react";
import { cn } from "@/lib/utils";
import { ChartTooltip } from "./chart-tooltip";

export interface TelemetryPoint {
  id?: number;
  time: string;
  timestamp_raw?: string | null;
  pm1: number;
  pm25: number;
  pm10: number;
}

export interface TelemetryAreaChartProps {
  data: TelemetryPoint[];
  height?: number;
  className?: string;
}

export function TelemetryAreaChart({
  data = [],
  height = 240,
  className,
}: TelemetryAreaChartProps) {
  const [tooltipData, setTooltipData] = useState<{
    x: number;
    y: number;
    point: TelemetryPoint;
  } | null>(null);

  const handlePointerMove = useCallback(
    (event: React.PointerEvent<SVGSVGElement>, width: number, innerHeight: number) => {
      if (!data || data.length === 0) return;

      const svgRect = event.currentTarget.getBoundingClientRect();
      const pointerX = event.clientX - svgRect.left;

      // Find closest data point based on X position
      const step = width / (data.length - 1 || 1);
      const index = Math.min(
        data.length - 1,
        Math.max(0, Math.round(pointerX / step))
      );

      const point = data[index];
      if (point) {
        setTooltipData({
          x: (index / (data.length - 1 || 1)) * width,
          y: innerHeight / 2,
          point,
        });
      }
    },
    [data]
  );

  const handlePointerLeave = useCallback(() => {
    setTooltipData(null);
  }, []);

  if (!data || data.length === 0) {
    return null;
  }

  return (
    <div className={cn("relative w-full overflow-hidden", className)} style={{ height }}>
      {/* Dynamic Hover Tooltip */}
      {tooltipData && (
        <div
          className="absolute z-30 pointer-events-none transition-all duration-75 ease-out"
          style={{
            left: Math.min(Math.max(tooltipData.x, 100), 500),
            top: 10,
            transform: "translateX(-50%)",
          }}
        >
          <ChartTooltip
            active={true}
            label={tooltipData.point.time}
            payload={[
              { name: "PM1.0", value: `${tooltipData.point.pm1.toFixed(1)} µg/m³`, color: "#2dd4bf" },
              { name: "PM2.5", value: `${tooltipData.point.pm25.toFixed(1)} µg/m³`, color: "#38bdf8" },
              { name: "PM10", value: `${tooltipData.point.pm10.toFixed(1)} µg/m³`, color: "#a855f7" },
            ]}
          />
        </div>
      )}

      <ParentSize>
        {({ width, height: h }) => {
          if (width < 10 || h < 10 || !data.length) return null;

          const paddingBottom = 30;
          const paddingTop = 20;
          const paddingLeft = 10;
          const paddingRight = 10;

          const innerHeight = h - paddingTop - paddingBottom;

          const xValues = data.map((d) => d.time);
          const allPMValues = data.flatMap((d) => [d.pm1, d.pm25, d.pm10]);

          const xScale = scalePoint<string>({
            domain: xValues,
            range: [paddingLeft, width - paddingRight],
          });

          const minY = Math.max(0, Math.min(...allPMValues) - 2);
          const maxY = Math.max(minY + 10, Math.max(...allPMValues) + 5);

          const yScale = scaleLinear<number>({
            domain: [minY, maxY],
            range: [h - paddingBottom, paddingTop],
          });

          // Horizontal grid lines
          const gridTicks = yScale.ticks(4);

          return (
            <svg
              width={width}
              height={h}
              className="overflow-visible cursor-crosshair"
              onPointerMove={(e) => handlePointerMove(e, width, innerHeight)}
              onPointerLeave={handlePointerLeave}
            >
              <defs>
                {/* PM1.0 Gradient (Cyan/Teal) */}
                <LinearGradient id="pm1-gradient" from="#2dd4bf" to="#2dd4bf" fromOpacity={0.25} toOpacity={0.0} x1="0" y1="0" x2="0" y2="1" />
                {/* PM2.5 Gradient (Sky Blue) */}
                <LinearGradient id="pm25-gradient" from="#38bdf8" to="#38bdf8" fromOpacity={0.35} toOpacity={0.0} x1="0" y1="0" x2="0" y2="1" />
                {/* PM10 Gradient (Purple/Indigo) */}
                <LinearGradient id="pm10-gradient" from="#a855f7" to="#a855f7" fromOpacity={0.2} toOpacity={0.0} x1="0" y1="0" x2="0" y2="1" />
              </defs>

              {/* Horizontal Reference Grid Lines */}
              <g className="opacity-20">
                {gridTicks.map((tickVal, i) => (
                  <line
                    key={i}
                    x1={paddingLeft}
                    y1={yScale(tickVal)}
                    x2={width - paddingRight}
                    y2={yScale(tickVal)}
                    stroke="#ffffff"
                    strokeDasharray="4 4"
                    strokeWidth={1}
                  />
                ))}
              </g>

              <motion.g initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5 }}>
                {/* 1. PM10 Area & Line (Purple/Indigo) */}
                <AreaClosed
                  data={data}
                  x={(d) => xScale(d.time) ?? 0}
                  y={(d) => yScale(d.pm10)}
                  yScale={yScale}
                  fill="url(#pm10-gradient)"
                  curve={curveMonotoneX}
                />
                <LinePath
                  data={data}
                  x={(d) => xScale(d.time) ?? 0}
                  y={(d) => yScale(d.pm10)}
                  stroke="#a855f7"
                  strokeWidth={1.5}
                  curve={curveMonotoneX}
                />

                {/* 2. PM2.5 Area & Line (Sky Blue) */}
                <AreaClosed
                  data={data}
                  x={(d) => xScale(d.time) ?? 0}
                  y={(d) => yScale(d.pm25)}
                  yScale={yScale}
                  fill="url(#pm25-gradient)"
                  curve={curveMonotoneX}
                />
                <LinePath
                  data={data}
                  x={(d) => xScale(d.time) ?? 0}
                  y={(d) => yScale(d.pm25)}
                  stroke="#38bdf8"
                  strokeWidth={2.2}
                  curve={curveMonotoneX}
                />

                {/* 3. PM1.0 Area & Line (Cyan/Teal) */}
                <AreaClosed
                  data={data}
                  x={(d) => xScale(d.time) ?? 0}
                  y={(d) => yScale(d.pm1)}
                  yScale={yScale}
                  fill="url(#pm1-gradient)"
                  curve={curveMonotoneX}
                />
                <LinePath
                  data={data}
                  x={(d) => xScale(d.time) ?? 0}
                  y={(d) => yScale(d.pm1)}
                  stroke="#2dd4bf"
                  strokeWidth={2.0}
                  curve={curveMonotoneX}
                />

                {/* Interactive Hover Crosshair */}
                {tooltipData && (
                  <line
                    x1={tooltipData.x}
                    y1={paddingTop}
                    x2={tooltipData.x}
                    y2={h - paddingBottom}
                    stroke="#ffffff"
                    strokeWidth={1.5}
                    strokeDasharray="3 3"
                    className="opacity-70 pointer-events-none"
                  />
                )}
              </motion.g>

              {/* X-Axis Time Labels */}
              <g className="text-[10px] fill-white/80 font-mono font-medium">
                {data.map((d, idx) => {
                  // Show labels selectively to avoid crowding
                  const total = data.length;
                  const step = Math.ceil(total / 6);
                  if (idx % step !== 0 && idx !== total - 1) return null;

                  const xPos = xScale(d.time) ?? 0;
                  return (
                    <text
                      key={idx}
                      x={xPos}
                      y={h - 8}
                      textAnchor="middle"
                      className="fill-sky-100/90 font-mono text-[10px]"
                    >
                      {d.time}
                    </text>
                  );
                })}
              </g>
            </svg>
          );
        }}
      </ParentSize>
    </div>
  );
}
