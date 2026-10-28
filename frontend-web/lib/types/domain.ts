export enum UserRole {
  ADMINISTRADOR = "administrador",
  SUPERVISOR = "supervisor",
  AUDITOR = "auditor",
}

export enum TipoAccion {
  ALTA = "Alta",
  BAJA = "Baja",
  SIN_ACCION = "Sin Acción",
}

export interface LoteDeposito {
  id_articulo: string;
  lote: string;
  vencimiento?: string | null;
  stock_real: number;
}

export interface StockPosition {
  id_articulo: string;
  id_sucursal: number;
  id_deposito: number;
  stock_real: number;
}

export interface ArticuloBase {
  id_articulo: string;
  cod_barras: string[];
  des_articulo: string;
  presentacion?: string | null;
  id_marca?: number | null;
  des_marca?: string | null;
  id_familia?: string | null;
  des_familia?: string | null;
  id_grupo?: string | null;
  des_grupo?: string | null;
  stock_real: number;
  lotes: LoteDeposito[];
  fue_auditado: boolean;
  ultimo_conteo_fisico?: number | null;
  vencimiento?: string | null;
}

// Supervisor & Auditor view (NO pcio_com_siva field)
export type ArticuloPublicView = ArticuloBase;
export type ArticuloSupervisorView = ArticuloPublicView;
export type ArticuloAuditorView = ArticuloPublicView;

// Admin view (strictly includes pcio_com_siva)
export interface ArticuloAdminView extends ArticuloBase {
  pcio_com_siva: number;
}

// Internal full data type kept in mock store
export interface ArticuloInternal extends ArticuloBase {
  pcio_com_siva: number;
}

export interface AuditEntry {
  id_articulo: string;
  stock_fisico_contado: number;
  id_sucursal?: number | null;
  id_deposito?: number | null;
  lote?: string | null;
  observation?: string | null;
}

export interface AuditResult {
  client_uuid: string;
  audit_id?: number;
  id_articulo: string;
  des_articulo: string;
  stock_real: number;
  stock_fisico_contado: number;
  delta_stock: number;
  tipo_accion: TipoAccion;
  cantidad_afectada: number;
  audit_quantity: number;
  monto_valorizado: number;
  applied_vat_rate: number;
  lote?: string | null;
  vencimiento?: string | null;
  observation?: string | null;
  scan_timestamp: string;
}

export interface DashboardKPIsBase {
  totalArticulos: number;
  auditados: number;
  pendientes: number;
  porcentajeAvance: number;
  discrepanciasAlta: number;
  discrepanciasBaja: number;
  sinAccion: number;
  outOfStockCount: number;
}

export interface DashboardKPIsAdmin extends DashboardKPIsBase {
  montoValorizadoTotal: number;
  montoValorizadoAlta: number;
  montoValorizadoBaja: number;
}

/**
 * Runtime type guard to safely discriminate Admin KPIs with valorized financial fields.
 */
export function isAdminKPIs(
  kpis: DashboardKPIsBase | DashboardKPIsAdmin | null | undefined
): kpis is DashboardKPIsAdmin {
  return (
    kpis != null &&
    "montoValorizadoBaja" in kpis &&
    typeof kpis.montoValorizadoBaja === "number"
  );
}

export interface MockUser {
  id: string;
  email: string;
  password?: string;
  name: string;
  first_name?: string;
  last_name?: string;
  role: UserRole;
  badgeToken?: string;
  avatar?: string;
  is_active?: boolean;
  tenant_id?: number;
  branch_id?: number | null;
}

export interface UserSession {
  user: MockUser;
  token: string;
  expires_at: string;
}


export interface ArticleCatalogQuery {
  page?: number;
  limit?: number;
  search?: string;
  id_familia?: string;
  id_grupo?: string;
  fue_auditado?: boolean;
  id_deposito?: number;
}

export interface PaginatedArticlesResult {
  items: (ArticuloPublicView | ArticuloAdminView)[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface ArticleFamily {
  id_familia: string;
  des_familia: string;
}
