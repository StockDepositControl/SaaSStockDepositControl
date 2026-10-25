# Spec: Dashboard KPI Iconography Consistency

## Objective
Enhance the visual consistency and premium feel of the Dashboard's summary KPI cards. Currently, the icons in the top-right corner (clipboard, $ symbol, and alert) have varying proportions and container styles. The goal is to standardize the icon container size using a uniform soft-edged square (`rounded-xl`) shape and ensure consistent icon line weights across all cards using Lucide React props, creating a unified and cohesive visual family.

## Tech Stack
- Framework: Next.js (App Router)
- UI Library: Tremor (for KPI Cards structure)
- Icons: Lucide React
- Styling: Tailwind CSS & `shared/design-tokens/`

## Commands
- Build: `npm run build`
- Dev: `npm run dev`
- Lint: `npm run lint`

## Project Structure
- `frontend-web/app/dashboard/` → Dashboard pages and layouts
- `frontend-web/components/` → Shared UI components (specifically the KPI Card and its icon container)
- `shared/design-tokens/` → Design System Tokens (colors, spacing, radiuses)

## Code Style
- **DRY (Don't Repeat Yourself)**: Extract the KPI icon container into a single reusable UI component (e.g., `IconContainer` or within a `KpiCard` component) rather than applying utility classes inline on every single card.
- **Strict Dimensionality & Shape**: Apply strict Tailwind spacing and sizing tokens (e.g., `w-10 h-10 p-2`) to ensure uniform dimensions, and use `rounded-xl` for the soft-edged square container shape.
- **Consistent Stroke**: Enforce a standard stroke width across all icons by passing the `strokeWidth` prop to the Lucide React components (e.g., `strokeWidth={2}`). 

## Testing Strategy
- Visually inspect the Dashboard on desktop, tablet, and mobile viewports to ensure the icon containers do not distort or break layout under flex constraints.
- Verify that both the `DashboardAdminScreen` and `DashboardAuditorScreen` correctly consume the newly standardized KPI cards without divergence.

## Boundaries
- **Always do:** 
  - Ensure the standardized container adapts to the semantic context of its card (e.g., a subtle red background for the alert icon, subtle green for a success metric) while maintaining identical physical dimensions and border-radius.
  - Rely exclusively on `shared/design-tokens/` or the Tailwind config for sizing, rounding, and color palettes.
- **Ask first:** 
  - If the existing SVGs are vastly different in internal viewbox scaling and cannot be visually harmonized through CSS `stroke-width`, request uniform SVG assets from Figma.
- **Never do:** 
  - Hardcode raw pixel dimensions (`width="42px"`) or use arbitrary paddings that break the grid.
  - Duplicate the icon container styling block across multiple cards.

## Success Criteria
- All summary cards on the Dashboard feature identical container proportions (width, height, and border-radius) for their top-right icons.
- The stroke weight of all icons (clipboard, $ symbol, alert) looks identical to the eye.
- The icon container logic is centralized, meaning a future size adjustment requires changing only one component or token.

