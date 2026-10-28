// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useArticles } from "./useArticles";
import { useDataClient } from "./useDataClient";
import { UserRole } from "../types/domain";

vi.mock("./useDataClient", () => ({ useDataClient: vi.fn() }));

const mockedUseDataClient = vi.mocked(useDataClient);

function setup(
  currentUser: unknown,
  getArticulos: ReturnType<typeof vi.fn>,
  currentRole: UserRole | null = UserRole.AUDITOR
) {
  mockedUseDataClient.mockReturnValue({
    client: { getArticulos },
    currentUser,
    currentRole,
  } as unknown as ReturnType<typeof useDataClient>);
}

describe("useArticles", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("does not call getArticulos when unauthenticated", async () => {
    const getArticulos = vi.fn();
    setup(null, getArticulos);

    const { result } = renderHook(() => useArticles());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(getArticulos).not.toHaveBeenCalled();
    expect(result.current.articles).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it("fetches and exposes articles when authenticated", async () => {
    const items = [{ id_articulo: "ART-1" }];
    const getArticulos = vi.fn().mockResolvedValue(items);
    setup({ id: "1" }, getArticulos, UserRole.ADMINISTRADOR);

    const { result } = renderHook(() => useArticles());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(getArticulos).toHaveBeenCalledTimes(1);
    expect(getArticulos).toHaveBeenCalledWith(UserRole.ADMINISTRADOR);
    expect(result.current.articles).toEqual(items);
    expect(result.current.error).toBeNull();
  });

  it("captures Error instances into error state", async () => {
    const getArticulos = vi.fn().mockRejectedValue(new Error("API failure"));
    setup({ id: "1" }, getArticulos);

    const { result } = renderHook(() => useArticles());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.error).toBe("API failure");
    expect(result.current.articles).toEqual([]);
  });

  it("captures non-Error rejections with fallback message", async () => {
    const getArticulos = vi.fn().mockRejectedValue("unknown network error");
    setup({ id: "1" }, getArticulos);

    const { result } = renderHook(() => useArticles());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.error).toBe("Error cargando artículos del catálogo");
    expect(result.current.articles).toEqual([]);
  });

  it("triggers refetch when calling refetch()", async () => {
    const itemsBatch1 = [{ id_articulo: "ART-1" }];
    const itemsBatch2 = [{ id_articulo: "ART-1" }, { id_articulo: "ART-2" }];
    const getArticulos = vi
      .fn()
      .mockResolvedValueOnce(itemsBatch1)
      .mockResolvedValueOnce(itemsBatch2);

    setup({ id: "1" }, getArticulos);

    const { result } = renderHook(() => useArticles());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.articles).toEqual(itemsBatch1);
    expect(getArticulos).toHaveBeenCalledTimes(1);

    await act(async () => {
      await result.current.refetch();
    });

    await waitFor(() => expect(result.current.articles).toEqual(itemsBatch2));
    expect(getArticulos).toHaveBeenCalledTimes(2);
  });

  it("does not expose stale or cross-role data when identity switches", async () => {
    let resolveFirst: ((val: unknown) => void) | undefined;
    const slowAdminPromise = new Promise((res) => {
      resolveFirst = res;
    });

    const getArticulos = vi
      .fn()
      .mockImplementationOnce(() => slowAdminPromise)
      .mockResolvedValueOnce([{ id_articulo: "ART-AUDITOR" }]);

    const userAdmin = { id: "USR-ADMIN", role: UserRole.ADMINISTRADOR };
    const userAuditor = { id: "USR-AUDITOR", role: UserRole.AUDITOR };

    setup(userAdmin, getArticulos, UserRole.ADMINISTRADOR);

    const { result, rerender } = renderHook(() => useArticles());

    expect(result.current.isLoading).toBe(true);
    expect(result.current.articles).toEqual([]);

    // Role switches to Auditor before Admin promise finishes
    setup(userAuditor, getArticulos, UserRole.AUDITOR);
    rerender();

    await waitFor(() => expect(result.current.articles).toEqual([{ id_articulo: "ART-AUDITOR" }]));

    // Resolving late Admin promise should not overwrite current Auditor view
    resolveFirst?.([{ id_articulo: "ART-ADMIN-SECRET", pcio_com_siva: 999 }]);

    expect(result.current.articles).toEqual([{ id_articulo: "ART-AUDITOR" }]);
  });

  it("ignores settled data if component unmounts during fetch", async () => {
    let resolvePromise: ((val: unknown) => void) | undefined;
    const pendingPromise = new Promise((res) => {
      resolvePromise = res;
    });

    const getArticulos = vi.fn().mockImplementation(() => pendingPromise);
    setup({ id: "1" }, getArticulos);

    const { result, unmount } = renderHook(() => useArticles());
    expect(result.current.isLoading).toBe(true);

    unmount();
    resolvePromise?.([{ id_articulo: "ART-1" }]);

    // Component is unmounted, verify no uncaught errors or leaks
    expect(getArticulos).toHaveBeenCalledTimes(1);
  });
});

