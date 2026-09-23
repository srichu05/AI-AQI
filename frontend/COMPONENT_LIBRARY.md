# AI-AQI Component Registry & Integration Log

This registry tracks all external UI components (from sources like Aceternity UI, Skiper UI, Magic UI, 21st.dev, etc.) adapted into local, reusable React + TypeScript components for the AI-AQI project.

---

## Component Integration Workflow

For every external component submitted:
1. **Source Inspection & Dependency Analysis**: Identify framework requirements, npm dependencies, CSS/Tailwind tokens, animation/3D drivers, and required assets.
2. **Architecture Adaptation**: Convert component source into isolated TypeScript components under `src/components/ui/` or `src/features/`.
3. **Design Token Harmonization**: Map visual styling to global AI-AQI design tokens (colors, radii, typography, spacing).
4. **API & Data Connection**: Replace hardcoded values with real backend data or clean, isolated mock state for UI preview.
5. **Registry Entry**: Log the component in this file.

---

## Integrated Components Log

| Component Name | Source | Target Path | Dependencies Added | Purpose & Placement | Status |
|---|---|---|---|---|---|
| **CloudShader** | Aceternity UI | `src/components/ui/cloud-shader.tsx` | WebGL (Native Browser Context) | Hero Section atmospheric animated background | Active |
| **GradientBackground** | 21st.dev | `src/components/ui/bloom-field-gradient.tsx` | SVG/CSS Filters | Reusable background gradient for future website sections | Active |

---

## Component Details

### 1. CloudShader (`src/components/ui/cloud-shader.tsx`)
- **Category:** WebGL Background Component
- **Source:** Aceternity UI (`cloud-shader-hero-demo.tsx`)
- **Adaptation:** Adapted for AI-AQI Hero section. Renders procedural billow noise and FBM domain warping on a 2D WebGL canvas. Supports reduced motion and clean WebGL context lifecycle management.
- **Props:** `speed`, `count`, `cloudColor`, `skyTopColor`, `skyBottomColor`, `className`, `children`.

### 2. GradientBackground (`src/components/ui/bloom-field-gradient.tsx`)
- **Category:** Reusable CSS/SVG Background Primitive ("Bloom Field Gradient")
- **Source:** 21st.dev Gradient Builder
- **Adaptation:** Pure CSS overlay with zero extra heavy npm dependencies. Ready for use across future dashboard, GIS map, CDSS, and telemetry sections.
