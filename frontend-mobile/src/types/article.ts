/**
 * Role-Scoped Article DTOs & Views
 * Strict Field-Level RBAC: pcio_com_siva is strictly and structurally absent.
 */

export type ArticleAuditStatus = 'pending' | 'audited';

export interface LotItemView {
  lote: string;
  vencimiento: string | null;
  stock_real: number;
}

export interface ArticuloAuditorView {
  id_articulo: string;
  barcode: string;
  barcodes: string[];
  code: string;
  des_articulo: string;
  presentacion?: string | null;
  des_marca?: string | null;
  des_grupo?: string | null;
  des_familia?: string | null;
  id_familia?: string | null;
  id_grupo?: string | null;
  status: ArticleAuditStatus;
  stock_real: number;
  fefo_expiration_date?: string | null;
  fefo_lot_code?: string | null;
}

export interface ArticuloSupervisorView extends ArticuloAuditorView {
  last_audited_by?: string | null;
  last_audited_at?: string | null;
}

export interface ArticleStockPositionView {
  id_articulo: string;
  des_articulo: string;
  presentacion?: string | null;
  des_marca?: string | null;
  des_familia?: string | null;
  des_grupo?: string | null;
  id_sucursal: number;
  id_deposito: number;
  stock_real: number;
  lotes?: LotItemView[];
}

export interface CatalogFilterParams {
  search?: string;
  status?: 'all' | 'pending' | 'audited';
  criticalOnly?: boolean;
  familyId?: string;
}

export interface CatalogResult<T> {
  items: T[];
  total: number;
}
