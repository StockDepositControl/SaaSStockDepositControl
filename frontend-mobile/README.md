# Audit Global — Field Auditing Mobile App (`frontend-mobile`)

React Native & Expo mobile client for **Audit Global (SaaS Stock Deposit Control)**. Purpose-built for warehouse floor operators (`auditor` and `supervisor`) to inspect stock positions, verify FEFO lot expiration dates, scan barcodes, and register physical stock counts with zero exposure to confidential financial or unit-cost metrics.

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| **Mobile SDK** | Expo (`expo`, `expo-status-bar`) | `~57.0.2` / `~57.0.0` |
| **Runtime** | React Native | `0.86.0` |
| **UI Library** | React | `19.2.3` |
| **Language** | TypeScript | `~6.0.3` |
| **Styling** | NativeWind (Tailwind CSS) + React Native `StyleSheet` | `^4.2.6` |
| **Local Storage** | `@react-native-async-storage/async-storage` | `2.2.0` |

---

## Role-Aware Field Architecture & Security

The mobile application enforces strict operational and security boundaries tailored for warehouse floor devices:

1. **Field-Only Role Enforcement (`auditor` & `supervisor`)**:
   - During authentication in [`src/adapters/apiMobileDataClient.ts`](src/adapters/apiMobileDataClient.ts) and [`src/adapters/mockMobileDataClient.ts`](src/adapters/mockMobileDataClient.ts), the decoded JWT role is validated before establishing a session.
   - Only `auditor` and `supervisor` roles are permitted to sign in on mobile. Accounts with the `administrador` role (or unrecognized roles) are rejected at login with an explicit operational access error.
2. **Zero Financial Leakage (`stripFinancialFields`)**:
   - In addition to backend RBAC filtering, `ApiMobileDataClient` runs a recursive defensive sanitizer (`stripFinancialFields`) on every incoming JSON payload (`searchArticles`, `getArticleCatalog`, `getArticleStockPosition`, `registerAudit`).
   - Any occurrence of `pcio_com_siva`, `monto_valorizado`, or `applied_unit_cost` is stripped before data enters React state or UI components.
3. **Tenant-Scoped Session Persistence & Server Change Protection**:
   - Authenticated sessions (`ActiveTenantSession`) are stored in `AsyncStorage` under the composite key `audit_global:session:{tenantId}:{branchId}` (`STORAGE_KEYS.SESSION_PREFIX`).
   - On app startup, `restoreSession()` validates the stored token's expiration timestamp (`expiresAtMs > Date.now()`) before restoring the operator's session.
   - Changing the server URL via [`ServerSettingsModal.tsx`](src/components/ServerSettingsModal.tsx) automatically clears stored JWT and session keys so credentials are never sent to a different server.
4. **Dynamic Runtime Server Discovery & LAN Cleartext Support**:
   - [`src/utils/serverUrl.ts`](src/utils/serverUrl.ts) resolves the backend URL dynamically per call: in-memory cache $\rightarrow$ `AsyncStorage` (`@stock_server_url`) $\rightarrow$ `EXPO_PUBLIC_API_URL` $\rightarrow$ `http://localhost:8000`.
   - `app.json` enables `android.usesCleartextTraffic: true` (via `expo-build-properties`) and `ios.infoPlist.NSAppTransportSecurity.NSAllowsArbitraryLoads: true` so devices can connect to on-premise pharmacy servers over plain HTTP Wi-Fi LAN (`http://<lan-ip>:8080`) while using native camera permissions.

---

## Navigation & Screens

Navigation is managed by a lightweight, state-driven navigator in [`src/navigation/AppNavigator.tsx`](src/navigation/AppNavigator.tsx) paired with [`src/context/AuthContext.tsx`](src/context/AuthContext.tsx):

- **Unauthenticated Flow**: Renders [`LoginScreen.tsx`](src/screens/LoginScreen.tsx) when no valid `ActiveTenantSession` is active, including the **Configuración del Servidor** link that opens [`ServerSettingsModal.tsx`](src/components/ServerSettingsModal.tsx).
- **Authenticated Shell**: Wraps active screens with [`TopAppBar.tsx`](src/components/layout/TopAppBar.tsx) and the slide-over [`SidebarDrawer.tsx`](src/components/layout/SidebarDrawer.tsx), switching across three primary `ScreenRoute` states (`'Dashboard' | 'AuditArticle' | 'Catalog'`):

