export interface ValidationResult {
  isValid: boolean;
  errorMessage?: string;
}

export class AuditValidator {
  static validateCount(rawCount: string): ValidationResult {
    if (!rawCount || rawCount.trim() === '') {
      return { isValid: false, errorMessage: 'Ingresá una cantidad contada.' };
    }
    const num = Number(rawCount.trim());
    if (isNaN(num) || num < 0 || !Number.isInteger(num)) {
      return { isValid: false, errorMessage: 'La cantidad debe ser un número entero mayor o igual a 0.' };
    }
    return { isValid: true };
  }

  static validateForm(params: {
    rawCount: string;
    requiresMotive: boolean;
    motiveId?: string | null;
    observation?: string | null;
  }): ValidationResult {
    const countCheck = this.validateCount(params.rawCount);
    if (!countCheck.isValid) {
      return countCheck;
    }

    if (params.requiresMotive && (!params.motiveId || params.motiveId.trim() === '')) {
      return { isValid: false, errorMessage: 'El motivo es obligatorio cuando existe una diferencia de stock.' };
    }

    if (params.observation && params.observation.length > 255) {
      return { isValid: false, errorMessage: 'La observación no puede superar los 255 caracteres.' };
    }

    return { isValid: true };
  }
}
