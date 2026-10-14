import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { HttpClient, ApiError } from "./httpClient";

describe("HttpClient", () => {
  let client: HttpClient;
  const mockBaseUrl = "http://localhost:8000";

  beforeEach(() => {
    client = new HttpClient(mockBaseUrl);
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("should build URL correctly and append query params", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ success: true }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await client.get("/api/v1/articles", { params: { page: 1, limit: 10, search: "aspirina" } });

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const calledUrl = fetchMock.mock.calls[0][0];
    expect(calledUrl).toContain("http://localhost:8000/api/v1/articles?page=1&limit=10&search=aspirina");
  });

  it("should inject Bearer token from localStorage when available", async () => {
    const mockStorage: Record<string, string> = { auth_token: "test-jwt-token" };
    vi.stubGlobal("window", {
      localStorage: {
        getItem: (key: string) => mockStorage[key] || null,
        removeItem: (key: string) => delete mockStorage[key],
      },
    });

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ data: "secure" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await client.get("/api/v1/articles");

    const requestHeaders = fetchMock.mock.calls[0][1].headers;
    expect(requestHeaders["Authorization"]).toBe("Bearer test-jwt-token");
  });

  it("should handle 401 Unauthorized by clearing storage and throwing ApiError", async () => {
    const mockStorage: Record<string, string> = { auth_token: "expired-token", auth_user: "{}" };
    vi.stubGlobal("window", {
      location: { pathname: "/dashboard", href: "" },
      localStorage: {
        getItem: (key: string) => mockStorage[key] || null,
        removeItem: (key: string) => delete mockStorage[key],
      },
    });

    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Token expired" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await expect(client.get("/api/v1/articles")).rejects.toThrow(ApiError);
    expect(mockStorage.auth_token).toBeUndefined();
    expect(mockStorage.auth_user).toBeUndefined();
  });

  it("should extract error details from backend 422 validation response", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({
        detail: [{ loc: ["body", "id_articulo"], msg: "Field required", type: "missing" }],
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    try {
      await client.post("/api/v1/stock/audit", {});
      expect.fail("Should have thrown");
    } catch (err: unknown) {
      expect(err).toBeInstanceOf(ApiError);
      const apiErr = err as ApiError;
      expect(apiErr.status).toBe(422);
      expect(apiErr.message).toContain("Field required");
    }
  });
});
