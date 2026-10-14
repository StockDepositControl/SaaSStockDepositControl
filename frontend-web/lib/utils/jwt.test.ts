import { describe, it, expect } from "vitest";
import { parseJwt, mapRoleToUserRole } from "./jwt";
import { UserRole } from "../types/domain";

describe("jwt utils", () => {
  it("should correctly decode valid JWT payload", () => {
    // Header: {"alg":"HS256","typ":"JWT"} -> eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
    // Payload: {"sub":"user_0@example.com","role":"administrador","tenant_id":1,"branch_id":1,"user_id":10,"exp":253402300799}
    const token =
      "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9." +
      "eyJzdWIiOiJ1c2VyXzBAZXhhbXBsZS5jb20iLCJyb2xlIjoiYWRtaW5pc3RyYWRvciIsInRlbmFudF9pZCI6MSwiYnJhbmNoX2lkIjoxLCJ1c2VyX2lkIjoxMCwiZXhwIjoyNTM0MDIzMDA3OTl9." +
      "signature";

    const payload = parseJwt(token);
    expect(payload).not.toBeNull();
    expect(payload?.sub).toBe("user_0@example.com");
    expect(payload?.role).toBe("administrador");
    expect(payload?.tenant_id).toBe(1);
    expect(payload?.branch_id).toBe(1);
    expect(payload?.user_id).toBe(10);
  });

  it("should return null for expired token", () => {
    // exp is in the past: 1000000000 (year 2001)
    const token =
      "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9." +
      "eyJzdWIiOiJ1c2VyXzBAZXhhbXBsZS5jb20iLCJyb2xlIjoiYWRtaW5pc3RyYWRvciIsImV4cCI6MTAwMDAwMDAwMH0." +
      "signature";

    const payload = parseJwt(token);
    expect(payload).toBeNull();
  });

  it("should return null for malformed tokens", () => {
    expect(parseJwt("")).toBeNull();
    expect(parseJwt("not-a-token")).toBeNull();
    expect(parseJwt("one.two")).toBeNull();
  });

  it("should map backend roles correctly to UserRole enum", () => {
    expect(mapRoleToUserRole("administrador")).toBe(UserRole.ADMINISTRADOR);
    expect(mapRoleToUserRole("ADMINISTRADOR")).toBe(UserRole.ADMINISTRADOR);
    expect(mapRoleToUserRole("admin")).toBe(UserRole.ADMINISTRADOR);
    expect(mapRoleToUserRole("supervisor")).toBe(UserRole.SUPERVISOR);
    expect(mapRoleToUserRole("auditor")).toBe(UserRole.AUDITOR);
    expect(mapRoleToUserRole("unknown")).toBe(UserRole.AUDITOR);
  });
});
