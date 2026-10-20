// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useAuditLogs } from "./useAuditLogs";
import { useDataClient } from "./useDataClient";
import { AuditResult, TipoAccion } from "../types/domain";

vi.mock("./useDataClient", () => ({ useDataClient: vi.fn() }));

const mockedUseDataClient = vi.mocked(useDataClient);

function setup(currentUser: unknown, getAuditLog: ReturnType<typeof vi.fn>) {
  mockedUseDataClient.mockReturnValue({
    client: { getAuditLog },
    currentUser,
  } as unknown as ReturnType<typeof useDataClient>);
}

const mockAuditLogs: AuditResult[] = [
  {
    client_uuid: "AUD-1",
    id_articulo: "ART-1",
    des_articulo: "Ibuprofeno 400mg",
    stock_fisico_contado: 10,
    stock_real: 12,
    delta_stock: -2,
    tipo_accion: TipoAccion.BAJA,
    cantidad_afectada: 2,
    audit_quantity: 10,
    monto_valorizado: 1200,
    applied_vat_rate: 21,
    scan_timestamp: "2026-10-20T10:00:00Z",
  },
];

describe("useAuditLogs", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("does not call getAuditLog when unauthenticated", async () => {
    const getAuditLog = vi.fn();
    setup(null, getAuditLog);

    const { result } = renderHook(() => useAuditLogs());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(getAuditLog).not.toHaveBeenCalled();
    expect(result.current.auditLogs).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it("fetches and exposes audit logs when authenticated", async () => {
    const getAuditLog = vi.fn().mockResolvedValue(mockAuditLogs);
    setup({ id: "USR-1" }, getAuditLog);

    const { result } = renderHook(() => useAuditLogs());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(getAuditLog).toHaveBeenCalledTimes(1);
    expect(result.current.auditLogs).toEqual(mockAuditLogs);
    expect(result.current.error).toBeNull();
  });

  it("captures Error instances into error state", async () => {
    const getAuditLog = vi.fn().mockRejectedValue(new Error("Database unavailable"));
    setup({ id: "USR-1" }, getAuditLog);

    const { result } = renderHook(() => useAuditLogs());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.error).toBe("Database unavailable");
    expect(result.current.auditLogs).toEqual([]);
  });

  it("captures non-Error rejections with fallback message", async () => {
    const getAuditLog = vi.fn().mockRejectedValue("network drop");
    setup({ id: "USR-1" }, getAuditLog);

    const { result } = renderHook(() => useAuditLogs());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.error).toBe("Error cargando registros de auditoría");
    expect(result.current.auditLogs).toEqual([]);
  });

  it("triggers refetch when calling refetch()", async () => {
    const batch1 = [mockAuditLogs[0]];
    const batch2 = [
      ...mockAuditLogs,
      {
        ...mockAuditLogs[0],
        client_uuid: "AUD-2",
        tipo_accion: TipoAccion.SIN_ACCION,
      },
    ];
    const getAuditLog = vi
      .fn()
      .mockResolvedValueOnce(batch1)
      .mockResolvedValueOnce(batch2);

    setup({ id: "USR-1" }, getAuditLog);

    const { result } = renderHook(() => useAuditLogs());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.auditLogs).toEqual(batch1);
    expect(getAuditLog).toHaveBeenCalledTimes(1);

    await act(async () => {
      await result.current.refetch();
    });

    await waitFor(() => expect(result.current.auditLogs).toEqual(batch2));
    expect(getAuditLog).toHaveBeenCalledTimes(2);
  });

  it("does not expose stale logs across user switches during in-flight fetch", async () => {
    let resolveFirst: ((val: unknown) => void) | undefined;
    const slowUserPromise = new Promise((res) => {
      resolveFirst = res;
    });

    const user1Logs: AuditResult[] = [mockAuditLogs[0]];
    const user2Logs: AuditResult[] = [
      {
        ...mockAuditLogs[0],
        client_uuid: "AUD-USER2",
      },
    ];

    const getAuditLog = vi
      .fn()
      .mockImplementationOnce(() => slowUserPromise)
      .mockResolvedValueOnce(user2Logs);

    const user1 = { id: "USR-1" };
    const user2 = { id: "USR-2" };

    setup(user1, getAuditLog);

    const { result, rerender } = renderHook(() => useAuditLogs());

    expect(result.current.isLoading).toBe(true);
    expect(result.current.auditLogs).toEqual([]);

    // Identity switches to User 2 before User 1 promise finishes
    setup(user2, getAuditLog);
    rerender();

    await waitFor(() => expect(result.current.auditLogs).toEqual(user2Logs));

    // Late resolution from User 1 must not overwrite User 2 data
    resolveFirst?.(user1Logs);

    expect(result.current.auditLogs).toEqual(user2Logs);
  });

  it("ignores settled data if component unmounts during fetch", async () => {
    let resolvePromise: ((val: unknown) => void) | undefined;
    const pendingPromise = new Promise((res) => {
      resolvePromise = res;
    });

    const getAuditLog = vi.fn().mockImplementation(() => pendingPromise);
    setup({ id: "USR-1" }, getAuditLog);

    const { result, unmount } = renderHook(() => useAuditLogs());
    expect(result.current.isLoading).toBe(true);

    unmount();
    resolvePromise?.(mockAuditLogs);

    expect(getAuditLog).toHaveBeenCalledTimes(1);
  });
});
