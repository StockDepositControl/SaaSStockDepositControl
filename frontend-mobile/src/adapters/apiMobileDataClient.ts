import AsyncStorage from '@react-native-async-storage/async-storage';
import { MobileDataClientPort } from '../ports/MobileDataClientPort';
import { ActiveTenantSession, LoginCredentials, AuthTokenResponse } from '../types/auth';
import { ArticuloAuditorView, ArticleStockPositionView, CatalogFilterParams, CatalogResult } from '../types/article';
import { AuditEntryRequest, AuditEntryResult, AuditDailyProgress } from '../types/audit';
import { decodeJwtClaims, extractInitials, extractFirstName } from '../utils/jwtDecoder';
import { API_CONFIG, STORAGE_KEYS } from '../utils/constants';

function parseErrorMessage(body: any, defaultMessage: string): string {
  if (!body) return defaultMessage;
  if (typeof body.detail === 'string') {
    if (body.detail === 'Invalid credentials') return 'Correo o contraseña incorrectos.';
    if (body.detail === 'User not found') return 'Usuario no encontrado.';
    return body.detail;
  }
  if (Array.isArray(body.detail)) {
    return body.detail.map((item: any) => item.msg || item.message || JSON.stringify(item)).join('. ');
  }
  return defaultMessage;
}

export class ApiMobileDataClient implements MobileDataClientPort {
  private readonly baseUrl: string;
  private currentSession: ActiveTenantSession | null = null;

  constructor(baseUrl: string = API_CONFIG.BASE_URL) {
    this.baseUrl = baseUrl.replace(/\/+$/, '');
  }

  /**
   * Defensive sanitizer: Recursively strips forbidden financial fields
   * (pcio_com_siva, monto_valorizado, applied_unit_cost) before entering state.
   */
  private stripFinancialFields<T>(data: T): T {
    if (Array.isArray(data)) {
      return data.map((item) => this.stripFinancialFields(item)) as unknown as T;
    }
    if (data !== null && typeof data === 'object') {
      const cleanObj: Record<string, unknown> = {};
      for (const [key, val] of Object.entries(data as Record<string, unknown>)) {
        if (key === 'pcio_com_siva' || key === 'monto_valorizado' || key === 'applied_unit_cost') {
          continue;
        }
        cleanObj[key] = this.stripFinancialFields(val);
      }
      return cleanObj as T;
    }
    return data;
  }

