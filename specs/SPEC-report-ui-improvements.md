# Spec: Report UI Improvements

## Objective
Refine the visual hierarchy and color semantics of the Report Screen to reduce alert overload and improve navigation clarity:
1. **Navigation Semantics (Tabs)**: Update the active tab state (e.g., "Financial Shortfalls") to use the corporate Primary Blue (`#0F2C59`) instead of red. Red must be reserved strictly for negative data or losses within the content itself, not for navigation states.
2. **Reducing Alert Overload**: 
   - **Table Headers**: Ensure the "TOTAL LOSS" table header uses the same neutral/gray color as other columns, rather than being red.
   - **Summary Card Styling**: Remove the full red border on the "TOTAL PERIOD LOSS" card. Instead, apply a thick accent line on the left edge (e.g., `border-l-4 border-l-red-500`), ensuring the numerical value itself remains the primary vibrant red element.

## Tech Stack
- Framework: Next.js (App Router)
- UI Library: Tremor (for Tabs, Cards, DataTables)
- Styling: Tailwind CSS & `shared/design-tokens/`

## Commands
- Build: `npm run build`
- Dev: `npm run dev`
- Lint: `npm run lint`

## Project Structure
- `frontend-web/app/reports/` → Reports Screen
- `frontend-web/components/` → Shared UI components (Tabs, KPIs, DataTable)
- `shared/design-tokens/` → Colors and Semantic variables

## Code Style
- **Color Semantics**: Strictly use `shared/design-tokens/` or Tailwind configured semantic colors. For example, use a primary brand color class (e.g., `text-brand-900`) for the active tab, and `text-danger-500` only for negative numerical data.
- **Card Accent**: Use Tailwind border utilities for the left edge accent (`border-l-4 border-l-danger-500`) rather than custom CSS.

## Testing Strategy
- Switch between different tabs to verify the active state uses the Primary Blue and non-active states use their appropriate neutral color.
- Check the table column headers to ensure "TOTAL LOSS" is visually consistent with the rest of the neutral headers.
- Visually inspect the "TOTAL PERIOD LOSS" card to ensure it doesn't feel overwhelming but still clearly communicates a negative/alert metric.

## Boundaries
- **Always do:**
  - Adhere to the established color semantics (Blue for navigation/active, Red for data/loss, Gray for structural text).
  - Use Tremor's built-in properties on Tabs or override them properly if they default to an unwanted color.
  - The Primary Blue (`#0F2C59`) is currently **not** defined in the project. You must add it to the Tailwind config or `shared/design-tokens/` (e.g., as `brand-primary`) before using it.
- **Never do:**
  - Hardcode raw hex values (`#0F2C59` or red hex codes) directly into the component's JSX or `className`.
  - Apply the red alert styling to non-negative/informational KPI cards.

## Success Criteria
- The Primary Blue (`#0F2C59`) is added to the design system and/or Tailwind config.
- The "Financial Shortfalls" tab (and any active tab) uses Primary Blue when selected.
- The "TOTAL LOSS" table header is gray/neutral, perfectly matching adjacent headers.
- The "TOTAL PERIOD LOSS" card features a thick left border accent, avoiding a heavy full border.
- The actual numerical loss value within the card is vibrant red text.
