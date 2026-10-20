// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useKPIs, defaultKPIs } from "./useKPIs";
import { useDataClient } from "./useDataClient";
import { UserRole, DashboardKPIsBase, DashboardKPIsAdmin } from "../types/domain";

vi.mock("./useDataClient", () => ({ useDataClient: vi.fn() }));

const mockedUseDataClient = vi.mocked(useDataClient);

function setup(
  currentUser: unknown,
  getKPIs: ReturnType<typeof vi.fn>,
  currentRole: UserRole | null = UserRole.AUDITOR
) {
  mockedUseDataClient.mockReturnValue({
    client: { getKPIs },
    currentUser,
    currentRole,
  } as unknown as ReturnType<typeof useDataClient>);
}

describe("useKPIs", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("does not call getKPIs when unauthenticated", async () => {
    const getKPIs = vi.fn();
    setup(null, getKPIs);

    const { result } = renderHook(() => useKPIs());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(getKPIs).not.toHaveBeenCalled();
    expect(result.current.kpis).toEqual(defaultKPIs);
    expect(result.current.error).toBeNull();
  });

  it("fetches and exposes KPIs when authenticated", async () => {
    const mockKPIs: DashboardKPIsBase = {
      totalArticulos: 20,
      auditados: 10,
      pendientes: 10,
      porcentajeAvance: 50,
      discrepanciasAlta: 1,
      discrepanciasBaja: 2,
      sinAccion: 7,
    };
    const getKPIs = vi.fn().mockResolvedValue(mockKPIs);
    setup({ id: "1" }, getKPIs, UserRole.SUPERVISOR);

    const { result } = renderHook(() => useKPIs());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(getKPIs).toHaveBeenCalledTimes(1);
    expect(getKPIs).toHaveBeenCalledWith(UserRole.SUPERVISOR);
    expect(result.current.kpis).toEqual(mockKPIs);
    expect(result.current.error).toBeNull();
  });

  it("supports role override parameter", async () => {
    const mockAdminKPIs: DashboardKPIsAdmin = {
      totalArticulos: 100,
      auditados: 80,
      pendientes: 20,
      porcentajeAvance: 80,
      discrepanciasAlta: 5,
      discrepanciasBaja: 5,
      sinAccion: 70,
      montoValorizadoTotal: 5000,
      montoValorizadoAlta: 3000,
      montoValorizadoBaja: 2000,
    };
    const getKPIs = vi.fn().mockResolvedValue(mockAdminKPIs);
    setup({ id: "1" }, getKPIs, UserRole.AUDITOR);

    const { result } = renderHook(() => useKPIs(UserRole.ADMINISTRADOR));

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(getKPIs).toHaveBeenCalledTimes(1);
    expect(getKPIs).toHaveBeenCalledWith(UserRole.ADMINISTRADOR);
    expect(result.current.kpis).toEqual(mockAdminKPIs);
  });

  it("captures Error instances into error state", async () => {
    const getKPIs = vi.fn().mockRejectedValue(new Error("KPI service down"));
    setup({ id: "1" }, getKPIs);

    const { result } = renderHook(() => useKPIs());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.error).toBe("KPI service down");
    expect(result.current.kpis).toEqual(defaultKPIs);
  });

  it("captures non-Error rejections with fallback message", async () => {
    const getKPIs = vi.fn().mockRejectedValue("unknown network error");
    setup({ id: "1" }, getKPIs);

    const { result } = renderHook(() => useKPIs());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.error).toBe("Error cargando KPIs del dashboard");
    expect(result.current.kpis).toEqual(defaultKPIs);
  });

  it("triggers refetch when calling refetch()", async () => {
    const kpisBatch1: DashboardKPIsBase = { ...defaultKPIs, totalArticulos: 5 };
    const kpisBatch2: DashboardKPIsBase = { ...defaultKPIs, totalArticulos: 10 };
    const getKPIs = vi
      .fn()
      .mockResolvedValueOnce(kpisBatch1)
      .mockResolvedValueOnce(kpisBatch2);

    setup({ id: "1" }, getKPIs);

    const { result } = renderHook(() => useKPIs());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.kpis).toEqual(kpisBatch1);
    expect(getKPIs).toHaveBeenCalledTimes(1);

    await act(async () => {
      await result.current.refetch();
    });

    await waitFor(() => expect(result.current.kpis).toEqual(kpisBatch2));
    expect(getKPIs).toHaveBeenCalledTimes(2);
  });

  it("does not expose stale or cross-role data when role switches during in-flight fetch", async () => {
    let resolveFirst: ((val: unknown) => void) | undefined;
    const slowAdminPromise = new Promise((res) => {
      resolveFirst = res;
    });

    const auditorKPIs: DashboardKPIsBase = { ...defaultKPIs, totalArticulos: 50 };
    const adminKPIs: DashboardKPIsAdmin = {
      ...defaultKPIs,
      totalArticulos: 50,
      montoValorizadoTotal: 999999,
      montoValorizadoAlta: 500000,
      montoValorizadoBaja: 499999,
    };

    const getKPIs = vi
      .fn()
      .mockImplementationOnce(() => slowAdminPromise)
      .mockResolvedValueOnce(auditorKPIs);

    const userAdmin = { id: "USR-ADMIN", role: UserRole.ADMINISTRADOR };
    const userAuditor = { id: "USR-AUDITOR", role: UserRole.AUDITOR };

    setup(userAdmin, getKPIs, UserRole.ADMINISTRADOR);

    const { result, rerender } = renderHook(() => useKPIs());

    expect(result.current.isLoading).toBe(true);
    expect(result.current.kpis).toEqual(defaultKPIs);

    // Role switches to Auditor before Admin promise finishes
    setup(userAuditor, getKPIs, UserRole.AUDITOR);
    rerender();

    await waitFor(() => expect(result.current.kpis).toEqual(auditorKPIs));

    // Resolving late Admin promise should not overwrite current Auditor view
    resolveFirst?.(adminKPIs);

    expect(result.current.kpis).toEqual(auditorKPIs);
  });

  it("ignores settled data if component unmounts during fetch", async () => {
    let resolvePromise: ((val: unknown) => void) | undefined;
    const pendingPromise = new Promise((res) => {
      resolvePromise = res;
    });

    const getKPIs = vi.fn().mockImplementation(() => pendingPromise);
    setup({ id: "1" }, getKPIs);

    const { result, unmount } = renderHook(() => useKPIs());
    expect(result.current.isLoading).toBe(true);

    unmount();
    resolvePromise?.(defaultKPIs);

    expect(getKPIs).toHaveBeenCalledTimes(1);
  });
});
