import { MobileActionType, ComputedAuditDelta } from '../../types/audit';

export class DeltaCalculator {
  static compute(stockBaseline: number, countedQuantity: number): ComputedAuditDelta {
    const safeBaseline = Math.max(0, Math.trunc(stockBaseline || 0));
    const safeCounted = Math.max(0, Math.trunc(countedQuantity || 0));
    const deltaStock = safeCounted - safeBaseline;
    const affectedQuantity = Math.abs(deltaStock);

    let actionType: MobileActionType = 'Sin Acción';
    if (deltaStock > 0) {
      actionType = 'Alta';
    } else if (deltaStock < 0) {
      actionType = 'Baja';
    }

    return {
      stockBaseline: safeBaseline,
      countedQuantity: safeCounted,
      deltaStock,
      affectedQuantity,
      actionType,
      requiresMotive: deltaStock !== 0,
    };
  }
}
