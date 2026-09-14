- [ ] Task: Set up `/reportes` route and main layout
  - Acceptance: Page renders with a Global Filter bar (defaulting to last 7 days) and empty tab navigation.
  - Verify: Visit `/reportes` and check the date filter.
  - Files: `app/reportes/page.tsx`, `components/reportes/GlobalFilters.tsx`

- [ ] Task: Implement Tabbed Navigation and Shared Components
  - Acceptance: `ReportsTabNavigation` allows switching between 4 tabs. Active tab is `#0F2C59`. `SummaryKPICard`, `EmptyState`, and `ReportSkeleton` are created.
  - Verify: Click through tabs and verify styling.
  - Files: `app/reportes/page.tsx`, `components/reportes/ReportsTabNavigation.tsx`, `components/reportes/SummaryKPICard.tsx`, `components/reportes/EmptyState.tsx`, `components/reportes/ReportSkeleton.tsx`

- [ ] Task: Implement Shrinkage and Financial Loss Tab
  - Acceptance: Tab 1 renders KPI card (with red left border) and table. Barcodes and currency are right-aligned monospace.
  - Verify: Render with mock data and check alignment/colors.
  - Files: `components/reportes/ShrinkageReportTab.tsx`

- [ ] Task: Implement Inbound and Addition Valuation Tab
  - Acceptance: Tab 2 renders KPI card (no red border) and table. Same typography constraints apply.
  - Verify: Render with mock data.
  - Files: `components/reportes/GoodsReceivedReportTab.tsx`

- [ ] Task: Setup Charting and Implement Daily Net Inventory Balance Tab
  - Acceptance: Chart library is installed/used. Tab 3 renders a summary chart and KPI card for Net Asset Variation.
  - Verify: Chart renders properly and resizes.
  - Files: `package.json`, `components/reportes/NetInventoryBalanceTab.tsx`

- [ ] Task: Implement Audit History Tab
  - Acceptance: Tab 4 renders the immutable traceability table.
  - Verify: Render with mock data.
  - Files: `components/reportes/AuditHistoryTab.tsx`