| Route / Screen | Source File | Key Capabilities |
|---|---|---|
| **Login & Server Setup** | `src/screens/LoginScreen.tsx`<br/>`src/components/ServerSettingsModal.tsx` | Email/password authentication, role-restriction feedback banner, and runtime server URL configuration (**Probar Conexión** probes `/api/v1/health` with an 8s timeout before enabling **Guardar**). |
| **`Dashboard`** | `src/screens/DashboardScreen.tsx` | Operator greeting, pull-to-refresh daily audit progress card (`getDailyProgress`: audited, pending, total, completion `%`), and quick navigation cards to start auditing or browse the catalog. |
| **`AuditArticle`** | `src/screens/AuditArticleScreen.tsx` | Barcode/text search bar (`SearchScannerBar`), camera barcode scanner modal (`BarcodeScannerModal`), article & FEFO lot inspection card (`ArticleInspectionCard`), physical count stepper (`CountedQuantityInput`), conditional discrepancy motive selector (`MotiveSelectSheet`), and audit submission (`registerAudit`). |
| **`Catalog`** | `src/screens/CatalogScreen.tsx` | Searchable warehouse catalog (`CatalogItemCard`) with status filters (`all`, `pending`, `audited`) and critical out-of-stock filtering (`stock_real === 0`) via `CatalogFilterSheet`. Selecting an item opens it directly in `AuditArticle`. |

---

## Hexagonal Data Layer & Pure Domain Services

### 1. Data Client Port (`src/ports/MobileDataClientPort.ts`)
Defines the boundary between React Native screens and data sources:
- `login(credentials: LoginCredentials): Promise<ActiveTenantSession>`
- `logout(): Promise<void>`
- `restoreSession(): Promise<ActiveTenantSession | null>`
- `getDailyProgress(): Promise<AuditDailyProgress>`
- `searchArticles(query: string): Promise<ArticuloAuditorView[]>`
- `getArticleCatalog(params?: CatalogFilterParams): Promise<CatalogResult<ArticuloAuditorView>>`
- `getArticleStockPosition(articleId: string, depositId?: number): Promise<ArticleStockPositionView>`
- `registerAudit(request: AuditEntryRequest): Promise<AuditEntryResult>`

### 2. Adapters (`src/adapters/`) & Context Wiring (`src/context/DataContext.tsx`)
- **`apiMobileDataClient.ts`**: Live HTTP adapter communicating with the FastAPI backend (`/api/v1/auth/login`, `/api/v1/articles`, `/api/v1/articles/search`, `/api/v1/stock/position`, `/api/v1/stock/audit`) using `getServerUrl()`, Bearer JWT headers, and financial field sanitization.
- **`mockMobileDataClient.ts`**: Offline-ready, stateful in-memory adapter seeded with pharmaceutical inventory items and FEFO lots for standalone field demos and testing.
- **`DataContext.tsx` & `src/utils/constants.ts`**: `DataProvider` selects `mockMobileDataClient` when `EXPO_PUBLIC_USE_MOCK === 'true'`, or `apiMobileDataClient` resolving its URL dynamically via `getServerUrl()`.

### 3. Pure Domain Services (`src/services/domain/`)
- **`DeltaCalculator.ts`**: Computes `deltaStock`, `affectedQuantity`, `actionType` (`'Alta' | 'Baja' | 'Sin Acción'`), and `requiresMotive` (`deltaStock !== 0`) from baseline stock and counted quantity.
- **`AuditValidator.ts`**: Validates integer counted quantities (`>= 0`), enforces mandatory discrepancy motive selection when `deltaStock !== 0`, and caps observation notes at 255 characters.
- **`FefoEvaluator.ts`**: Evaluates lot expiration dates (`YYYY-MM-DD` or `DD/MM/YYYY`) against the current date and classifies FEFO risk into `EXPIRED` (`VENCIDO`, `< 0` days), `PROXIMO` (`PRÓXIMO`, `<= 90` days), `SAFE` (`> 90` days), or `NONE`.

---

## Quick Start & Commands

### 1. Install Dependencies
```bash
cd frontend-mobile
npm ci
```

### 2. Environment Configuration
You can configure the fallback backend URL and mock mode via environment variables (or configure the server URL at runtime on the Login screen via **Configuración del Servidor**):
```env
# Fallback base URL of the FastAPI backend (overridden at runtime by @stock_server_url in AsyncStorage)
EXPO_PUBLIC_API_URL=http://localhost:8000

# Set to "true" to use the offline in-memory MockMobileDataClient
EXPO_PUBLIC_USE_MOCK=false
```

### 3. Verify & Run the Application

| Command | Description |
|---|---|
| `npx tsc --noEmit` | Run strict TypeScript typechecking |
| `npx expo-doctor` | Verify Expo SDK package compatibility and project health |
| `npx expo start` / `npm start` | Start the Expo Metro bundler and interactive CLI |
| `npx expo start --android` / `npm run android` | Launch on an Android emulator or connected device |
| `npx expo start --ios` / `npm run ios` | Launch on an iOS simulator or connected device |
| `npx expo start --web` / `npm run web` | Launch in a web browser via Expo Web |
