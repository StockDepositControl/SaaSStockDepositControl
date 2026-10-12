/**
 * Audit Movement & Operation Types
 */

export type MobileActionType = 'Alta' | 'Baja' | 'Sin Acción';

export interface AuditMotive {
  id: string;
  label: string;
  applicableAction?: MobileActionType | 'All';
}

export interface AuditEntryRequest {
  id_sucursal?: number;
  id_deposito?: number;
  id_articulo: string;
  stock_fisico_contado: number;
  cantidad_afectada?: number;
  tipo_accion?: MobileActionType;
  motive_id?: string;
  observation?: string;
}

export interface AuditEntryResult {
  id_articulo: string;
  stock_real: number;
  stock_fisico_contado: number | null;
  delta_stock: number;
  tipo_accion: MobileActionType;
  cantidad_afectada: number;
  audit_quantity: number;
  audit_id?: number | null;
}

export interface AuditDailyProgress {
  auditedCount: number;
  totalCount: number;
  pendingCount: number;
  percentage: number;
}

export interface ComputedAuditDelta {
  readonly stockBaseline: number;
  readonly countedQuantity: number;
  readonly deltaStock: number;
  readonly affectedQuantity: number;
  readonly actionType: MobileActionType;
  readonly requiresMotive: boolean;
}
