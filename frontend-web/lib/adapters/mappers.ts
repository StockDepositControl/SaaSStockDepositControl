import {
  UserRole,
  ArticuloPublicView,
  ArticuloAdminView,
  AuditResult,
  TipoAccion,
} from "../types/domain";
import {
  ApiArticuloAdminOut,
  ApiArticuloPublicOut,
  ApiAuditEntryResult,
} from "../types/api";

/**
 * Whitelist mapper for public article view (Auditor & Supervisor).
 * Guaranteed to NEVER include pcio_com_siva in the output structure.
 */
export function mapToArticuloPublicView(
  raw: ApiArticuloPublicOut | ApiArticuloAdminOut
): ArticuloPublicView {
  return {
    id_articulo: String(raw.id_articulo),
    cod_barras: [String(raw.id_articulo)],
    des_articulo: raw.des_articulo || "",
    presentacion: raw.presentacion ?? null,
    id_marca: raw.id_marca ?? null,
    des_marca: raw.des_marca ?? null,
    id_familia: raw.id_familia ?? null,
    des_familia: raw.des_familia ?? null,
    id_grupo: raw.id_grupo ?? null,
    des_grupo: raw.des_grupo ?? null,
    stock_real: raw.stock_real !== null && raw.stock_real !== undefined ? Number(raw.stock_real) : 0,
    lotes: [],
    fue_auditado: Boolean(raw.fue_auditado),
    ultimo_conteo_fisico: null,
    vencimiento: null,
  };
}

/**
 * Whitelist mapper for admin article view.
 * Exclusively assigns pcio_com_siva as a parsed numeric value.
 */
export function mapToArticuloAdminView(
  raw: ApiArticuloAdminOut
): ArticuloAdminView {
  const base = mapToArticuloPublicView(raw);
  const cost = raw.pcio_com_siva !== undefined && raw.pcio_com_siva !== null
    ? Number(raw.pcio_com_siva)
    : 0;

  return {
    ...base,
    pcio_com_siva: isNaN(cost) ? 0 : cost,
  };
}

/**
 * Role-aware article mapper enforcing strict structural separation.
 */
export function mapArticleByRole(
  raw: ApiArticuloAdminOut | ApiArticuloPublicOut,
  role: UserRole = UserRole.AUDITOR
): ArticuloPublicView | ArticuloAdminView {
  if (role === UserRole.ADMINISTRADOR) {
    return mapToArticuloAdminView(raw as ApiArticuloAdminOut);
  }
  return mapToArticuloPublicView(raw);
}

/**
 * Normalizes backend TipoAccion enum string to domain TipoAccion.
 */
export function mapTipoAccion(actionStr: string): TipoAccion {
  const normalized = (actionStr || "").toLowerCase().trim();
  if (normalized.includes("alta")) {
    return TipoAccion.ALTA;
  }
  if (normalized.includes("baja")) {
    return TipoAccion.BAJA;
  }
  return TipoAccion.SIN_ACCION;
}

/**
 * Maps backend AuditEntryResult to domain AuditResult.
 */
export function mapToDomainAuditResult(
  apiResult: ApiAuditEntryResult,
  des_articulo: string = "Artículo Auditado",
  observation?: string | null
): AuditResult {
  const monto = apiResult.monto_valorizado !== undefined && apiResult.monto_valorizado !== null
    ? Number(apiResult.monto_valorizado)
    : 0;

  return {
    client_uuid: apiResult.client_uuid,
    audit_id: apiResult.audit_id ?? undefined,
    id_articulo: apiResult.id_articulo,
    des_articulo,
    stock_real: Number(apiResult.stock_real || 0),
    stock_fisico_contado: Number(apiResult.stock_fisico_contado ?? apiResult.stock_real),
    delta_stock: Number(apiResult.delta_stock || 0),
    tipo_accion: mapTipoAccion(String(apiResult.tipo_accion)),
    cantidad_afectada: Number(apiResult.cantidad_afectada || 0),
    audit_quantity: Number(apiResult.audit_quantity || 0),
    monto_valorizado: isNaN(monto) ? 0 : monto,
    applied_vat_rate: 0.21,
    observation: observation ?? null,
    scan_timestamp: new Date().toISOString(),
  };
}