  private async getAuthHeaders(): Promise<Record<string, string>> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    };
    if (this.currentSession?.token) {
      headers.Authorization = `Bearer ${this.currentSession.token}`;
    }
    return headers;
  }

  async login(credentials: LoginCredentials): Promise<ActiveTenantSession> {
    const response = await fetch(`${this.baseUrl}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({
        email: credentials.email.trim().toLowerCase(),
        password: credentials.password,
      }),
    });

    if (!response.ok) {
      let detail = 'Error al iniciar sesión.';
      try {
        const body = await response.json();
        detail = parseErrorMessage(body, detail);
      } catch {
        // Fallback
      }
      throw new Error(detail);
    }

    const tokenData = (await response.json()) as AuthTokenResponse;
    const claims = decodeJwtClaims(tokenData.access_token);

    const roleLower = (claims.role || '').toLowerCase();
    if (roleLower !== 'auditor' && roleLower !== 'supervisor') {
      throw new Error('Acceso denegado: tu perfil no tiene permisos operativos móviles o se encuentra bloqueado.');
    }

    const tenantIdStr = String(claims.tenant_id || '1');
    const branchIdNum = Number(claims.branch_id || 1);
    const depositIdNum = 1;
    const userIdNum = Number(claims.id_usuario || claims.user_id || 1);
    const email = claims.sub || credentials.email;

    const session: ActiveTenantSession = {
      token: tokenData.access_token,
      email,
      displayName: extractFirstName(email),
      initials: extractInitials(email),
      role: roleLower as 'auditor' | 'supervisor',
      tenantId: tenantIdStr,
      branchId: branchIdNum,
      depositId: depositIdNum,
      userId: userIdNum,
      expiresAtMs: (claims.exp || 0) * 1000,
    };

    this.currentSession = session;
    await AsyncStorage.setItem(
      `${STORAGE_KEYS.SESSION_PREFIX}:${tenantIdStr}:${branchIdNum}`,
      JSON.stringify(session)
    );

    return session;
  }

  async logout(): Promise<void> {
    if (this.currentSession) {
      await AsyncStorage.removeItem(
        `${STORAGE_KEYS.SESSION_PREFIX}:${this.currentSession.tenantId}:${this.currentSession.branchId}`
      );
    }
    this.currentSession = null;
  }

  async restoreSession(): Promise<ActiveTenantSession | null> {
    const keys = await AsyncStorage.getAllKeys();
    const sessionKey = keys.find((k) => k.startsWith(STORAGE_KEYS.SESSION_PREFIX));
    if (!sessionKey) return null;

    const raw = await AsyncStorage.getItem(sessionKey);
    if (!raw) return null;

    try {
      const parsed = JSON.parse(raw) as ActiveTenantSession;
      if (parsed.expiresAtMs > Date.now()) {
        this.currentSession = parsed;
        return parsed;
      }
    } catch {
      // Ignored
    }
    return null;
  }

  async getDailyProgress(): Promise<AuditDailyProgress> {
    const headers = await this.getAuthHeaders();
    const depositId = this.currentSession?.depositId || 1;

    try {
      // 1. Fetch total count
      const totalRes = await fetch(`${this.baseUrl}/api/v1/articles?limit=1&id_deposito=${depositId}`, {
        headers,
      });
      const totalData = totalRes.ok ? await totalRes.json() : { total: 0 };
      const totalCount = totalData.total || 0;

      // 2. Fetch audited count
      const auditedRes = await fetch(
        `${this.baseUrl}/api/v1/articles?limit=1&id_deposito=${depositId}&fue_auditado=true`,
        { headers }
      );
      const auditedData = auditedRes.ok ? await auditedRes.json() : { total: 0 };
      const auditedCount = auditedData.total || 0;

      const pendingCount = Math.max(0, totalCount - auditedCount);
      const percentage = totalCount > 0 ? Math.round((auditedCount / totalCount) * 100) : 0;

      return {
        totalCount,
        auditedCount,
        pendingCount,
        percentage,
      };
    } catch {
      return {
        totalCount: 0,
        auditedCount: 0,
        pendingCount: 0,
        percentage: 0,
      };
    }
  }

  async searchArticles(query: string): Promise<ArticuloAuditorView[]> {
    const headers = await this.getAuthHeaders();
    const encoded = encodeURIComponent(query.trim());
    const res = await fetch(`${this.baseUrl}/api/v1/articles/search?query=${encoded}`, {
      headers,
    });

    if (!res.ok) {
      return [];
    }

    const rawList = (await res.json()) as any[];
    const sanitized = this.stripFinancialFields(rawList);

    return sanitized.map((item) => ({
      id_articulo: String(item.id_articulo),
      barcode: String(item.id_articulo),
      barcodes: [String(item.id_articulo)],
      code: String(item.id_articulo),
      des_articulo: item.des_articulo || 'Sin descripción',
      presentacion: item.presentacion || null,
      des_marca: item.des_marca || null,
      des_grupo: item.des_grupo || null,
      des_familia: item.des_familia || null,
      id_familia: item.id_familia ? String(item.id_familia) : null,
      id_grupo: item.id_grupo ? String(item.id_grupo) : null,
      status: item.fue_auditado ? 'audited' : 'pending',
      stock_real: typeof item.stock_real === 'number' ? item.stock_real : 0,
      fefo_expiration_date: item.fefo_expiration_date || null,
      fefo_lot_code: item.fefo_lot_code || null,
    }));
  }

  async getArticleCatalog(params?: CatalogFilterParams): Promise<CatalogResult<ArticuloAuditorView>> {
    const headers = await this.getAuthHeaders();
    const depositId = this.currentSession?.depositId || 1;
    const queryParts: string[] = [`limit=100`, `id_deposito=${depositId}`];

    if (params?.search) {
      queryParts.push(`search=${encodeURIComponent(params.search)}`);
    }
    if (params?.status === 'audited') {
      queryParts.push('fue_auditado=true');
    } else if (params?.status === 'pending') {
      queryParts.push('fue_auditado=false');
    }
    if (params?.familyId) {
      queryParts.push(`id_familia=${encodeURIComponent(params.familyId)}`);
    }

    const url = `${this.baseUrl}/api/v1/articles?${queryParts.join('&')}`;
    const res = await fetch(url, { headers });

    if (!res.ok) {
      return { items: [], total: 0 };
    }

    const data = await res.json();
    const rawItems = (data.items || data || []) as any[];
    const sanitized = this.stripFinancialFields(rawItems);

    let mapped: ArticuloAuditorView[] = sanitized.map((item) => ({
      id_articulo: String(item.id_articulo),
      barcode: String(item.id_articulo),
      barcodes: [String(item.id_articulo)],
      code: String(item.id_articulo),
      des_articulo: item.des_articulo || 'Sin descripción',
      presentacion: item.presentacion || null,
      des_marca: item.des_marca || null,
      des_grupo: item.des_grupo || null,
      des_familia: item.des_familia || null,
      id_familia: item.id_familia ? String(item.id_familia) : null,
      id_grupo: item.id_grupo ? String(item.id_grupo) : null,
      status: item.fue_auditado ? 'audited' : 'pending',
      stock_real: typeof item.stock_real === 'number' ? item.stock_real : 0,
      fefo_expiration_date: item.fefo_expiration_date || null,
      fefo_lot_code: item.fefo_lot_code || null,
    }));

    if (params?.criticalOnly) {
      mapped = mapped.filter((a) => a.stock_real === 0);
    }

    return {
      items: mapped,
      total: data.total ?? mapped.length,
    };
  }

  async getArticleStockPosition(articleId: string, depositId?: number): Promise<ArticleStockPositionView> {
    const headers = await this.getAuthHeaders();
    const resolvedDep = depositId || this.currentSession?.depositId || 1;
    const resolvedBranch = this.currentSession?.branchId || 1;

    const res = await fetch(
      `${this.baseUrl}/api/v1/stock/position?id_articulo=${encodeURIComponent(articleId)}&id_sucursal=${resolvedBranch}&id_deposito=${resolvedDep}`,
      { headers }
    );

    if (!res.ok) {
      let detail = `Error al obtener stock del artículo ${articleId}`;
      try {
        const body = await res.json();
        detail = parseErrorMessage(body, detail);
      } catch {
        // Fallback
      }
      throw new Error(detail);
    }

    const raw = await res.json();
    const clean = this.stripFinancialFields(raw) as any;

    return {
      id_articulo: clean.id_articulo || articleId,
      des_articulo: clean.des_articulo || '',
      presentacion: clean.presentacion || null,
      des_marca: clean.des_marca || null,
      des_familia: clean.des_familia || null,
      des_grupo: clean.des_grupo || null,
      id_sucursal: clean.id_sucursal || resolvedBranch,
      id_deposito: clean.id_deposito || resolvedDep,
      stock_real: typeof clean.stock_real === 'number' ? clean.stock_real : 0,
      lotes: clean.lotes || [],
    };
  }

  async registerAudit(request: AuditEntryRequest): Promise<AuditEntryResult> {
    const headers = await this.getAuthHeaders();

    const payload: Record<string, any> = {
      id_articulo: request.id_articulo,
      id_sucursal: request.id_sucursal || this.currentSession?.branchId || 1,
      id_deposito: request.id_deposito || this.currentSession?.depositId || 1,
      stock_fisico_contado: request.stock_fisico_contado,
      cantidad_afectada: request.cantidad_afectada,
      tipo_accion: request.tipo_accion,
      observation: request.observation,
    };

    const res = await fetch(`${this.baseUrl}/api/v1/stock/audit`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      let detail = 'Error al registrar la auditoría.';
      try {
        const body = await res.json();
        if (body.error_type === 'NoActiveWorkSession') {
          detail = 'No se encontró una sesión de trabajo activa para esta sucursal. Contactá a tu supervisor.';
        } else {
          detail = parseErrorMessage(body, detail);
        }
      } catch {
        // Fallback
      }
      throw new Error(detail);
    }

    const rawResult = await res.json();
    const cleanResult = this.stripFinancialFields(rawResult) as any;

    return {
      id_articulo: cleanResult.id_articulo,
      stock_real: cleanResult.stock_real,
      stock_fisico_contado: cleanResult.stock_fisico_contado,
      delta_stock: cleanResult.delta_stock,
      tipo_accion: cleanResult.tipo_accion,
      cantidad_afectada: cleanResult.cantidad_afectada,
      audit_quantity: cleanResult.audit_quantity,
      audit_id: cleanResult.audit_id,
    };
  }
}

export const apiMobileDataClient = new ApiMobileDataClient();
