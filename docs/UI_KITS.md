# UI Kits (Web)

Recommendation (default)
- Tailwind CSS + Radix Primitives + shadcn/ui
  - Pros: accessible primitives, consistent theming, great DX, large ecosystem.
  - Cons: Tailwind learning curve; design drift if not curated.

Alternatives
- MUI: batteries-included, theming, enterprise-friendly; heavier bundle.
- Mantine: strong components and hooks; good dark mode; moderate ecosystem.
- Chakra UI: simple, accessible, ergonomic props; fewer complex components.
- Headless UI: unstyled a11y primitives; pair with Tailwind.
- NextUI: modern React UI library; solid components; good theming.
- Ant Design: comprehensive enterprise components; heavier style footprint.
- Flowbite: Tailwind-based components; rapid prototyping.
- daisyUI: Tailwind plugin with themes/components; quick starts.
- PrimeReact: large suite incl. data components; heavier.

Patterns
- Define tokens (colors/spacing/typography) early; stick to them.
- Prefer headless primitives for complex interactive widgets (combobox, dialogs).
- Use a design doc per complex component (API/props/events/states/examples).

Starter Stack
- Tailwind + shadcn/ui with class-variance-authority for variants.
- TanStack Table/Query for data and caching.
- Radix Icons or Lucide for consistent icons.

Project Selection
- Configure default UI kit in `config/project.yml` (`ui_kit: shadcn` or one of the alternatives).
- Document chosen kit and rationale in `docs/DECISIONS.md`.

Selection Criteria Checklist
- Accessibility: WCAG AA support; keyboard traps; focus outlines.
- Theming: dark/light; tokens; CSS vars; motion controls.
- Composition: headless primitives for custom behaviors; escape hatches.
- Performance: SSR compatibility; tree‑shaking; RSC readiness.
- Docs & Ecosystem: examples; maintenance; TypeScript coverage.

Setup Notes
- Tailwind config: define color scales, spacing, and typography tokens.
- shadcn/ui: pin component versions; curate a local library to avoid drift.
- Global styles: respect `prefers-reduced-motion`; strong focus rings.

Lint/Format
- Prettier + ESLint (eslint-config-next) + Tailwind plugin; enforce import/order.
