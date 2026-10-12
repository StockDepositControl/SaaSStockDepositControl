import { AuditMotive } from '../types/audit';

export const MOTIVES_CATALOG: AuditMotive[] = [
  { id: 'VENCIDO_BAJA', label: 'Vencido y dado de baja', applicableAction: 'Baja' },
  { id: 'MERCADERIA_DANADA', label: 'Mercadería dañada / rotura', applicableAction: 'Baja' },
  { id: 'PERDIDA_DESCONOCIDA', label: 'Faltante / pérdida desconocida', applicableAction: 'Baja' },
  { id: 'SOBRANTE_RECEPCION', label: 'Sobrante no ingresado en recepción', applicableAction: 'Alta' },
  { id: 'ERROR_SISTEMA', label: 'Error de carga en sistema', applicableAction: 'All' },
  { id: 'CONTEO_REGULAR', label: 'Conteo regular sin diferencias', applicableAction: 'Sin Acción' },
];

export const STORAGE_KEYS = {
  JWT_TOKEN: 'audit_global.jwt_token',
  SESSION_PREFIX: 'audit_global:session',
} as const;

export const API_CONFIG = {
  BASE_URL: process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000',
  TIMEOUT_MS: 15000,
  USE_MOCK: process.env.EXPO_PUBLIC_USE_MOCK === 'true',
} as const;
