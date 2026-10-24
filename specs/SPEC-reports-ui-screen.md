# Spec: Reports UI Screen (Phase 1)

## Objective
Implement the new `/reportes` screen for Administrators. The screen will aggregate various financial and inventory reports provided by the backend, displayed within a tabbed interface. This Phase 1 focuses on building the layout, navigation, global filters, and the first four reports, explicitly excluding the FEFO Risk Traffic Light.

## Tech Stack
- Frontend: Next.js (App Router), React
- Styling: Tailwind CSS
- Data Fetching: Standard project defaults (e.g., SWR, React Query, or fetch)
- Charting: Any suitable charting library (e.g., Recharts, Chart.js)

## Commands
```bash
# Run from frontend-web directory
npm run dev
npm run build
npm run lint
```

## Project Structure
```text
frontend-web/
  app/reportes/
    page.tsx                      -> Main layout and route
  components/reportes/
    ReportsTabNavigation.tsx      -> Tab selector
    GlobalFilters.tsx             -> Date range (default last 7 days) & Export button
    SummaryKPICard.tsx            -> Reusable KPI card (white bg, optional red left-border for loss)
    ShrinkageReportTab.tsx        -> Tab 1
    GoodsReceivedReportTab.tsx    -> Tab 2
    NetInventoryBalanceTab.tsx    -> Tab 3 (includes chart)
    AuditHistoryTab.tsx           -> Tab 4
    EmptyState.tsx                -> Reusable empty state view
    ReportSkeleton.tsx            -> Loading skeleton
```

## Code Style
```tsx
export function SummaryKPICard({ title, amount, quantity, isLoss }: Props) {
  return (
    <div className={`bg-white p-4 rounded-lg shadow-sm border ${isLoss ? 'border-l-4 border-l-red-500' : 'border-gray-200'}`}>
      <h3 className="text-sm font-medium text-gray-500">{title}</h3>
      <div className="mt-2 flex justify-between items-baseline">
        <span className="text-2xl font-semibold font-mono text-right">${amount}</span>
        <span className="text-sm text-gray-400">{quantity} units</span>
      </div>
    </div>
  );
}
```

## Testing Strategy
- Manual verification of responsive layout, visual alignment, empty states, and tab switching.
- Verify exact color codes for active tabs (Primary Blue `#0F2C59`) and loss accents (Red `#EF4444`).

## Boundaries
- **Always do:**
  - Default global date filter to "last 7 days".
  - Use monospaced font for barcodes and currency ($).
  - Right-align numeric data in tables.
  - Active tab text/border must be Primary Blue (`#0F2C59`). No red for active states.
  - Loss cards must use a left red border (`#EF4444`) with a Pure White (`#FFFFFF`) background.
- **Ask first:** 
  - Adding new heavy dependencies for charting if a lightweight one exists.
- **Never do:** 
  - Implement the "FEFO Risk Traffic Light" tab in this phase.
  - Hide columns based on roles (this screen is exclusively for Administrators).
  - Use red-tinted backgrounds for loss cards.

## Success Criteria
- [ ] Global Date Filter (defaulting to last 7 days) and Export button are present and sticky/fixed.
- [ ] Four tabs are implemented, navigable, and styled correctly:
  1. Shrinkage and Financial Loss Report
  2. Inbound and Addition Valuation Report
  3. Daily Net Inventory Balance (with summary chart)
  4. Audit History (Audit Trail)
- [ ] All currency values and barcodes use monospaced fonts and right alignment.
- [ ] Empty states (icon + message + clear button) and Skeletons are visually complete and responsive.
