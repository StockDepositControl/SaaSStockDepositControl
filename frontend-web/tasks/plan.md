# Technical Implementation Plan: Reports UI Screen (Phase 1)

**Reference Spec:** `specs/SPEC-reports-ui-screen.md`

## 1. Components & Dependencies
- `app/reportes/page.tsx`: Page layout and state manager.
- Reusable UI Components: `SummaryKPICard`, `EmptyState`, `ReportSkeleton`.
- Tab Views: `ShrinkageReportTab`, `GoodsReceivedReportTab`, `NetInventoryBalanceTab`, `AuditHistoryTab`.
- Dependencies: Requires a charting library (e.g., Recharts) for Tab 3.

## 2. Implementation Order
1. **Foundation:** Create the route (`app/reportes/page.tsx`), define the layout with the Global Filters (defaulting to 7 days), and establish the Tabbed Navigation state.
2. **Shared UI Atoms:** Implement `SummaryKPICard` (with loss accent logic), `EmptyState`, and `ReportSkeleton`.
3. **Tab 1 & 2 (Tables & KPIs):** Implement `ShrinkageReportTab` and `GoodsReceivedReportTab` ensuring monospaced fonts and right alignment for data tables.
4. **Tab 3 (Charts):** Add the charting library and build `NetInventoryBalanceTab`.
5. **Tab 4 (Audit):** Implement `AuditHistoryTab` table.

## 3. Risks & Mitigations
- **Monospaced Fonts not aligning:** Ensure the CSS class (`font-mono` or specific project font) is applied exactly to the container of the value, and `text-right` is applied.
- **Active State colors:** Hardcode or reference the specific `#0F2C59` and `#EF4444` in Tailwind config or inline if needed, to avoid AI default purples or reds on backgrounds.

## 4. Verification Checkpoints
- Checkpoint 1: Route loads with Tabs and Global Filters (Verify 7 days default and active tab styling).
- Checkpoint 2: All tables render with exact typography constraints (Monospace, right align).
- Checkpoint 3: Chart renders correctly and empty states toggle properly.
