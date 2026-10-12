import { DecodedJwtClaims } from '../types/auth';

/**
 * Pure Base64URL decoder for JWT payloads
 * Safe across mobile runtimes without native crypto modules
 */
export function decodeJwtClaims(token: string): DecodedJwtClaims {
  try {
    const parts = token.split('.');
    if (parts.length < 2) {
      throw new Error('Invalid JWT format');
    }
    const base64Url = parts[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload) as DecodedJwtClaims;
  } catch (error) {
    throw new Error('Failed to decode JWT claims: ' + (error instanceof Error ? error.message : 'Unknown error'));
  }
}

export function extractInitials(nameOrEmail: string): string {
  if (!nameOrEmail) return 'OP';
  const clean = nameOrEmail.split('@')[0].replace(/[._-]/g, ' ').trim();
  const parts = clean.split(/\s+/).filter(Boolean);
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return clean.slice(0, 2).toUpperCase();
}

export function extractFirstName(nameOrEmail: string): string {
  if (!nameOrEmail) return 'Operario';
  const clean = nameOrEmail.split('@')[0].replace(/[._-]/g, ' ').trim();
  const parts = clean.split(/\s+/).filter(Boolean);
  if (parts.length > 0) {
    const first = parts[0];
    return first.charAt(0).toUpperCase() + first.slice(1).toLowerCase();
  }
  return 'Operario';
}
