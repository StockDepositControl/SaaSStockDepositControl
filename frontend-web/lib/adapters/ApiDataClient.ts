import { DataClientPort } from "../ports/DataClientPort";
import {
  UserRole,
  ArticuloPublicView,
  ArticuloAdminView,
  AuditEntry,
  AuditResult,
  DashboardKPIsBase,
  DashboardKPIsAdmin,
  MockUser,
} from "../types/domain";
import {
  ApiArticleListResponse,
  ApiArticuloAdminOut,
  ApiArticuloPublicOut,
  ApiAuditEntryResult,
  ApiAuthToken,
  ApiDailyInventoryBalanceResponse,
} from "../types/api";
import { httpClient, HttpClient, ApiError } from "./httpClient";
import { parseJwt, mapRoleToUserRole } from "../utils/jwt";
import {
  mapArticleByRole,
  mapToDomainAuditResult,
} from "./mappers";

export class ApiDataClient implements DataClientPort {
  private http: HttpClient;
  private sessionAuditLogs: AuditResult[] = [];

  constructor(customHttpClient?: HttpClient) {
    this.http = customHttpClient || httpClient;
  }

  public getCurrentRole(): UserRole {
    const user = this.getStoredUser();
    return user ? user.role : UserRole.AUDITOR;
  }

  public setRole(_role: UserRole): void {
    // In live backend mode, RBAC is governed by the server-issued JWT token.
    console.warn("ApiDataClient: setRole is a no-op in API mode. Role is derived from authenticated JWT.");
  }

  private getStoredToken(): string | null {
    if (typeof window !== "undefined" && window.localStorage) {
      return window.localStorage.getItem("auth_token");
    }
    return null;
  }

  private getStoredUser(): MockUser | null {
    if (typeof window !== "undefined" && window.localStorage) {
      const stored = window.localStorage.getItem("auth_user");
      if (stored) {
        try {
          return JSON.parse(stored) as MockUser;
        } catch {
          // parse error
        }
      }
      // Reconstruct from token if present and valid
      const token = this.getStoredToken();
      if (token) {
        const payload = parseJwt(token);
        if (payload) {
          const user: MockUser = {
            id: String(payload.user_id || payload.id_usuario || payload.sub),
            email: payload.sub,
            password: "",
            name: payload.sub.split("@")[0],
            role: mapRoleToUserRole(payload.role),
            badgeToken: token,
          };
          window.localStorage.setItem("auth_user", JSON.stringify(user));
          return user;
        }
      }
    }
    return null;
  }

  public async login(email: string, password: string = "password123"): Promise<MockUser> {
    const data = await this.http.post<ApiAuthToken>("/api/v1/auth/login", {
      email,
      password,
    });

    const payload = parseJwt(data.access_token);
    if (!payload) {
      throw new ApiError(400, "Received invalid or unparseable JWT from backend");
    }

    const user: MockUser = {
      id: String(payload.user_id || payload.id_usuario || payload.sub),
      email: payload.sub,
      password: "",
      name: payload.sub.split("@")[0],
      role: mapRoleToUserRole(payload.role),
      badgeToken: data.access_token,
      is_active: true,
    };

    if (typeof window !== "undefined" && window.localStorage) {
      window.localStorage.setItem("auth_token", data.access_token);
      window.localStorage.setItem("auth_user", JSON.stringify(user));
    }

    return user;
  }

  public logout(): void {
    if (typeof window !== "undefined" && window.localStorage) {
      window.localStorage.removeItem("auth_token");
      window.localStorage.removeItem("auth_user");
    }
    this.sessionAuditLogs = [];
  }

  public async getCurrentUser(): Promise<MockUser | null> {
    return this.getStoredUser();
  }

  public async getUsers(): Promise<MockUser[]> {
    const currentUser = await this.getCurrentUser();
    if (currentUser) {
      return [currentUser];
    }
    return [];
  }

  public switchUser(_userId: string): void {
    console.warn("ApiDataClient: switchUser is disabled in API mode. Please use login with account credentials.");
  }

  public resetData(): void {
    this.sessionAuditLogs = [];
  }

  public async getArticulos(role?: UserRole): Promise<(ArticuloPublicView | ArticuloAdminView)[]> {
    const effectiveRole = role || this.getCurrentRole();
    const data = await this.http.get<ApiArticleListResponse>("/api/v1/articles", {
      params: { page: 1, limit: 100 },
    });

    return (data.items || []).map((item) => mapArticleByRole(item, effectiveRole));
  }

