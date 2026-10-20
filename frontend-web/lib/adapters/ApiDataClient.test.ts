// @vitest-environment jsdom
import { describe, it, expect, beforeEach, vi } from "vitest";
import { ApiDataClient } from "./ApiDataClient";
import { HttpClient } from "./httpClient";
import { UserRole } from "../types/domain";

describe("ApiDataClient", () => {
  let mockHttp: HttpClient;
  let client: ApiDataClient;

  beforeEach(() => {
    mockHttp = new HttpClient("http://localhost:8000");
    client = new ApiDataClient(mockHttp);
    vi.restoreAllMocks();
  });

  it("login authenticates, saves token, and returns user", async () => {
    // Valid token for user_0@example.com (role: administrador)
    const token =
      "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9." +
      "eyJzdWIiOiJ1c2VyXzBAZXhhbXBsZS5jb20iLCJyb2xlIjoiYWRtaW5pc3RyYWRvciIsInRlbmFudF9pZCI6MSwiYnJhbmNoX2lkIjoxLCJ1c2VyX2lkIjoxMCwiZXhwIjoyNTM0MDIzMDA3OTl9." +
      "signature";

    const postSpy = vi.spyOn(mockHttp, "post").mockResolvedValue({
      access_token: token,
      token_type: "bearer",
    });

    const user = await client.login("user_0@example.com", "password123");

    expect(postSpy).toHaveBeenCalledWith("/api/v1/auth/login", {
      email: "user_0@example.com",
      password: "password123",
    });
    expect(user.email).toBe("user_0@example.com");
    expect(user.role).toBe(UserRole.ADMINISTRADOR);
  });

  it("getArticulos fetches from /api/v1/articles and maps articles", async () => {
    const getSpy = vi.spyOn(mockHttp, "get").mockResolvedValue({
      items: [
        {
          id_articulo: "ART-1",
          des_articulo: "Paracetamol 500mg",
          stock_real: 200,
          fue_auditado: false,
          pcio_com_siva: "150.00",
        },
      ],
      total: 1,
      page: 1,
      limit: 100,
      pages: 1,
    });

    // When role is AUDITOR, pcio_com_siva is omitted
    const articlesAuditor = await client.getArticulos(UserRole.AUDITOR);
    expect(articlesAuditor.length).toBe(1);
    expect(articlesAuditor[0].id_articulo).toBe("ART-1");
    expect("pcio_com_siva" in articlesAuditor[0]).toBe(false);

    // When role is ADMINISTRADOR, pcio_com_siva is present
    const articlesAdmin = await client.getArticulos(UserRole.ADMINISTRADOR);
    expect(articlesAdmin.length).toBe(1);
    expect("pcio_com_siva" in articlesAdmin[0]).toBe(true);
  });

  it("registerAudit posts to /api/v1/stock/audit and maps domain result", async () => {
    const postSpy = vi.spyOn(mockHttp, "post").mockResolvedValue({
      client_uuid: "uuid-999",
      id_articulo: "ART-1",
      stock_real: 200,
      stock_fisico_contado: 195,
      delta_stock: -5,
      tipo_accion: "Baja",
      cantidad_afectada: 5,
      audit_quantity: 195,
      monto_valorizado: "750.00",
      audit_id: 1,
    });

    const result = await client.registerAudit({
      id_articulo: "ART-1",
      stock_fisico_contado: 195,
      observation: "Conteo físico",
    });

    expect(postSpy).toHaveBeenCalledWith("/api/v1/stock/audit", {
      id_articulo: "ART-1",
      stock_fisico_contado: 195,
      observation: "Conteo físico",
    });
    expect(result.id_articulo).toBe("ART-1");
    expect(result.delta_stock).toBe(-5);
    expect(result.monto_valorizado).toBe(750);

    const logs = await client.getAuditLog();
    expect(logs.length).toBe(1);
    expect(logs[0].client_uuid).toBe("uuid-999");
  });

  describe("stored session validation", () => {
    const makeToken = (exp: number) => {
      const payload = btoa(
        JSON.stringify({ sub: "u@example.com", role: "auditor", user_id: 7, exp })
      );
      return `h.${payload}.s`;
    };

    beforeEach(() => {
      window.localStorage.clear();
    });

    it("returns null and purges storage when token is expired", async () => {
      window.localStorage.setItem("auth_token", makeToken(1));
      window.localStorage.setItem("auth_user", JSON.stringify({ id: "7" }));

      expect(await client.getCurrentUser()).toBeNull();
      expect(window.localStorage.getItem("auth_token")).toBeNull();
      expect(window.localStorage.getItem("auth_user")).toBeNull();
    });

    it("does not trust cached auth_user when token is missing", async () => {
      window.localStorage.setItem("auth_user", JSON.stringify({ id: "7" }));

      expect(await client.getCurrentUser()).toBeNull();
      expect(window.localStorage.getItem("auth_user")).toBeNull();
    });

    it("restores user from a valid unexpired token", async () => {
      window.localStorage.setItem("auth_token", makeToken(9999999999));

      const user = await client.getCurrentUser();
      expect(user?.email).toBe("u@example.com");
      expect(user?.role).toBe(UserRole.AUDITOR);
    });
  });
});
