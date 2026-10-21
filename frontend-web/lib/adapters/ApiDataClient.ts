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
  ApiAuditEntryRequest,
  ApiAuditEntryResult,
  ApiAuthToken,
  ApiDashboardKPIsResponse,
  ApiUserResponse,
  ApiUserStatusUpdate,
  ApiUserRoleAssignment,
} from "../types/api";
import { httpClient, HttpClient, ApiError } from "./httpClient";
import { parseJwt, mapRoleToUserRole } from "../utils/jwt";
import {
  mapArticleByRole,
  mapToDomainAuditResult,
  mapToDomainUser,
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

  private clearStoredSession(): void {
    window.localStorage.removeItem("auth_token");
    window.localStorage.removeItem("auth_user");
  }

  private getStoredUser(): MockUser | null {
    if (typeof window === "undefined" || !window.localStorage) {
      return null;
    }

    // A session is valid only when an unexpired token exists (parseJwt rejects expired tokens).
    const token = this.getStoredToken();
    const payload = token ? parseJwt(token) : null;
    if (!token || !payload) {
      this.clearStoredSession();
      return null;
    }

    const stored = window.localStorage.getItem("auth_user");
    if (stored) {
      try {
        return JSON.parse(stored) as MockUser;
      } catch {
        // parse error: rebuild from token below
      }
    }

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

  public async getUsers(includeInactive: boolean = true): Promise<MockUser[]> {
    const data = await this.http.get<ApiUserResponse[]>("/api/v1/users", {
      params: { include_inactive: includeInactive },
    });
    return (data || []).map(mapToDomainUser);
  }

  public async updateUserStatus(userId: string | number, isActive: boolean): Promise<MockUser> {
    const payload: ApiUserStatusUpdate = { is_active: isActive };
    const data = await this.http.patch<ApiUserResponse>(
      `/api/v1/users/${encodeURIComponent(String(userId))}/status`,
      payload
    );
    return mapToDomainUser(data);
  }

  public async updateUserRole(userId: string | number, role: UserRole): Promise<MockUser> {
    const payload: ApiUserRoleAssignment = { roles: [role] };
    const data = await this.http.put<ApiUserResponse>(
      `/api/v1/users/${encodeURIComponent(String(userId))}/roles`,
      payload
    );
    return mapToDomainUser(data);
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
    const token = this.getStoredToken();
    const claims = token ? parseJwt(token) : null;
    const branchId = entry.id_sucursal ?? (claims?.branch_id ? Number(claims.branch_id) : 1);
    const depositId = entry.id_deposito ?? 1;

    const payload: ApiAuditEntryRequest = {
      id_articulo: entry.id_articulo,
      id_sucursal: branchId,
      id_deposito: depositId,
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

    const data = await this.http.get<ApiDashboardKPIsResponse>("/api/v1/stock/kpis", {
      params: { id_deposito: 1 },
    });

    const baseKPIs: DashboardKPIsBase = {
      totalArticulos: Number(data.total_articulos) || 0,
      auditados: Number(data.auditados) || 0,
      pendientes: Number(data.pendientes) || 0,
      porcentajeAvance: Number(data.porcentaje_avance) || 0,
      discrepanciasAlta: Number(data.discrepancias_alta) || 0,
      discrepanciasBaja: Number(data.discrepancias_baja) || 0,
      sinAccion: Number(data.sin_accion) || 0,
      outOfStockCount: Number(data.out_of_stock_count) || 0,
    };

    if (!isAdmin) {
      return baseKPIs;
    }

    const montoValorizadoAlta = Number(data.monto_valorizado_alta) || 0;
    const montoValorizadoBaja = Number(data.monto_valorizado_baja) || 0;

    return {
      ...baseKPIs,
      montoValorizadoTotal: montoValorizadoAlta - montoValorizadoBaja,
      montoValorizadoAlta,
      montoValorizadoBaja,
    };
  }
}
