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

  describe("Relative URL & Reverse Proxy Ingress Support", () => {
    it("should default to empty baseUrl when NEXT_PUBLIC_API_URL is unset or empty", () => {
      const defaultClient = new HttpClient("");
      expect(defaultClient.getBaseUrl()).toBe("");
    });

    it("should preserve relative path without params when baseUrl is empty", async () => {
      const relativeClient = new HttpClient("");
      const fetchMock = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ success: true }),
      });
      vi.stubGlobal("fetch", fetchMock);

      await relativeClient.get("/api/v1/articles");

      expect(fetchMock).toHaveBeenCalledTimes(1);
      const calledUrl = fetchMock.mock.calls[0][0];
      expect(calledUrl).toBe("/api/v1/articles");
    });

    it("should safely append query params to relative path without throwing Invalid URL", async () => {
      const relativeClient = new HttpClient("");
      const fetchMock = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ success: true }),
      });
      vi.stubGlobal("fetch", fetchMock);

      await relativeClient.get("/api/v1/articles", {
        params: { page: 1, limit: 10, search: "paracetamol" },
      });

      expect(fetchMock).toHaveBeenCalledTimes(1);
      const calledUrl = fetchMock.mock.calls[0][0];
      expect(calledUrl).toBe("/api/v1/articles?page=1&limit=10&search=paracetamol");
    });

    it("should use window.location.origin as base for query param parsing in browser environment", async () => {
      vi.stubGlobal("window", {
        location: { origin: "http://192.168.1.100:8080" },
      });

      const relativeClient = new HttpClient("");
      const fetchMock = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ success: true }),
      });
      vi.stubGlobal("fetch", fetchMock);

      await relativeClient.get("/api/v1/health", { params: { check: "db" } });

      expect(fetchMock).toHaveBeenCalledTimes(1);
      const calledUrl = fetchMock.mock.calls[0][0];
      expect(calledUrl).toBe("/api/v1/health?check=db");
    });

    it("should use fallback origin in non-browser environment without throwing", async () => {
      vi.stubGlobal("window", undefined);

      const relativeClient = new HttpClient("");
      const fetchMock = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ success: true }),
      });
      vi.stubGlobal("fetch", fetchMock);

      await relativeClient.get("/api/v1/metrics", { params: { period: "day" } });

      expect(fetchMock).toHaveBeenCalledTimes(1);
      const calledUrl = fetchMock.mock.calls[0][0];
      expect(calledUrl).toBe("/api/v1/metrics?period=day");
    });

    it("should preserve fully qualified absolute path regardless of baseUrl", async () => {
      const relativeClient = new HttpClient("");
      const fetchMock = vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({ success: true }),
      });
      vi.stubGlobal("fetch", fetchMock);

      await relativeClient.get("https://external-service.org/v1/status", {
        params: { verbose: true },
      });

      expect(fetchMock).toHaveBeenCalledTimes(1);
      const calledUrl = fetchMock.mock.calls[0][0];
      expect(calledUrl).toBe("https://external-service.org/v1/status?verbose=true");
    });
  });
});
