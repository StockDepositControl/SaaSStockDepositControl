import { TipoAccion } from "./domain";

export interface ApiAuthToken {
  access_token: string;
  token_type: string;
}

export interface ApiJwtPayload {
  sub: string;
  role: string;
  tenant_id: number | string;
  branch_id?: number | null;
  user_id?: number;
  id_usuario?: number;
  exp?: number;
  iat?: number;
}

export interface ApiArticuloBase {
  id_articulo: string;
  des_articulo: string;
  presentacion?: string | null;
  id_marca?: number | null;
  des_marca?: string | null;
  id_familia?: string | null;
  des_familia?: string | null;
  id_grupo?: string | null;
  des_grupo?: string | null;
  stock_real?: number | null;
  fue_auditado?: boolean;
}

export interface ApiArticuloPublicOut extends ApiArticuloBase {
  pcio_com_siva?: never;
}

export interface ApiArticuloAdminOut extends ApiArticuloBase {
  pcio_com_siva: string | number;
}

export interface ApiArticleListResponse {
  items: (ApiArticuloAdminOut | ApiArticuloPublicOut)[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface ApiAuditEntryRequest {
  id_articulo: string;
  stock_fisico_contado?: number | null;
  cantidad_afectada?: number | null;
  tipo_accion?: TipoAccion | null;
  id_sucursal?: number | null;
  id_deposito?: number | null;
  observation?: string | null;
}

export interface ApiAuditEntryResult {
  client_uuid: string;
  id_articulo: string;
  stock_real: number;
  stock_fisico_contado?: number | null;
  delta_stock: number;
  tipo_accion: TipoAccion;
  cantidad_afectada: number;
  audit_quantity: number;
  monto_valorizado: string | number;
  audit_id?: number | null;
}

export interface ApiShrinkageLineItem {
  article_code: string;
  des_articulo: string;
  des_familia: string;
  pcio_com_siva: string | number;
  vat_rate: string | number;
  total_unit_cost: string | number;
  total_quantity: number;
  total_financial_loss: string | number;
  barcode?: string;
  reason?: string;
  quantity_shrinkage?: number;
  financial_erosion?: string | number;
}

export interface ApiShrinkageReportResponse {
  tenant_id: string;
  start_date: string;
  end_date: string;
  default_vat_rate: string | number;
  total_items: number;
  total_shrinkage_units: number;
  total_financial_erosion: string | number;
  line_items: ApiShrinkageLineItem[];
}

export interface ApiGoodsReceivedLineItem {
  barcode?: string;
  article_code: string;
  des_articulo: string;
  des_familia: string;
  reason: string;
  quantity_added: number;
  pcio_com_siva: string | number;
  vat_rate: string | number;
  total_unit_cost: string | number;
  capital_inyectado: string | number;
}

export interface ApiGoodsReceivedReportResponse {
  tenant_id: string;
  start_date: string;
  end_date: string;
  default_vat_rate: string | number;
  total_items: number;
  total_added_units: number;
  total_goods_received_units?: number;
  total_capital_inyectado: string | number;
  total_capital_injected?: string | number;
  line_items: ApiGoodsReceivedLineItem[];
}

export interface ApiDailyInventoryBalanceSummary {
  report_date: string;
  total_audit_articles: number;
  total_processed_units: number;
  total_addition_units: number;
  total_shrinkage_units: number;
  total_addition_value: string | number;
  total_shrinkage_value: string | number;
  net_patrimonial_variation: string | number;
}

export interface ApiDailyInventoryBalanceResponse {
  tenant_id: string;
  branch_id?: number | null;
  start_date: string;
  end_date: string;
  total_days: number;
  total_addition_value?: string | number;
  total_shrinkage_value?: string | number;
  net_patrimonial_variation: string | number;
  total_net_patrimonial_variation?: string | number;
  daily_summaries: ApiDailyInventoryBalanceSummary[];
}

// Mirrors backend DashboardKPIsPublicOut (no financial fields for non-admin roles).
export interface ApiDashboardKPIsPublicOut {
  total_articulos: number;
  auditados: number;
  pendientes: number;
  porcentaje_avance: number;
  discrepancias_alta: number;
  discrepancias_baja: number;
  sin_accion: number;
  out_of_stock_count: number;
}

// Mirrors backend DashboardKPIsResponse (administrator only).
export interface ApiDashboardKPIsResponse extends ApiDashboardKPIsPublicOut {
  monto_valorizado_baja?: string | number | null;
  monto_valorizado_alta?: string | number | null;
}

// User Management API Contracts
export interface ApiUserResponse {
  user_id: number;
  tenant_id: number;
  first_name: string;
  last_name: string;
  email: string;
  branch_id?: number | null;
  is_active: boolean;
  roles: string[];
}

export interface ApiUserStatusUpdate {
  is_active: boolean;
}

export interface ApiUserRoleAssignment {
  roles: string[];
}