function setupClient(
  client: Record<string, unknown>,
  currentUser: unknown = { id: "1" },
  currentRole: UserRole | null = UserRole.AUDITOR
) {
  mockedUseDataClient.mockReturnValue({
    client,
    currentUser,
    currentRole,
  } as unknown as ReturnType<typeof useDataClient>);
}

function pageResult(page: number, items: unknown[] = [{ id_articulo: `ART-P${page}` }]) {
  return { items, total: 500, page, limit: 10, pages: 50 };
}

function makeClient(overrides: Record<string, unknown> = {}) {
  return {
    getArticulos: vi.fn().mockResolvedValue([]),
    getPaginatedArticles: vi
      .fn()
      .mockImplementation((q: { page: number }) => Promise.resolve(pageResult(q.page))),
    getFamilies: vi.fn().mockResolvedValue([
      { id_familia: "01", des_familia: "Medicamentos" },
      { id_familia: "02", des_familia: "Perfumería" },
    ]),
    ...overrides,
  };
}

describe("useArticles paginated mode", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("fetches the first page with default limit and the current role", async () => {
    const client = makeClient();
    setupClient(client, { id: "1" }, UserRole.ADMINISTRADOR);

    const { result } = renderHook(() => useArticles({ paginated: true }));

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(client.getPaginatedArticles).toHaveBeenCalledTimes(1);
    expect(client.getPaginatedArticles).toHaveBeenCalledWith(
      { page: 1, limit: 10 },
      UserRole.ADMINISTRADOR
    );
    expect(client.getArticulos).not.toHaveBeenCalled();
    expect(result.current.articles).toEqual([{ id_articulo: "ART-P1" }]);
    expect(result.current.total).toBe(500);
    expect(result.current.pages).toBe(50);
    expect(result.current.page).toBe(1);
    expect(result.current.limit).toBe(10);
  });

  it("refetches with the new page when setPage is called", async () => {
    const client = makeClient();
    setupClient(client);

    const { result } = renderHook(() => useArticles({ paginated: true }));
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => result.current.setPage(11));

    await waitFor(() => expect(result.current.articles).toEqual([{ id_articulo: "ART-P11" }]));
    expect(client.getPaginatedArticles).toHaveBeenLastCalledWith(
      { page: 11, limit: 10 },
      UserRole.AUDITOR
    );
    expect(result.current.page).toBe(11);
  });

  it("debounces search by 250ms, fetches once with the last term and resets page to 1", async () => {
    vi.useFakeTimers();
    const client = makeClient();
    setupClient(client);

    const { result } = renderHook(() => useArticles({ paginated: true }));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    act(() => result.current.setPage(3));
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    const callsBeforeTyping = client.getPaginatedArticles.mock.calls.length;

    act(() => result.current.setSearch("A"));
    act(() => result.current.setSearch("Am"));
    act(() => result.current.setSearch("Amox"));
    expect(result.current.search).toBe("Amox");

    await act(async () => {
      await vi.advanceTimersByTimeAsync(249);
    });
    expect(client.getPaginatedArticles).toHaveBeenCalledTimes(callsBeforeTyping);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1);
    });
    expect(client.getPaginatedArticles).toHaveBeenCalledTimes(callsBeforeTyping + 1);
    expect(client.getPaginatedArticles).toHaveBeenLastCalledWith(
      { page: 1, limit: 10, search: "Amox" },
      UserRole.AUDITOR
    );
    expect(result.current.page).toBe(1);
  });

  it("resets page to 1 when the family or status filter changes", async () => {
    const client = makeClient();
    setupClient(client);

    const { result } = renderHook(() => useArticles({ paginated: true }));
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => result.current.setPage(3));
    await waitFor(() => expect(result.current.page).toBe(3));

    act(() => result.current.setFamily("02"));
    await waitFor(() =>
      expect(client.getPaginatedArticles).toHaveBeenLastCalledWith(
        { page: 1, limit: 10, id_familia: "02" },
        UserRole.AUDITOR
      )
    );
    expect(result.current.page).toBe(1);
    expect(result.current.idFamilia).toBe("02");

    act(() => result.current.setPage(4));
    act(() => result.current.setStatus(true));
    await waitFor(() =>
      expect(client.getPaginatedArticles).toHaveBeenLastCalledWith(
        { page: 1, limit: 10, id_familia: "02", fue_auditado: true },
        UserRole.AUDITOR
      )
    );
    expect(result.current.page).toBe(1);
  });

  it("discards out-of-order responses from superseded queries", async () => {
    let resolvePage2: ((val: unknown) => void) | undefined;
    const client = makeClient({
      getPaginatedArticles: vi.fn().mockImplementation((q: { page: number }) => {
        if (q.page === 2) {
          return new Promise((res) => {
            resolvePage2 = res;
          });
        }
        return Promise.resolve(pageResult(q.page));
      }),
    });
    setupClient(client);

    const { result } = renderHook(() => useArticles({ paginated: true }));
    await waitFor(() => expect(result.current.isLoading).toBe(false));

    act(() => result.current.setPage(2));
    act(() => result.current.setPage(3));
    await waitFor(() => expect(result.current.articles).toEqual([{ id_articulo: "ART-P3" }]));

    await act(async () => {
      resolvePage2?.(pageResult(2));
    });

    expect(result.current.articles).toEqual([{ id_articulo: "ART-P3" }]);
    expect(result.current.isLoading).toBe(false);
  });

  it("fetches families once and exposes them", async () => {
    const client = makeClient();
    setupClient(client);

    const { result } = renderHook(() => useArticles({ paginated: true }));

    await waitFor(() => expect(result.current.families).toHaveLength(2));
    act(() => result.current.setPage(2));
    await waitFor(() => expect(result.current.page).toBe(2));
    expect(client.getFamilies).toHaveBeenCalledTimes(1);
    expect(result.current.families[1]).toEqual({ id_familia: "02", des_familia: "Perfumería" });
  });

  it("degrades to empty families without affecting articles when getFamilies fails", async () => {
    const client = makeClient({ getFamilies: vi.fn().mockRejectedValue(new Error("boom")) });
    setupClient(client);

    const { result } = renderHook(() => useArticles({ paginated: true }));

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    await waitFor(() => expect(client.getFamilies).toHaveBeenCalledTimes(1));
    expect(result.current.families).toEqual([]);
    expect(result.current.error).toBeNull();
    expect(result.current.articles).toEqual([{ id_articulo: "ART-P1" }]);
  });

  it("does not fetch pages or families when unauthenticated", async () => {
    const client = makeClient();
    setupClient(client, null);

    const { result } = renderHook(() => useArticles({ paginated: true }));

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(client.getPaginatedArticles).not.toHaveBeenCalled();
    expect(client.getFamilies).not.toHaveBeenCalled();
  });

  it("keeps the legacy full-list path when called without options", async () => {
    const client = makeClient({
      getArticulos: vi.fn().mockResolvedValue([{ id_articulo: "ART-1" }, { id_articulo: "ART-2" }]),
    });
    setupClient(client);

    const { result } = renderHook(() => useArticles());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(client.getArticulos).toHaveBeenCalledTimes(1);
    expect(client.getPaginatedArticles).not.toHaveBeenCalled();
    expect(client.getFamilies).not.toHaveBeenCalled();
    expect(result.current.total).toBe(2);
    expect(result.current.families).toEqual([]);
  });
});
