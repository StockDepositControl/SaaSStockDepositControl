// @vitest-environment jsdom
import { describe, it, expect, beforeEach, vi } from "vitest";
import { ApiDataClient } from "./ApiDataClient";
import { HttpClient } from "./httpClient";
import { UserRole, DashboardKPIsAdmin } from "../types/domain";

describe("ApiDataClient", () => {
  let mockHttp: HttpClient;
  let client: ApiDataClient;

  beforeEach(() => {
    window.localStorage.clear();
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
      id_sucursal: 1,
      id_deposito: 1,
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

  it("registerAudit extracts branch_id from JWT token claims and defaults deposit to 1", async () => {
    const token =
      "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9." +
      "eyJzdWIiOiJhdWRpdG9yQGV4YW1wbGUuY29tIiwicm9sZSI6ImF1ZGl0b3IiLCJ0ZW5hbnRfaWQiOjEsImJyYW5jaF9pZCI6MiwiZXhwIjoyNTM0MDIzMDA3OTl9." +
      "signature";
    window.localStorage.setItem("auth_token", token);

    const postSpy = vi.spyOn(mockHttp, "post").mockResolvedValue({
      client_uuid: "uuid-100",
      id_articulo: "ART-1",
      stock_real: 200,
      stock_fisico_contado: 200,
      delta_stock: 0,
      tipo_accion: "Sin Acción",
      cantidad_afectada: 0,
      audit_quantity: 200,
      monto_valorizado: "0.00",
      audit_id: 2,
    });

    await client.registerAudit({
      id_articulo: "ART-1",
      stock_fisico_contado: 200,
    });

    expect(postSpy).toHaveBeenCalledWith("/api/v1/stock/audit", {
      id_articulo: "ART-1",
      id_sucursal: 2,
      id_deposito: 1,
      stock_fisico_contado: 200,
      observation: null,
    });
  });

  it("registerAudit honors explicit id_sucursal and id_deposito overrides", async () => {
    const postSpy = vi.spyOn(mockHttp, "post").mockResolvedValue({
      client_uuid: "uuid-101",
      id_articulo: "ART-1",
      stock_real: 200,
      stock_fisico_contado: 210,
      delta_stock: 10,
      tipo_accion: "Alta",
      cantidad_afectada: 10,
      audit_quantity: 210,
      monto_valorizado: "1500.00",
      audit_id: 3,
    });

    await client.registerAudit({
      id_articulo: "ART-1",
      stock_fisico_contado: 210,
      id_sucursal: 3,
      id_deposito: 2,
      observation: "Recuento manual",
    });

    expect(postSpy).toHaveBeenCalledWith("/api/v1/stock/audit", {
      id_articulo: "ART-1",
      id_sucursal: 3,
      id_deposito: 2,
      stock_fisico_contado: 210,
      observation: "Recuento manual",
    });
  });

  describe("getKPIs", () => {
    const apiPayload = {
      total_articulos: 100,
      auditados: 40,
      pendientes: 60,
      porcentaje_avance: 40,
      discrepancias_alta: 3,
      discrepancias_baja: 5,
      sin_accion: 32,
      out_of_stock_count: 12,
      monto_valorizado_baja: "8900.50",
      monto_valorizado_alta: "1200.00",
    };

    it("executes exactly ONE HTTP call to /api/v1/stock/kpis", async () => {
      const getSpy = vi.spyOn(mockHttp, "get").mockResolvedValue(apiPayload);

      await client.getKPIs(UserRole.AUDITOR);

      expect(getSpy).toHaveBeenCalledTimes(1);
      expect(getSpy).toHaveBeenCalledWith("/api/v1/stock/kpis", {
        params: { id_deposito: 1 },
      });
    });

    it("maps outOfStockCount and omits financial fields for non-admin", async () => {
      vi.spyOn(mockHttp, "get").mockResolvedValue(apiPayload);

      const kpis = await client.getKPIs(UserRole.SUPERVISOR);

      expect(kpis.outOfStockCount).toBe(12);
      expect(kpis.totalArticulos).toBe(100);
      expect(kpis.porcentajeAvance).toBe(40);
      expect("montoValorizadoBaja" in kpis).toBe(false);
      expect("montoValorizadoAlta" in kpis).toBe(false);
    });

    it("maps financial amounts for administrator", async () => {
      vi.spyOn(mockHttp, "get").mockResolvedValue(apiPayload);

      const kpis = (await client.getKPIs(UserRole.ADMINISTRADOR)) as DashboardKPIsAdmin;

      expect(kpis.outOfStockCount).toBe(12);
      expect(kpis.montoValorizadoBaja).toBe(8900.5);
      expect(kpis.montoValorizadoAlta).toBe(1200);
    });
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
