### ASSUMPTIONS I'M MAKING:
1. The backend API `/api/v1/stock/kpis` contract remains unchanged and correctly returns `monto_valorizado_baja`, `monto_valorizado_alta`, and `monto_valorizado_total` for authenticated Administrators once the request resolves.
2. The root cause is strictly a client-side race/lifecycle defect: `useKPIs()` initializes with `defaultKPIs` (`DashboardKPIsBase`), and the UI forces an unsafe type assertion (`as DashboardKPIsAdmin`) during the asynchronous fetch window.
3. The fix should eliminate type casting (`as`) in favor of a reusable runtime type guard (`isAdminKPIs`) and defensive property resolution (`?.` with fallback values).
4. Sibling views (`app/debug/page.tsx`) suffering from the exact same anti-pattern must be hardened in tandem.

---

# Spec: Admin Dashboard KPI Resilience & Type Guard Hardening

## 1. Objective
Eliminate the client-side `TypeError: Cannot read properties of undefined (reading 'toLocaleString')` occurring upon Administrator login. 

When an Administrator logs into the application, the role is recognized immediately (`isAdmin = true`), but the domain KPI metrics are fetched asynchronously via `useKPIs()`. During this in-flight window, `kpis` defaults to `defaultKPIs` (`DashboardKPIsBase`). The current implementation forcibly casts `kpis as DashboardKPIsAdmin`, tricking TypeScript into assuming financial fields exist. In the JSX render, the truthy check passes because `defaultKPIs` is an object, attempting `adminKPIs.montoValorizadoBaja.toLocaleString(...)` on an `undefined` property and crashing the UI.

This specification details the transition from unsafe compile-time assertions to runtime type guards, defensive rendering fallbacks, and comprehensive integration testing for the Admin loading lifecycle.

---

## 2. Tech Stack
- **Framework:** Next.js 16.2 (App Router), React 19
- **Language:** TypeScript 5.x (Strict mode)
- **Testing:** Vitest 2.1, React Testing Library, jsdom
- **Icons & Styling:** Tailwind CSS, Lucide React

---

## 3. Commands
- **Run Frontend Tests:** `npx vitest run app/dashboard/page.test.tsx` (inside `frontend-web/`)
- **Full Test Suite:** `npm test` (inside `frontend-web/`)
- **Typecheck & Build:** `npm run build` (inside `frontend-web/`)
- **Dev Server:** `npm run dev` (inside `frontend-web/`)

---

## 4. Project Structure & Affected Surfaces

```
specs/
└── SPEC-admin-dashboard-resilience-fix.md   → [NEW] This specification document

frontend-web/
├── lib/
│   └── types/
│       └── domain.ts                       → [MODIFY] Export runtime type guard `isAdminKPIs()`
├── app/
│   ├── dashboard/
│   │   ├── page.tsx                        → [MODIFY] Replace `as` cast with `isAdminKPIs`, add defensive optional chaining
│   │   └── page.test.tsx                   → [MODIFY] Add Admin loading/empty state test case
│   └── debug/
│       └── page.tsx                        → [MODIFY] Remove unsafe `as DashboardKPIsAdmin` casting; harden `.toLocaleString()`
```

---

## 5. Code Style & Architectural Conventions

### Type Guard Pattern (Domain Layer)
In `frontend-web/lib/types/domain.ts`:
```typescript
/**
 * Runtime type guard to safely discriminate Admin KPIs with valorized financial fields.
 */
export function isAdminKPIs(
  kpis: DashboardKPIsBase | DashboardKPIsAdmin | null | undefined
): kpis is DashboardKPIsAdmin {
  return (
    kpis != null &&
    "montoValorizadoBaja" in kpis &&
    typeof kpis.montoValorizadoBaja === "number"
  );
}
```

### Defensive Consumption Pattern (UI Layer)
In `frontend-web/app/dashboard/page.tsx`:
```tsx
const isAdmin = currentRole === UserRole.ADMINISTRADOR;
const adminKPIs = isAdmin && isAdminKPIs(kpis) ? kpis : null;

// Inside JSX:
<div className="text-4xl font-bold text-red-600 mb-1">
  $ {adminKPIs?.montoValorizadoBaja != null
    ? adminKPIs.montoValorizadoBaja.toLocaleString("en-US", { minimumFractionDigits: 2 })
    : "---"}
</div>
```

---

## 6. Testing Strategy

1. **Unit / Integration Test (Vitest + React Testing Library):**
   - File: `frontend-web/app/dashboard/page.test.tsx`
   - Test Case 1: `renders administrator view in loading state without throwing`
     - Mock `currentRole: UserRole.ADMINISTRADOR`
     - Mock `useKPIs` returning `isLoading: true, kpis: defaultKPIs`
     - Assert component mounts cleanly.
     - Assert placeholder `"$ ---"` is displayed while metrics are unresolved.
   - Test Case 2: `renders administrator view when metrics resolve`
     - Mock `useKPIs` returning `isLoading: false, kpis: adminKPIsFixture`
     - Assert formatted financial amount `"$ 8,900.00"` displays.

---

## 7. Boundaries
- **Always:** Use runtime type guards instead of `as` casts when narrowing union types derived from asynchronous state.
- **Always:** Verify UI stability across all user roles (`ADMINISTRADOR`, `SUPERVISOR`, `AUDITOR`) in both loading and settled states.
- **Ask First:** Modifying the backend KPI payload contract or changing public domain interfaces.
- **Never:** Use unconditional property invocation (`obj.prop.method()`) on asynchronously populated objects.
- **Never:** Add "Co-Authored-By" or AI attribution to git commit messages.

---

## 8. Agent Roster & RACI Matrix

| Agent | Role | RACI | Specific Responsibilities |
| :--- | :--- | :---: | :--- |
| **`web-development-agent`** | Senior Frontend Engineer | **R / A** | • Implement `isAdminKPIs` type guard in `lib/types/domain.ts`.<br>• Eliminate `as DashboardKPIsAdmin` in `app/dashboard/page.tsx` and `app/debug/page.tsx`.<br>• Ensure robust defensive formatting and fallback placeholders in JSX. |
| **`test-engineer`** | QA & Test Engineer | **R** | • Author the failing test reproducing the Admin loading crash in `app/dashboard/page.test.tsx`.<br>• Verify regression tests across all roles (`AUDITOR`, `SUPERVISOR`, `ADMINISTRADOR`). |
| **`code-reviewer`** | Senior Architect / Reviewer | **C / I** | • Audit changes against Clean Architecture and type-safety standards.<br>• Verify that zero unsafe type casts (`as`) remain on async data boundaries. |
| **`core-backend-agent`** | Senior Backend Engineer | **I** | • Consulted only to guarantee `/api/v1/stock/kpis` schema integrity (no code changes required). |

---

## 9. Success Criteria
1. Logging in as Administrator and landing on `/dashboard` does not trigger any runtime exceptions.
2. While `useKPIs` is fetching (`isLoading: true`), the shortage metric displays `"$ ---"` safely without layout shift.
3. Once `useKPIs` resolves, the shortage metric correctly formats the currency (e.g., `"$ 8,900.00"`).
4. `app/dashboard/page.test.tsx` passes with 100% coverage on the new Admin loading test case.
5. `npm run build` in `frontend-web` completes with zero TypeScript or ESLint errors.
