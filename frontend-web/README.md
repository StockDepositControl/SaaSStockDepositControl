# Audit Global — Web Application (`frontend-web`)

Enterprise Next.js web console for **Audit Global (SaaS Stock Deposit Control)**. Provides role-based warehouse inventory control, barcode-driven physical stock auditing, executive financial analytics, and multi-tenant user & role administration.

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| **Framework** | Next.js (App Router, `output: "standalone"`) | `^16.4.3` |
| **UI Library** | React / React DOM | `19.2.4` |
| **Language** | TypeScript | `^5` |
| **Styling** | Tailwind CSS v4 (`@tailwindcss/postcss`) | `^4` |
| **Icons** | `lucide-react` | `^1.32.0` |
| **Barcode Scanner** | `html5-qrcode` + Native `BarcodeDetector` | `^2.3.8` |
| **Test Runner** | Vitest + React Testing Library (`jsdom`) | `^2.1.8` / `^16.3.3` |

---

## Application Routes (`app/`)

| Route | Source File | Access Level | Description |
|---|---|---|---|
| `/` | `app/page.tsx` | Public | Root entry point that redirects unauthenticated visitors to `/login`. |
| `/login` | `app/login/page.tsx` | Public | JWT authentication login screen (`POST /api/v1/auth/login`). Decodes role, tenant, and branch claims and redirects to `/dashboard`. |
| `/dashboard` | `app/dashboard/page.tsx` | All authenticated roles | Executive & operational KPI summary (`getKPIs` / `GET /api/v1/stock/kpis`), audit progress bar, out-of-stock critical alerts, role-specific metrics (financial shrinkage valuation for `administrador`, unit deficit & session counters for `supervisor` / `auditor`), and quick-action navigation cards. |
| `/catalog` | `app/catalog/page.tsx` | All authenticated roles | Master article catalog with multi-criteria search, barcode lookup, stock position inspection, FEFO expiration status, and strict RBAC field projection (`pcio_com_siva` unit cost column is rendered and populated exclusively for `administrador`). |
| `/audit` | `app/audit/page.tsx` | All authenticated roles | Physical stock deposit audit registration (`registerAudit` / `POST /api/v1/stock/audit`), live camera barcode scanner modal (`BarcodeScannerModal` powered by `html5-qrcode`), debounced autocomplete search, FEFO lot verification, and real-time discrepancy delta calculation (`ALTA`, `BAJA`, `SIN_ACCION`). |
| `/reports` | `app/reports/page.tsx` | `administrador` only | Executive analytical and financial reports module with date-range filtering (`GlobalFilters`), JSON export, and specialized tabs under `components/reportes/`: `ShrinkageReportTab` (`/api/v1/reports/shrinkage`), `GoodsReceivedReportTab` (`/api/v1/reports/goods-received`), `NetInventoryBalanceTab` (`/api/v1/reports/inventory-balance`), and `AuditHistoryTab`. Non-admin users see an `Acceso Restringido` guard view. |
| `/users` | `app/users/page.tsx` | `administrador` only | Administrator User Management & Role Assignment module. Lists tenant users (`GET /api/v1/users`), displays live KPI counters (total, active, inactive, and role breakdown), toggles active/inactive account status (`PATCH /api/v1/users/{id}/status`) with optimistic UI rollback and self-lockout protection, and assigns single operational roles (`PUT /api/v1/users/{id}/roles` for `administrador`, `supervisor`, `auditor`) with self-demotion guards. |
| `/debug` | `app/debug/page.tsx` | Diagnostic / Dev | Interactive diagnostic console for inspecting active JWT/badge tokens, switching mock identities, verifying DTO-level cost masking across roles, and triggering in-memory or live audit mutations. |

---

## Hexagonal Data Client Architecture (`lib/`)

The web client follows a strict **Ports and Adapters (Hexagonal)** architecture so UI components and pages remain decoupled from transport details and can run against either the live FastAPI backend or an in-memory deterministic store.

```
[ Next.js App Router Pages & Components ]
                   │
                   ▼
          [ useDataClient() ]
                   │
                   ▼
      [ lib/ports/DataClientPort.ts ]
                   │
     ┌─────────────┴─────────────┐
     ▼                           ▼
[ ApiDataClient.ts ]    [ MockDataContext.tsx ]
 (Live REST + JWT)       (Stateful In-Memory Seed)
```

### 1. Port Contract (`lib/ports/DataClientPort.ts`)
Defines the TypeScript interface consumed across hooks and screens:
- **Authentication & Session:** `login(email, password)`, `logout()`, `getCurrentUser()`, `getCurrentRole()`, `setRole(role)`, `switchUser(userId)`
- **Catalog & Stock Lookup:** `getArticulos(role)` (`getArticles`), `getArticuloByBarcode(barcodeOrId, role)`, `searchArticulos(query, role)` (`searchArticles`)
- **Stock Auditing & KPIs:** `registerAudit(entry)` (`submitAudit`), `getKPIs(role)` (`getDashboardKPIs`), `getAuditLog()`
- **User & Role Administration:** `getUsers(includeInactive)`, `updateUserStatus(userId, isActive)`, `updateUserRole(userId, role)` (`assignUserRoles`)
- **Diagnostics:** `resetData()`

