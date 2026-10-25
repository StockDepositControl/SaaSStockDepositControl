# Spec: Frontend UX/UI Improvements

## Objective
Enhance the user experience and interface of the SaaS Stock Deposit Control frontend web application by applying key UX/UI principles:
1. **Status Badge Contrast**: Improve the contrast of the "PENDING" status badge in the Catalog by applying the semantic warning color (Yellow/Orange #F59E0B) from the design system, replacing the low-contrast light gray background. This will distinguish it clearly from "AUDITED" (green).
2. **Monospaced Typography for Hard Data**: Use a monospaced font (like JetBrains Mono) exclusively for the "CODE" column and monetary values across tables. This ensures vertical alignment of numbers, improving scannability.
3. **Interactivity (Affordance)**: Add hover effects (e.g., shadow lift, subtle background color change) and a directional icon (e.g., `→` in the bottom-right corner) to the "QUICK ACCESS" cards on the Dashboard to clearly communicate their clickability.

## Tech Stack
- Framework: Next.js (App Router)
- UI Library: Tremor
- Language: TypeScript
- Styling: Tailwind CSS & `shared/design-tokens/`

## Commands
- Build: `npm run build`
- Dev: `npm run dev`
- Lint: `npm run lint`

## Project Structure
- `frontend-web/` → Frontend Application Source Code
  - `app/` → Next.js App Router Pages
  - `components/` → Shared UI components (e.g., StatusBadge, KPI Card, DataTable)
- `shared/design-tokens/` → Design System Tokens (Colors, Typography)

## Code Style
- Strictly consume visual values (colors, fonts, spacing) from `shared/design-tokens/` or configured Tailwind variables. Never hardcode hex colors or font strings in the UI components.
- Example: Use semantic color classes like `bg-warning` or `text-warning-600` instead of `bg-[#F59E0B]`.

## Testing Strategy
- Ensure all interactive components (like QUICK ACCESS cards) maintain accessibility (ARIA labels, focus states).
- Visually verify contrast ratios meet WCAG AA standards.
- Verify monospaced font alignment in the Catalog table on desktop and tablet viewports.

## Boundaries
- **Always do:** 
  - Consult `shared/design-tokens/` before introducing new styles.
  - Implement role-aware rendering (hide cost fields from non-admins structurally, not just visually).
- **Ask first:** 
  - If a required design token (like the warning color or JetBrains Mono) is missing from `shared/design-tokens/`.
- **Never do:** 
  - Hardcode business logic. 
  - Modify backend APIs or `frontend-mobile/`.
  - Hardcode raw colors (`#F59E0B`) directly in React components.

## Success Criteria
- The "PENDING" status badge uses the semantic warning color and is clearly distinguishable from "AUDITED".
- The "CODE" column and monetary values in tables use a monospaced font, and decimal points/characters align perfectly vertically.
- The "QUICK ACCESS" cards have a visible hover state (shadow/background shift) and an arrow icon indicating they are clickable.
- No direct hardcoded hex colors or fonts in the components; all rely on the design system/Tailwind config.

## Open Questions
- Is `JetBrains Mono` (or another monospaced font) already configured in the design system/Tailwind config, or does it need to be added?
- Do the "QUICK ACCESS" cards already use a standard card component, or are they bespoke per page?
