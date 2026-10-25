### ASSUMPTIONS I'M MAKING
1. The dedicated domain hooks will be named `useKPIs` and `useAuditLogs`, placed in `frontend-web/lib/hooks/useKPIs.ts` and `frontend-web/lib/hooks/useAuditLogs.ts` respectively, mirroring the successful architectural pattern of `useArticles.ts`.
2. The global `ApiDataContext` and `DataContext` will be completely relieved of managing `kpis` and `auditLogs`. Neither `client.getKPIs()` nor `client.getAuditLog()` will be called on root application mount, session restore, or login.
3. `useDataClient` will remove `kpis` and `auditLogs` from its return contract (`UseDataClientReturn`), focusing strictly on session, authentication, user switching, and the raw `client` port.
4. Consuming pages (`app/dashboard/page.tsx`, `app/reports/page.tsx`, `app/debug/page.tsx`) will consume `useKPIs()` and/or `useAuditLogs()` directly, loading data only when those views mount.
5. In-memory `MockDataProvider` will keep its internal seed arrays to power `client.getKPIs()` and `client.getAuditLog()`, but will stop publishing `kpis` and `auditLogs` through `DataContextValue`.

---

# Spec: Decoupling KPIs and Audit Logs into Dedicated Domain Hooks (`useKPIs`, `useAuditLogs`)

## 1. Objective
Following the zero-prefetch architecture established by `useArticles`, decouple the `kpis` and `auditLogs` state management from the monolithic `ApiDataContext` and `DataContext`.

Currently, `ApiDataContext` eagerly fetches both KPIs and Audit Logs inside `fetchBackendData()` on every session boot and user login, even if the user is on views (such as `/login`, `/audit`, or `/catalog`) where this data is not required. Furthermore, any mutation or refresh triggers an uncoordinated bulk re-fetch on the root provider, forcing re-renders across all consumers of `useDataClient`.

This specification defines the extraction of `useKPIs` and `useAuditLogs` as independent, resilient, RBAC-aware domain hooks adhering to the **Principle of Colocated State & Single Responsibility**.

---

## 2. Tech Stack
- **Framework:** Next.js 16.2.10 (App Router) + React 19.2.4
- **Language:** TypeScript 5.x
- **Testing:** Vitest 2.1.8 + React Testing Library 16.3.3 + JSDOM 29.1.1
- **Icons & Styling:** Tailwind CSS 4 + Lucide React

---

## 3. Commands
- **Dev Server:** `npm run dev` (inside `frontend-web/`)
- **Typecheck & Build:** `npm run build`
- **Linter:** `npm run lint`
- **Unit & Hook Tests:** `npm test`
- **Targeted Test Execution:** `npx vitest run lib/hooks/useKPIs.test.ts lib/hooks/useAuditLogs.test.ts lib/context/ApiDataContext.test.tsx`

---

## 4. Project Structure & Affected Surfaces
```
frontend-web/
├── lib/
│   ├── hooks/
│   │   ├── useKPIs.ts                  → [NEW] Dedicated domain hook for Dashboard KPIs with RBAC guarding
│   │   ├── useKPIs.test.ts             → [NEW] Vitest suite: lifecycle, auth guard, role-isolation, error handling
│   │   ├── useAuditLogs.ts             → [NEW] Dedicated domain hook for Audit History logs
│   │   ├── useAuditLogs.test.ts        → [NEW] Vitest suite: lifecycle, auth guard, refetching, cancellation
│   │   └── useDataClient.ts            → [MODIFY] Remove `kpis` and `auditLogs` from UseDataClientReturn
│   ├── context/
│   │   ├── DataContext.tsx             → [MODIFY] Remove `kpis` and `auditLogs` from DataContextValue
│   │   ├── ApiDataContext.tsx          → [MODIFY] Remove `kpis` / `auditLogs` states & `fetchBackendData()` calls
│   │   ├── ApiDataContext.test.tsx     → [MODIFY] Assert 0 calls to getKPIs / getAuditLog on boot or login
│   │   └── ApiDataContext.test.tsx
│   └── mocks/
│       └── MockDataContext.tsx         → [MODIFY] Keep mock client logic, remove kpis/auditLogs from contextValue
├── app/
│   ├── dashboard/
│   │   └── page.tsx                    → [MODIFY] Consume useKPIs() and useAuditLogs() directly
│   ├── reports/
│   │   └── page.tsx                    → [MODIFY] Consume useAuditLogs() directly for audit history tabs
│   └── debug/
│       └── page.tsx                    → [MODIFY] Consume useKPIs() and useAuditLogs() directly
```