### 2. Live API Adapter (`lib/adapters/ApiDataClient.ts` & `lib/adapters/httpClient.ts`)
- **`httpClient.ts`**: Lightweight `fetch` wrapper that normalizes query parameters, serializes JSON bodies, automatically attaches `Authorization: Bearer <token>` from `localStorage`, and intercepts `401 Unauthorized` responses to clear stale credentials and redirect to `/login`.
- **`ApiDataClient.ts`**: Connects to FastAPI endpoints (`/api/v1/auth/login`, `/api/v1/articles`, `/api/v1/articles/search`, `/api/v1/stock/audit`, `/api/v1/stock/kpis`, `/api/v1/users`, `/api/v1/users/{id}/status`, `/api/v1/users/{id}/roles`).
- **`mappers.ts`**: Whitelist domain mappers (`mapArticleByRole`, `mapToDomainAuditResult`, `mapToDomainUser`) that enforce client-side defense-in-depth by stripping `pcio_com_siva` whenever the active role is not `administrador`.
- **Analytical Reports (`/reports`)**: Queries `/api/v1/reports/shrinkage`, `/api/v1/reports/goods-received`, and `/api/v1/reports/inventory-balance` via `httpClient` with automatic fallback to session audit logs if offline.

### 3. Stateful Mock Adapter (`lib/mocks/MockDataContext.tsx`)
- Provides `MockDataProvider` backed by `lib/mocks/seed-data.ts`.
- Replicates backend domain rules in memory: role-based cost stripping (`projectArticleForRole`), VAT calculation (`0%` for `Medicamentos`, `21%` for other families), audit delta classification, and anti-lockout / self-demotion invariants in `updateUserStatus` and `updateUserRole`.

### 4. Provider Switching & Single-Origin Routing (`app/providers.tsx`)
Controlled via environment variables:
- `NEXT_PUBLIC_DATA_SOURCE`: Set to `api` (default) to mount `ApiDataProvider`, or `mock` to mount `MockDataProvider`.
- `NEXT_PUBLIC_API_URL`: Defaults to `""` (empty string) so requests use relative `/api/v1/*` paths behind the Caddy single-origin reverse proxy (set `http://localhost:8000` only when running `npm run dev` on the host without a reverse proxy).

### 5. Camera Barcode Scanner Lifecycle (`lib/hooks/`)
- **`useCameraPermissions.ts`**: Uses `navigator.permissions.query({ name: "camera" })` fast-path to avoid redundant stream probes when permission is already granted, requests `{ facingMode: { ideal: "environment" } }`, and enforces a `150ms` hardware abstraction layer (HAL) release delay after stopping stream tracks.
- **`useBarcodeScanner.ts`**: Leverages native `BarcodeDetector` when supported, restricts scan formats to `EAN_13`, `EAN_8`, `CODE_128`, and `QR_CODE` at `10 fps`, clamps `computeQrbox` dimensions on narrow viewports, and serializes start/stop transitions with a promise mutex (`startPromiseRef` / `stopPromiseRef`).

---

## Shared Design System

Visual foundations are shared across web and mobile via [`../shared/design-tokens/index.ts`](../shared/design-tokens/index.ts):
- **Surfaces & Palette**: Deep slate backgrounds, brand accent indigo/blue (`#1a56db` / `#6366F1`), and high-contrast slate typography.
- **Semantic Audit Tokens**: Standardized colors and badges for `alta` (surplus), `baja` (shrinkage/deficit), `sinAccion` (exact match), FEFO expiration tiers (`critical` ≤30d, `warning` ≤60d, `attention` ≤90d, `safe` >90d), and role badges (`administrador`, `supervisor`, `auditor`).
- **Typography & Spacing**: Geist Sans & Geist Mono font variables, responsive container widths (`1440px`), and collapsible sidebar dimensions (`260px` expanded / `72px` collapsed).

---

## Quick Start & Environment Configuration

### 1. Install Dependencies
```bash
cd frontend-web
npm ci
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env.local`:
```bash
cp .env.example .env.local
```

Configure the variables in `.env.local`:
```env
# Leave empty behind the Caddy single-origin reverse proxy, or set to http://localhost:8000 for direct host dev
NEXT_PUBLIC_API_URL=

# Data adapter mode: "api" (live FastAPI backend) or "mock" (in-memory demo store)
NEXT_PUBLIC_DATA_SOURCE=api
```

### 3. Start the Development Server
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) (or [http://localhost:8080](http://localhost:8080) when running behind Caddy) in your browser.

---

## Available Scripts & Testing

| Command | Description |
|---|---|
| `npm run dev` | Start the Next.js development server on port `3000` |
| `npm run build` | Compile the standalone Next.js production build (`.next/standalone/server.js`) |
| `npm start` | Start the production server after `npm run build` |
| `npx tsc --noEmit` | Run strict TypeScript typechecking |
| `npm run lint` | Run ESLint across the project |
| `npm test` / `npx vitest run` | Run the Vitest unit and component integration test suite |
| `npm audit --audit-level=high` | Audit dependencies for high/critical vulnerabilities |

### Test Suite Coverage
Automated tests run in `jsdom` via Vitest (`vitest.config.ts`) and cover:
- **HTTP, Config & Adapter Layer**: `next.config.test.ts`, `lib/adapters/httpClient.test.ts`, `lib/adapters/ApiDataClient.test.ts`, `lib/adapters/mappers.test.ts`, `lib/utils/jwt.test.ts`
- **Camera & Scanner Hooks**: `lib/hooks/useCameraPermissions.test.ts`, `lib/hooks/useBarcodeScanner.test.ts`
- **Context & Session Providers**: `lib/context/ApiDataContext.test.tsx`, `lib/mocks/__tests__/MockDataClient.test.tsx`
- **UI Pages & Workflows**: `app/users/page.test.tsx` (RBAC access guard, status toggles, single-role assignment, anti-lockout guards, optimistic rollback), `app/audit/__tests__/AuditPage.test.tsx`, `components/scanner/__tests__/BarcodeScannerModal.test.tsx`
