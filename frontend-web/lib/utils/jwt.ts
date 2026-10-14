import { UserRole } from "../types/domain";
import { ApiJwtPayload } from "../types/api";

function base64UrlDecode(str: string): string {
  let base64 = str.replace(/-/g, "+").replace(/_/g, "/");
  while (base64.length % 4) {
    base64 += "=";
  }
  if (typeof atob === "function") {
    return atob(base64);
  }
  if (typeof Buffer !== "undefined") {
    return Buffer.from(base64, "base64").toString("utf-8");
  }
  throw new Error("Unable to decode base64 string in current environment");
}

export function parseJwt(token: string): ApiJwtPayload | null {
  if (!token || typeof token !== "string") {
    return null;
  }

  const parts = token.split(".");
  if (parts.length !== 3) {
    return null;
  }

  try {
    const jsonStr = base64UrlDecode(parts[1]);
    const payload = JSON.parse(jsonStr) as ApiJwtPayload;

    if (payload.exp && typeof payload.exp === "number") {
      const nowSeconds = Math.floor(Date.now() / 1000);
      if (payload.exp < nowSeconds) {
        return null;
      }
    }

    return payload;
  } catch {
    return null;
  }
}

export function mapRoleToUserRole(roleStr?: string | null): UserRole {
  const normalized = (roleStr || "").toLowerCase().trim();
  switch (normalized) {
    case "administrador":
    case "admin":
      return UserRole.ADMINISTRADOR;
    case "supervisor":
      return UserRole.SUPERVISOR;
    case "auditor":
      return UserRole.AUDITOR;
    default:
      return UserRole.AUDITOR;
  }
}