  public async getArticuloByBarcode(
    barcodeOrId: string,
    role?: UserRole
  ): Promise<ArticuloPublicView | ArticuloAdminView | null> {
    const effectiveRole = role || this.getCurrentRole();
    try {
      const data = await this.http.get<ApiArticuloAdminOut | ApiArticuloPublicOut>(
        `/api/v1/articles/${encodeURIComponent(barcodeOrId)}`
      );
      if (!data) return null;
      return mapArticleByRole(data, effectiveRole);
    } catch (err: unknown) {
      if (err instanceof ApiError && err.status === 404) {
        // Fallback to search if direct ID lookup fails
        const searchResults = await this.searchArticulos(barcodeOrId, effectiveRole);
        return searchResults.length > 0 ? searchResults[0] : null;
      }
      throw err;
    }
  }

  public async searchArticulos(
    query: string,
    role?: UserRole
  ): Promise<(ArticuloPublicView | ArticuloAdminView)[]> {
    const effectiveRole = role || this.getCurrentRole();
    const trimmed = query.trim();
    if (!trimmed) {
      return this.getArticulos(effectiveRole);
    }

    const data = await this.http.get<(ApiArticuloAdminOut | ApiArticuloPublicOut)[]>(
      "/api/v1/articles/search",
      { params: { query: trimmed } }
    );

    return (data || []).map((item) => mapArticleByRole(item, effectiveRole));
  }

  public async registerAudit(entry: AuditEntry): Promise<AuditResult> {
    const payload = {
      id_articulo: entry.id_articulo,
      stock_fisico_contado: entry.stock_fisico_contado,
      observation: entry.observation || null,
    };

    const result = await this.http.post<ApiAuditEntryResult>("/api/v1/stock/audit", payload);
    const domainResult = mapToDomainAuditResult(result, entry.id_articulo, entry.observation);
    this.sessionAuditLogs.unshift(domainResult);
    return domainResult;
  }

  public async getAuditLog(): Promise<AuditResult[]> {
    return [...this.sessionAuditLogs];
  }

  public async getKPIs(role?: UserRole): Promise<DashboardKPIsBase | DashboardKPIsAdmin> {
    const effectiveRole = role || this.getCurrentRole();
    const isAdmin = effectiveRole === UserRole.ADMINISTRADOR;

    // Fetch live articles count to calculate progress and base quantities
    let totalArticulos = 0;
    let auditados = 0;
    try {
      const articlesRes = await this.http.get<ApiArticleListResponse>("/api/v1/articles", {
        params: { page: 1, limit: 1 },
      });
      totalArticulos = articlesRes.total || 0;
    } catch {
      totalArticulos = 0;
    }

    // Try fetching audited count if supported
    try {
      const auditedRes = await this.http.get<ApiArticleListResponse>("/api/v1/articles", {
        params: { page: 1, limit: 1, fue_auditado: true },
      });
      auditados = auditedRes.total || 0;
    } catch {
      auditados = this.sessionAuditLogs.length;
    }

    const pendientes = Math.max(0, totalArticulos - auditados);
    const porcentajeAvance = totalArticulos > 0 ? Math.round((auditados / totalArticulos) * 100) : 0;

    let discrepanciasAlta = 0;
    let discrepanciasBaja = 0;
    let sinAccion = 0;

    this.sessionAuditLogs.forEach((log) => {
      if (log.delta_stock > 0) discrepanciasAlta++;
      else if (log.delta_stock < 0) discrepanciasBaja++;
      else sinAccion++;
    });

    const baseKPIs: DashboardKPIsBase = {
      totalArticulos,
      auditados,
      pendientes,
      porcentajeAvance,
      discrepanciasAlta,
      discrepanciasBaja,
      sinAccion,
    };

    if (!isAdmin) {
      return baseKPIs;
    }

    // Attempt to query financial totals from live backend report if available
    let montoValorizadoAlta = 0;
    let montoValorizadoBaja = 0;
    let montoValorizadoTotal = 0;

    try {
      const today = new Date().toISOString().split("T")[0];
      const past30Days = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split("T")[0];
      const balance = await this.http.get<ApiDailyInventoryBalanceResponse>("/api/v1/reports/inventory-balance", {
        params: { start_date: past30Days, end_date: today },
      });
      montoValorizadoTotal = Number(balance.total_net_patrimonial_variation) || 0;
    } catch {
      // If reports endpoint is pending or restricted, aggregate from active session audit results
      this.sessionAuditLogs.forEach((log) => {
        if (log.delta_stock > 0) montoValorizadoAlta += log.monto_valorizado;
        if (log.delta_stock < 0) montoValorizadoBaja += log.monto_valorizado;
      });
      montoValorizadoTotal = montoValorizadoAlta - montoValorizadoBaja;
    }

    return {
      ...baseKPIs,
      montoValorizadoTotal,
      montoValorizadoAlta,
      montoValorizadoBaja,
    };
  }
}