---

## 5. Architectural Pattern & Code Style

CONCEPTS > CODE. Domain data should live as close to its consumption boundary as possible. The root context should only manage global infrastructure: authentication tokens, session identity, and data client port access.

### 5.1 Hook 1: `useKPIs.ts` (`lib/hooks/useKPIs.ts`)
```typescript
"use client";

import { useState, useEffect, useCallback } from "react";
import { useDataClient } from "@/lib/hooks/useDataClient";
import {
  DashboardKPIsBase,
  DashboardKPIsAdmin,
  UserRole,
} from "@/lib/types/domain";
import type { DataClientPort } from "@/lib/ports/DataClientPort";
import type { MockUser } from "@/lib/types/domain";

export const defaultKPIs: DashboardKPIsBase = {
  totalArticulos: 0,
  auditados: 0,
  pendientes: 0,
  porcentajeAvance: 0,
  discrepanciasAlta: 0,
  discrepanciasBaja: 0,
  sinAccion: 0,
};

export interface UseKPIsReturn {
  kpis: DashboardKPIsBase | DashboardKPIsAdmin;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

interface SettledKPIsResult {
  client: DataClientPort;
  currentUser: MockUser;
  currentRole: UserRole | null;
  tick: number;
  kpis: DashboardKPIsBase | DashboardKPIsAdmin;
  error: string | null;
}

export function useKPIs(overrideRole?: UserRole): UseKPIsReturn {
  const { client, currentRole, currentUser } = useDataClient();
  const [tick, setTick] = useState(0);
  const [settled, setSettled] = useState<SettledKPIsResult | null>(null);

  const effectiveRole = overrideRole ?? currentRole ?? UserRole.AUDITOR;

  useEffect(() => {
    // 🛑 Boundary Guard: Never fetch if not authenticated
    if (!currentUser) return;

    let cancelled = false;
    client
      .getKPIs(effectiveRole)
      .then((kpis) => {
        if (!cancelled) {
          setSettled({
            client,
            currentUser,
            currentRole: effectiveRole,
            tick,
            kpis,
            error: null,
          });
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const msg = err instanceof Error ? err.message : "Error cargando KPIs del dashboard";
          setSettled({
            client,
            currentUser,
            currentRole: effectiveRole,
            tick,
            kpis: defaultKPIs,
            error: msg,
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [client, effectiveRole, currentUser, tick]);

  const refetch = useCallback(async () => {
    setTick((t) => t + 1);
  }, []);

  if (!currentUser) {
    return { kpis: defaultKPIs, isLoading: false, error: null, refetch };
  }

  const isCurrent =
    settled !== null &&
    settled.client === client &&
    settled.currentUser === currentUser &&
    settled.currentRole === effectiveRole &&
    settled.tick === tick;

  // RBAC safety check: Never expose KPIs calculated for a different role or session
  const sameIdentity =
    settled !== null &&
    settled.currentUser === currentUser &&
    settled.currentRole === effectiveRole;

  return {
    kpis: sameIdentity ? settled.kpis : defaultKPIs,
    isLoading: !isCurrent,
    error: sameIdentity ? settled.error : null,
    refetch,
  };
}
```

### 5.2 Hook 2: `useAuditLogs.ts` (`lib/hooks/useAuditLogs.ts`)
```typescript
"use client";

import { useState, useEffect, useCallback } from "react";
import { useDataClient } from "@/lib/hooks/useDataClient";
import { AuditResult } from "@/lib/types/domain";
import type { DataClientPort } from "@/lib/ports/DataClientPort";
import type { MockUser } from "@/lib/types/domain";

export interface UseAuditLogsReturn {
  auditLogs: AuditResult[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

interface SettledAuditLogsResult {
  client: DataClientPort;
  currentUser: MockUser;
  tick: number;
  auditLogs: AuditResult[];
  error: string | null;
}

export function useAuditLogs(): UseAuditLogsReturn {
  const { client, currentUser } = useDataClient();
  const [tick, setTick] = useState(0);
  const [settled, setSettled] = useState<SettledAuditLogsResult | null>(null);

  useEffect(() => {
    // 🛑 Boundary Guard: Never fetch if not authenticated
    if (!currentUser) return;

    let cancelled = false;
    client
      .getAuditLog()
      .then((auditLogs) => {
        if (!cancelled) {
          setSettled({
            client,
            currentUser,
            tick,
            auditLogs,
            error: null,
          });
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const msg = err instanceof Error ? err.message : "Error cargando registros de auditoría";
          setSettled({
            client,
            currentUser,
            tick,
            auditLogs: [],
            error: msg,
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [client, currentUser, tick]);

  const refetch = useCallback(async () => {
    setTick((t) => t + 1);
  }, []);

  if (!currentUser) {
    return { auditLogs: [], isLoading: false, error: null, refetch };
  }

  const isCurrent =
    settled !== null &&
    settled.client === client &&
    settled.currentUser === currentUser &&
    settled.tick === tick;

  const sameIdentity = settled !== null && settled.currentUser === currentUser;

  return {
    auditLogs: sameIdentity ? settled.auditLogs : [],
    isLoading: !isCurrent,
    error: sameIdentity ? settled.error : null,
    refetch,
  };
}
```

