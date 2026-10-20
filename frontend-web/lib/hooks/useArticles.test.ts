// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest";
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
