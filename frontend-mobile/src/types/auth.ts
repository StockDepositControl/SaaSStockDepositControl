/**
 * Authentication & Tenant Context Types
 */

export type MobileAllowedRole = 'auditor' | 'supervisor';

export interface DecodedJwtClaims {
  sub: string;
  role: string;
  tenant_id: number | string;
  branch_id?: number;
  user_id?: number;
  id_usuario?: number;
  exp: number;
}

export interface ActiveTenantSession {
  token: string;
  email: string;
  displayName: string;
  initials: string;
  role: MobileAllowedRole;
  tenantId: string;
  branchId: number;
  depositId: number;
  userId: number;
  expiresAtMs: number;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthTokenResponse {
  access_token: string;
  token_type: string;
}
