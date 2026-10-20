// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, waitFor, act } from "@testing-library/react";
import React from "react";

const getArticulos = vi.fn();
const getCurrentUser = vi.fn();
const getKPIs = vi.fn();
const getAuditLog = vi.fn();
const mockLogin = vi.fn();
const mockLogout = vi.fn();

vi.mock("../adapters/ApiDataClient", () => ({
  ApiDataClient: vi.fn().mockImplementation(() => ({
    getArticulos,
    getCurrentUser,
    getKPIs,
    getAuditLog,
    login: mockLogin,
    logout: mockLogout,
    setRole: vi.fn(),
    switchUser: vi.fn(),
  })),
}));

import { ApiDataProvider } from "./ApiDataContext";
import { useDataContext } from "./DataContext";
import { UserRole } from "../types/domain";

function Probe({ onValue }: { onValue: (v: ReturnType<typeof useDataContext>) => void }) {
  const ctx = useDataContext();
  onValue(ctx);
  return null;
}

describe("ApiDataProvider zero-prefetch", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    getKPIs.mockResolvedValue({
      totalArticulos: 10,
      auditados: 2,
      pendientes: 8,
      porcentajeAvance: 20,
      discrepanciasAlta: 0,
      discrepanciasBaja: 0,
      sinAccion: 0,
    });
    getAuditLog.mockResolvedValue([]);
  });

  it("makes no domain requests when there is no stored session", async () => {
    getCurrentUser.mockResolvedValue(null);
    let latest: ReturnType<typeof useDataContext> | undefined;

    render(
      <ApiDataProvider>
        <Probe onValue={(v) => (latest = v)} />
      </ApiDataProvider>
    );

    await waitFor(() => expect(latest?.isLoading).toBe(false));
    expect(getArticulos).not.toHaveBeenCalled();
    expect(getKPIs).not.toHaveBeenCalled();
    expect(getAuditLog).not.toHaveBeenCalled();
    expect("articles" in (latest as object)).toBe(false);
    expect("kpis" in (latest as object)).toBe(false);
    expect("auditLogs" in (latest as object)).toBe(false);
  });

  it("does not load articles, kpis, or audit logs even with an authenticated session", async () => {
    getCurrentUser.mockResolvedValue({ id: "1", role: UserRole.AUDITOR });
    let latest: ReturnType<typeof useDataContext> | undefined;

    render(
      <ApiDataProvider>
        <Probe onValue={(v) => (latest = v)} />
      </ApiDataProvider>
    );

    await waitFor(() => expect(latest?.isLoading).toBe(false));
    expect(getArticulos).not.toHaveBeenCalled();
    expect(getKPIs).not.toHaveBeenCalled();
    expect(getAuditLog).not.toHaveBeenCalled();
    expect("articles" in (latest as object)).toBe(false);
    expect("kpis" in (latest as object)).toBe(false);
    expect("auditLogs" in (latest as object)).toBe(false);
  });

  it("executes login without fetching articles, kpis, or audit logs eagerly", async () => {
    getCurrentUser.mockResolvedValue(null);
    mockLogin.mockResolvedValue({
      id: "USR-ADMIN",
      email: "admin@example.com",
      role: UserRole.ADMINISTRADOR,
    });

    let latest: ReturnType<typeof useDataContext> | undefined;

    render(
      <ApiDataProvider>
        <Probe onValue={(v) => (latest = v)} />
      </ApiDataProvider>
    );

    await waitFor(() => expect(latest?.isLoading).toBe(false));
    expect(getArticulos).not.toHaveBeenCalled();
    expect(getKPIs).not.toHaveBeenCalled();
    expect(getAuditLog).not.toHaveBeenCalled();

    await act(async () => {
      await latest?.login("admin@example.com", "password123");
    });

    expect(mockLogin).toHaveBeenCalledWith("admin@example.com", "password123");
    expect(getKPIs).not.toHaveBeenCalled();
    expect(getAuditLog).not.toHaveBeenCalled();
    expect(getArticulos).not.toHaveBeenCalled();
    expect("articles" in (latest as object)).toBe(false);
    expect("kpis" in (latest as object)).toBe(false);
    expect("auditLogs" in (latest as object)).toBe(false);
  });

  it("clears user and session state on logout without triggering queries", async () => {
    getCurrentUser.mockResolvedValue({ id: "USR-1", role: UserRole.AUDITOR });
    let latest: ReturnType<typeof useDataContext> | undefined;

    render(
      <ApiDataProvider>
        <Probe onValue={(v) => (latest = v)} />
      </ApiDataProvider>
    );

    await waitFor(() => expect(latest?.currentUser?.id).toBe("USR-1"));

    act(() => {
      latest?.logout();
    });

    expect(mockLogout).toHaveBeenCalledTimes(1);
    expect(latest?.currentUser).toBeNull();
    expect(latest?.currentRole).toBeNull();
    expect(getArticulos).not.toHaveBeenCalled();
    expect(getKPIs).not.toHaveBeenCalled();
    expect(getAuditLog).not.toHaveBeenCalled();
  });
});