### 5.3 Cleaned Global Contracts (`DataContext.tsx` & `useDataClient.ts`)

`DataContextValue` and `UseDataClientReturn` become lean and focused on identity & port access:
```typescript
export interface DataContextValue {
  client: DataClientPort;
  currentUser: MockUser | null;
  currentRole: UserRole | null;
  users: MockUser[];
  setRole: (role: UserRole) => void;
  switchUser: (userId: string) => void;
  login: (email: string, password?: string) => Promise<MockUser>;
  logout: () => void;
  isLoading?: boolean;
  error?: string | null;
  refreshData?: () => Promise<void>;
}
```

`ApiDataContext.tsx` drops `kpis` and `auditLogs` states and their associated `fetchBackendData()` calls. Registering an audit on `client` simply runs the port method:
```typescript
registerAudit: async (entry: AuditEntry): Promise<AuditResult> => {
  return await client.registerAudit(entry);
}
```

### 5.4 Consuming Pages Clean Refactoring

#### `app/dashboard/page.tsx`
```typescript
"use client";

import React, { useMemo } from "react";
import { useDataClient } from "@/lib/hooks/useDataClient";
import { useArticles } from "@/lib/hooks/useArticles";
import { useKPIs } from "@/lib/hooks/useKPIs";
import { useAuditLogs } from "@/lib/hooks/useAuditLogs";
import { UserRole, DashboardKPIsAdmin } from "@/lib/types/domain";

export default function DashboardPage() {
  const { currentUser, currentRole } = useDataClient();
  const { articles } = useArticles();
  const { kpis, isLoading: isKPIsLoading } = useKPIs();
  const { auditLogs, isLoading: isLogsLoading } = useAuditLogs();

  const isAdmin = currentRole === UserRole.ADMINISTRADOR;
  const adminKPIs = isAdmin ? (kpis as DashboardKPIsAdmin) : null;
  // ... rest of dashboard calculations remain identical but driven by colocated hooks
```

#### `app/reports/page.tsx`
```typescript
"use client";

import { useDataClient } from "@/lib/hooks/useDataClient";
import { useAuditLogs } from "@/lib/hooks/useAuditLogs";
import { useArticles } from "@/lib/hooks/useArticles";
import { UserRole } from "@/lib/types/domain";

export default function ReportesPage() {
  const { currentRole } = useDataClient();
  const { auditLogs, isLoading: isLogsLoading } = useAuditLogs();
  const { articles } = useArticles();
  const isAdmin = currentRole === UserRole.ADMINISTRADOR;
  // ...
```

---

## 6. Testing Strategy

### 6.1 `lib/hooks/useKPIs.test.ts`
1. **Unauthenticated Guard:**
   - Calling `useKPIs()` when `currentUser` is `null` returns `defaultKPIs`, `isLoading: false`, `error: null`.
   - Asserts `client.getKPIs` is **NEVER** called.
2. **Authenticated Fetch:**
   - When `currentUser` is set, calls `client.getKPIs(role)` with the active role and populates `kpis`.
3. **Role Override Support:**
   - Calling `useKPIs(UserRole.ADMINISTRADOR)` passes the override role directly to `client.getKPIs`.
4. **Error Handling:**
   - When `client.getKPIs` rejects with an `Error`, sets `error: Error.message` and resets `kpis` to `defaultKPIs`.
   - When rejecting with non-Error, captures fallback `"Error cargando KPIs del dashboard"`.
5. **Refetch Capability:**
   - Invoking `refetch()` executes a fresh call to `client.getKPIs`.
6. **RBAC Isolation / Anti-Leakage:**
   - When role switches from `ADMINISTRADOR` to `AUDITOR` while an admin fetch is in flight, late resolution of the admin request is discarded and does not overwrite auditor data.
