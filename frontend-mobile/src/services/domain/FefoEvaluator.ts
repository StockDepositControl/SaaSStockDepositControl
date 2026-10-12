export type FefoAlertSeverity = 'EXPIRED' | 'PROXIMO' | 'SAFE' | 'NONE';

export interface FefoEvaluation {
  readonly severity: FefoAlertSeverity;
  readonly formattedDate: string | null;
  readonly badgeLabel: 'VENCIDO' | 'PRÓXIMO' | null;
  readonly daysUntilExpiry: number | null;
}

export class FefoEvaluator {
  static evaluate(
    rawExpirationDate: string | null | undefined,
    referenceDate: Date = new Date(),
    proximoThresholdDays: number = 90
  ): FefoEvaluation {
    if (!rawExpirationDate) {
      return { severity: 'NONE', formattedDate: null, badgeLabel: null, daysUntilExpiry: null };
    }

    const parsed = FefoEvaluator.parseDate(rawExpirationDate);
    if (!parsed) {
      return { severity: 'NONE', formattedDate: null, badgeLabel: null, daysUntilExpiry: null };
    }

    const startOfToday = new Date(
      referenceDate.getFullYear(),
      referenceDate.getMonth(),
      referenceDate.getDate()
    );
    const diffMs = parsed.getTime() - startOfToday.getTime();
    const daysUntilExpiry = Math.ceil(diffMs / (1000 * 60 * 60 * 24));

    const dd = String(parsed.getDate()).padStart(2, '0');
    const mm = String(parsed.getMonth() + 1).padStart(2, '0');
    const yyyy = parsed.getFullYear();
    const formattedDate = `${dd}/${mm}/${yyyy}`;

    if (daysUntilExpiry < 0) {
      return {
        severity: 'EXPIRED',
        formattedDate,
        badgeLabel: 'VENCIDO',
        daysUntilExpiry,
      };
    }

    if (daysUntilExpiry <= proximoThresholdDays) {
      return {
        severity: 'PROXIMO',
        formattedDate,
        badgeLabel: 'PRÓXIMO',
        daysUntilExpiry,
      };
    }

    return {
      severity: 'SAFE',
      formattedDate,
      badgeLabel: null,
      daysUntilExpiry,
    };
  }

  private static parseDate(input: string): Date | null {
    const clean = input.trim();
    // Match ISO YYYY-MM-DD
    const isoMatch = /^(\d{4})-(\d{2})-(\d{2})/.exec(clean);
    if (isoMatch) {
      return new Date(Number(isoMatch[1]), Number(isoMatch[2]) - 1, Number(isoMatch[3]));
    }
    // Match DD/MM/YYYY
    const dmyMatch = /^(\d{2})\/(\d{2})\/(\d{4})/.exec(clean);
    if (dmyMatch) {
      return new Date(Number(dmyMatch[3]), Number(dmyMatch[2]) - 1, Number(dmyMatch[1]));
    }
    return null;
  }
}
