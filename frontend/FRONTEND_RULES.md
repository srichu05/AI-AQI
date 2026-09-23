# AI-AQI Frontend Engineering Rules & Principles

## 1. Clean Scaffolding & Component Ownership
- **Local Ownership:** Once an external component (from Aceternity UI, Skiper UI, Magic UI, 21st.dev, etc.) is integrated, it becomes a local component under `src/components/ui/` or `src/features/`.
- **No Direct Source Dependencies:** Never iframe external demo sites or depend on external runtime servers.
- **No Copying External Project Architectures:** Adapt external components to fit our Vite + React + TypeScript + Tailwind structure rather than rearchitecting our app around the external component.

## 2. Styling & Design System
- **Single Coherent Aesthetic:** All components, regardless of source, must conform to the unified AI-AQI design language (slate/zinc dark palette with AQI severity color coding: Good `#10b981`, Moderate `#f59e0b`, Unhealthy `#f97316`, Severe `#ef4444`, Hazardous `#8b5cf6`).
- **Tailwind + CSS Variables:** Use the `cn` utility (`clsx` + `tailwind-merge`) in `src/lib/utils.ts` for dynamic class merging.
- **Micro-Animations & 3D:** Use motion strategically (high visual motion for landing/hero/sensor streams; restrained motion for CDSS clinical forms and data tables).

## 3. Dependency Management Policy
- **No Unnecessary Packages:** Do not install heavy dependencies (e.g. Three.js, GSAP, Framer Motion, Recharts) until an approved component specifically requires them.
- **Reuse Existing Primitives:** Check if existing dependencies or utilities can perform the required task before adding new ones.

## 4. API & Backend Policy
- **Strict Backend Isolation:** The frontend is purely a consumer of backend endpoints (`/health`, `/predict`, `/map_data`, `/cdss/assess`, `/api/telemetry/latest`). Never modify backend files or recreate backend business logic in frontend JS.
- **No Fake Hardcoded Data in Production:** All components displaying operational AQI or CDSS data must consume real API data via `src/api/`. UI-only development mock data must be explicitly isolated.

## 5. Directory & Modular Architecture
- `src/api/`: Typed FastAPI endpoint handlers (`health.ts`, `predict.ts`, `map.ts`, `cdss.ts`, `telemetry.ts`).
- `src/components/ui/`: Adapted UI primitives.
- `src/components/shared/`: Layout containers, navbars, footers.
- `src/features/`: Feature modules (`landing`, `dashboard`, `prediction`, `gis`, `cdss`, `sensors`, `about`).
- `src/lib/`: Helper utilities (`utils.ts`).
- `src/types/`: TypeScript request/response contracts.
- `src/hooks/`: Reusable custom React hooks.