7. **Unmount Protection:**
   - Unmounting the hook before the promise settles cancels state updates with no memory leaks or warnings.

### 6.2 `lib/hooks/useAuditLogs.test.ts`
1. **Unauthenticated Guard:**
   - Calling `useAuditLogs()` when `currentUser` is `null` returns `auditLogs: []`, `isLoading: false`, `error: null`.
   - Asserts `client.getAuditLog` is **NEVER** called.
2. **Authenticated Fetch:**
   - When authenticated, calls `client.getAuditLog()` once and populates `auditLogs`.
3. **Error Handling:**
   - Captures `Error` and non-Error rejections into `error` with fallback `"Error cargando registros de auditoría"`.
4. **Refetch Capability:**
   - Calling `refetch()` triggers a second query and updates state with fresh logs.
5. **Race Condition & Identity Safety:**
   - Changing user identity invalidates previous data and prevents cross-user log exposure.

### 6.3 `lib/context/ApiDataContext.test.tsx`
1. **Zero-Prefetch on Boot:**
   - Mounting `<ApiDataProvider>` with or without a stored user triggers **0** calls to `getKPIs` and **0** calls to `getAuditLog`.
2. **Zero-Prefetch on Login:**
   - Invoking `login()` authenticates the user and updates `currentUser` and `currentRole`, but triggers **0** calls to `getKPIs` or `getAuditLog`.
3. **Clean Contract:**
   - Verify `"kpis"` and `"auditLogs"` no longer exist on `useDataContext()`.

---

## 7. Boundaries

- **Always:**
  - Verify `currentUser` is present before executing any fetch in `useKPIs` and `useAuditLogs`.
  - Maintain the `cancelled` flag pattern to prevent React state-update-on-unmounted-component warnings and race conditions.
  - Return safe defaults (`defaultKPIs` and `[]`) when unauthenticated.
- **Ask first:**
  - If additional role-based aggregations should be performed on the client vs backend for `useKPIs`.
  - If pagination is required for `useAuditLogs` (e.g. `limit`, `offset`) before expanding the `DataClientPort.getAuditLog()` signature.
- **Never:**
  - Import `useKPIs` or `useAuditLogs` in root `layout.tsx`, `providers.tsx`, or `ApiDataContext.tsx`.
  - Return unmasked administrative KPI values (`pcio_com_siva`, `montoValorizado*`) to non-admin roles during role switches.
  - Re-introduce global cache synchronization loops in `registerAudit`.

---

## 8. Agent Delegation

| Agent | Responsibility | Task Scope |
|---|---|---|
| **`web-development-agent`** | Frontend Architecture (`frontend-web`) | 1. Implement `useKPIs.ts` and `useAuditLogs.ts` in `lib/hooks/`.<br>2. Remove `kpis` and `auditLogs` from `DataContext.tsx`, `ApiDataContext.tsx`, and `useDataClient.ts`.<br>3. Refactor `app/dashboard/page.tsx`, `app/reports/page.tsx`, and `app/debug/page.tsx` to consume the new hooks.<br>4. Align `MockDataContext.tsx` context exports. |
| **`test-engineer`** | Unit & Integration Verification | 1. Implement `useKPIs.test.ts` and `useAuditLogs.test.ts` with 100% boundary and RBAC coverage.<br>2. Update `ApiDataContext.test.tsx` to guarantee zero calls to `getKPIs` / `getAuditLog` during boot/login.<br>3. Verify all existing tests pass via `npm test`. |
| **`code-reviewer`** | Code Quality & Architecture Gate | 1. Verify strict decoupling between auth context and domain hooks.<br>2. Audit network waterfall profiles on `/login` to confirm zero unauthorized requests.<br>3. Verify RBAC sanitization. |

---

## 9. Success Criteria

1. Navigating to `/login` triggers **0** network calls to `/api/v1/articles`, `/api/v1/reports/*`, or any KPI endpoints.
2. Navigating to `/dashboard` while authenticated triggers `useKPIs` and `useAuditLogs` and renders operational tiles without layout shifts or missing data.
3. Navigating to `/reports` triggers `useAuditLogs` on-demand for history tabs.
4. Logging out resets states cleanly without triggering lingering KPI or log queries.
5. All tests in `frontend-web` pass with zero failures:
   ```bash
   npm test
   ```
   (including `useKPIs.test.ts`, `useAuditLogs.test.ts`, and updated `ApiDataContext.test.tsx`).
