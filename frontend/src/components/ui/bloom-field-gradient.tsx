import { cn } from "@/lib/utils";

// --- Component ---
// GradientBackground — "Bloom Field gradient", exported as live CSS with soften-blur and grain passes.
// Zero runtime heavy dependencies: fills its parent container.
export function GradientBackground({ className }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={cn("relative h-full w-full overflow-hidden", className)}
      style={{
        containerType: "size",
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          backgroundColor: "#E2E2E2",
          backgroundImage:
            "url(\"data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(%23n)' opacity='0.500'/></svg>\"), radial-gradient(circle at 67.04% 45.93%, rgba(226, 226, 226, 1) 0%, rgba(226, 226, 226, 0.844) 19.02%, rgba(226, 226, 226, 0.5) 38.05%, rgba(226, 226, 226, 0.156) 57.07%, rgba(226, 226, 226, 0) 76.1%), radial-gradient(circle at 35.47% 65.92%, rgba(27, 159, 254, 1) 0%, rgba(27, 159, 254, 0.844) 12.9%, rgba(27, 159, 254, 0.5) 25.8%, rgba(27, 159, 254, 0.156) 38.7%, rgba(27, 159, 254, 0) 51.6%), radial-gradient(circle at 48.33% 20.11%, rgba(27, 159, 254, 1) 0%, rgba(27, 159, 254, 0.844) 16.75%, rgba(27, 159, 254, 0.5) 33.5%, rgba(27, 159, 254, 0.156) 50.25%, rgba(27, 159, 254, 0) 67%), radial-gradient(circle at 80.81% 88.03%, rgba(74, 201, 255, 1) 0%, rgba(74, 201, 255, 0.844) 10.28%, rgba(74, 201, 255, 0.5) 20.55%, rgba(74, 201, 255, 0.156) 30.83%, rgba(74, 201, 255, 0) 41.1%)",
          backgroundSize: "120px 120px, auto, auto, auto, auto",
          backgroundBlendMode: "overlay, normal, normal, normal, normal",
        }}
      />
      <svg
        aria-hidden="true"
        style={{
          position: "absolute",
          inset: 0,
          width: "100%",
          height: "100%",
          opacity: 0.5,
          mixBlendMode: "overlay",
        }}
      >
        <filter id="grain-fba2fa02">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.8"
            numOctaves="2"
            stitchTiles="stitch"
          />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#grain-fba2fa02)" />
      </svg>
    </div>
  );
}
