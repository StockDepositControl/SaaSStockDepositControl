### ASSUMPTIONS I'M MAKING
1. The dedicated hook will be named `useArticles` (or `useCatalogArticles`) located in `frontend-web/lib/hooks/useArticles.ts` (or under a dedicated `modules/catalog/` directory).
2. The global `ApiDataContext` will be relieved of managing the `articles` array and will no longer call `client.getArticulos()` on boot.
3. Consuming pages (such as `frontend-web/app/catalog/page.tsx`) will consume `useArticles()` directly, loading data only when that view mounts.
4. If `DashboardPage` requires article alerts, it can consume `useArticles()` independently without forcing the `/login` page to prefetch catalog data.

---

# Spec: Dedicated Catalog Hook (`useArticles`) & Zero-Prefetch Auth Lifecycle

## 1. Objective
Decouple the catalog data lifecycle from global application boot. Replace the monolithic `ApiDataContext` article state with a dedicated `useArticles` hook scoped to the **Catálogo** module. Ensure that navigating to `/login` triggers **zero** calls to `/api/v1/articles` or any other protected business endpoints.

---

## 2. Tech Stack
- **Framework:** Next.js 16.2.10 (App Router) + React 19.2.4
- **Language:** TypeScript 5.x
- **Testing:** Vitest 2.1.8 + React Testing Library + JSDOM

---

## 3. Commands
- **Dev:** `npm run dev` (inside `frontend-web/`)
- **Build:** `npm run build`
- **Lint:** `npm run lint`
- **Test:** `npm test`

---

## 4. Project Structure & Affected Surfaces
```
frontend-web/
├── lib/
│   ├── hooks/
│   │   ├── useArticles.ts           → [NEW] Dedicated hook for fetching/caching catalog articles
│   │   ├── useArticles.test.ts      → [NEW] Vitest tests for hook lifecycle, auth guarding & errors
│   │   └── useDataClient.ts         → [MODIFY] Keep auth/session methods, remove global articles dependency
│   ├── context/
│   │   ├── ApiDataContext.tsx       → [MODIFY] Remove articles state and remove client.getArticulos() from root fetch
│   │   └── ApiDataContext.test.tsx  → [MODIFY] Verify root provider executes 0 network calls when unauthenticated or on /login
│   └── adapters/
│       └── ApiDataClient.ts         → [MODIFY] Validate token expiration in getStoredUser() before returning a session
├── app/
│   ├── catalog/
│   │   └── page.tsx                 → [MODIFY] Consume useArticles() directly instead of useDataClient()
│   └── dashboard/
│       └── page.tsx                 → [ALIGN] Consume useArticles() locally if stock shortage calculations require items
```

---

## 5. Architectural Pattern & Code Style

CONCEPTS > CODE. Moving state closer to where it is consumed adheres to the **Principle of Least Privilege & Colocated State**.

### Dedicated Hook: `useArticles.ts`
```typescript
"use client";

import { useState, useEffect, useCallback } from "react";
import { useDataClient } from "@/lib/hooks/useDataClient";
import { ArticuloPublicView, ArticuloAdminView, UserRole } from "@/lib/types/domain";

export interface UseArticlesReturn {
  articles: (ArticuloPublicView | ArticuloAdminView)[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useArticles(): UseArticlesReturn {
  const { client, currentRole, currentUser } = useDataClient();
  const [articles, setArticles] = useState<(ArticuloPublicView | ArticuloAdminView)[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchArticles = useCallback(async () => {
    // 🛑 Boundary Guard: Never fetch if not authenticated
    if (!currentUser) {
      setArticles([]);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const data = await client.getArticulos(currentRole || UserRole.AUDITOR);
      setArticles(data);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Error cargando artículos del catálogo";
      setError(msg);
      setArticles([]);
    } finally {
      setIsLoading(false);
    }
  }, [client, currentRole, currentUser]);

  useEffect(() => {
    fetchArticles();
  }, [fetchArticles]);

  return { articles, isLoading, error, refetch: fetchArticles };
}
```

### Cleaned `CatalogPage` (`app/catalog/page.tsx`)
```typescript
"use client";

import { useDataClient } from "@/lib/hooks/useDataClient";
import { useArticles } from "@/lib/hooks/useArticles";
import { UserRole } from "@/lib/types/domain";
import { DemoShell } from "@/components/layout/DemoShell";
import { DataTable } from "@/components/ui/DataTable";

export default function CatalogPage() {
  const { currentRole } = useDataClient();
  const { articles, isLoading, error } = useArticles();

  return (
    <DemoShell>
      {/* Renders DataTable with articles fetched on-demand */}
      <DataTable
        articles={articles}
        currentRole={currentRole || UserRole.AUDITOR}
        isLoading={isLoading}
      />
    </DemoShell>
  );
}
```

---

## 6. Testing Strategy
- **`useArticles.test.ts`:**
  1. Does **NOT** call `client.getArticulos()` if `currentUser` is `null`.
  2. Calls `client.getArticulos()` once mounted with an authenticated user and populates `articles`.
  3. Properly exposes `isLoading` and captures `ApiError` into `error` state.
- **`ApiDataContext.test.tsx`:**
  1. Mounting `<ApiDataProvider>` with empty storage or on `/login` invokes **0** calls to `getArticulos`.
  2. Verify that `articles` is no longer eagerly loaded in root state.

---

## 7. Boundaries
- **Always:** Verify `currentUser` is present before executing any fetch inside `useArticles`.
- **Ask first:** If we should also decouple `kpis` and `auditLogs` into their own dedicated domain hooks (`useKPIs`, `useAuditLogs`) now or in a separate task.
- **Never:** Import `useArticles` into the root `layout.tsx` or `providers.tsx`.

---

## 8. Agent Delegation

| Agent | Module / Responsibility | Task Scope |
|---|---|---|
| **`web-development-agent`** | Frontend Architecture (`frontend-web`) | 1. Implement `useArticles.ts` in `lib/hooks/`.<br>2. Remove `articles` state and `client.getArticulos()` from `ApiDataContext.tsx`.<br>3. Refactor `app/catalog/page.tsx` (and `app/dashboard/page.tsx`) to consume `useArticles()`.<br>4. Guard `ApiDataClient.getStoredUser()` against unauthenticated calls. |
| **`test-engineer`** | Unit & Integration Verification | 1. Write `useArticles.test.ts` covering unauthenticated vs authenticated states.<br>2. Update `ApiDataContext.test.tsx` and run `npm test` across `frontend-web`. |
| **`code-reviewer`** | Code Quality & Architecture Gate | Ensure complete decoupling between root auth context and domain catalog hooks, and verify zero 401 console errors on `/login`. |

---

## 9. Success Criteria
1. Loading `/login` causes **zero** network requests to `/api/v1/articles` in both frontend and backend logs.
2. Navigating to `/catalog` while authenticated triggers the fetch via `useArticles` and renders the article table.
3. Logging out clears the state and redirects to `/login` without triggering trailing article requests.
4. `npm test` passes cleanly in `frontend-web`.
