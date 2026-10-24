# Spec: Catalog UI Improvements

## Objective
Enhance the layout and readability of the Catalog Screen by applying established UX/UI principles:
1. **Search Bar Layout**: Give the main text input field for search more visual prominence and space. It currently feels compressed by adjacent dropdown filters. Assigning a larger flexible width (e.g., using `flex-grow` or a wider baseline width) will make the search interaction more inviting.
2. **Numeric Column Alignment**: Right-align all numeric values (e.g., "STOCK", "PRICE", "COST") in the data table. Right-aligning numbers is a standard typographic practice that makes comparing magnitudes and scanning digits much easier for the user.

## Tech Stack
- Framework: Next.js (App Router)
- UI Library: Tremor (for DataTables, TextInput, Select)
- Styling: Tailwind CSS & `shared/design-tokens/`

## Commands
- Build: `npm run build`
- Dev: `npm run dev`
- Lint: `npm run lint`

## Project Structure
- `frontend-web/app/catalog/` → Catalog pages (Admin, Supervisor, Auditor views)
- `frontend-web/components/` → Shared UI components (specifically the search/filter bar and the DataTable component)

## Code Style
- **Flexbox Utility Classes**: Use Tailwind flexbox utilities (e.g., `flex-1`, `flex-grow`, `w-full`) to manage the spatial relationship between the search input and the dropdown filters, ensuring the layout remains responsive.
- **Table Cell Alignment**: Use Tremor's built-in column alignment properties or Tailwind's `text-right` utility on the cell content to handle the numeric alignment.

## Testing Strategy
- Verify the search bar layout on desktop, tablet, and mobile viewports. On smaller screens, the search bar and filters might need to stack (`flex-col`) rather than remaining in a single row.
- Ensure the right-alignment applies to all numeric column headers (e.g., "STOCK", "PRICE", "COST") and their data cells beneath them, so titles and values align correctly.

## Boundaries
- **Always do:** 
  - Ensure changes to the DataTable component don't break other screens that might consume the same shared component. If the DataTable is shared, ensure column alignment can be passed as a configuration or prop per column.
  - Implement role-aware checks. If other numeric columns are right-aligned, ensure role restrictions (like hiding cost for non-admins) are maintained structurally.
- **Ask first:** 
  - If making the search bar wider causes the dropdown filters to wrap awkwardly on mid-sized tablet screens, ask for preferred breakpoint wrapping behavior.
- **Never do:** 
  - Use fixed pixel widths (like `w-[600px]`) for the search bar, as this will break responsive layouts.

## Success Criteria
- The Search text input visibly occupies more horizontal space than the individual dropdown filters in the desktop view.
- All numeric column headers (e.g., "STOCK", "PRICE", "COST") and their corresponding data cells are perfectly right-aligned.
- The layout remains unbroken and fully responsive on mobile devices.

