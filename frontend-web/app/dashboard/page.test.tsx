// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import DashboardPage from "./page";
import { UserRole, DashboardKPIsBase, DashboardKPIsAdmin, AuditResult, TipoAccion } from "@/lib/types/domain";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/dashboard",
}));

// Mock domain hooks
const mockUseDataClient = vi.fn();
const mockUseArticles = vi.fn();
const mockUseKPIs = vi.fn();
const mockUseAuditLogs = vi.fn();

vi.mock("@/lib/hooks/useDataClient", () => ({
  useDataClient: () => mockUseDataClient(),
}));

vi.mock("@/lib/hooks/useArticles", () => ({
  useArticles: () => mockUseArticles(),
}));

vi.mock("@/lib/hooks/useKPIs", () => ({
  useKPIs: () => mockUseKPIs(),
}));

vi.mock("@/lib/hooks/useAuditLogs", () => ({
  useAuditLogs: () => mockUseAuditLogs(),
}));

const baseKPIsFixture: DashboardKPIsBase = {
  totalArticulos: 50,
  auditados: 25,
  pendientes: 25,
  porcentajeAvance: 50,
  discrepanciasAlta: 2,
  discrepanciasBaja: 3,
  sinAccion: 20,
  outOfStockCount: 0,
};

describe("DashboardPage (Integration with decoupled hooks)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("does not execute useArticles on mount (no catalog overfetch)", () => {
    mockUseDataClient.mockReturnValue({
      currentUser: { id: "USR-001", name: "Juan Auditor", role: UserRole.AUDITOR },
      currentRole: UserRole.AUDITOR,
      logout: vi.fn(),
    });
    mockUseKPIs.mockReturnValue({
      kpis: { ...baseKPIsFixture },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    mockUseAuditLogs.mockReturnValue({
      auditLogs: [],
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<DashboardPage />);

    expect(mockUseArticles).not.toHaveBeenCalled();
  });

  it("renders auditor view with decoupled KPI and audit log metrics", () => {
    mockUseDataClient.mockReturnValue({
      currentUser: { id: "USR-001", name: "Juan Auditor", role: UserRole.AUDITOR },
      currentRole: UserRole.AUDITOR,
      logout: vi.fn(),
    });

    const auditorKPIs: DashboardKPIsBase = { ...baseKPIsFixture };

    const mockLogs: AuditResult[] = [
      {
        client_uuid: "AUD-1",
        id_articulo: "ART-1",
        des_articulo: "Amoxicilina 500mg",
        stock_fisico_contado: 8,
        stock_real: 10,
        delta_stock: -2,
        tipo_accion: TipoAccion.BAJA,
        cantidad_afectada: 2,
        audit_quantity: 8,
        monto_valorizado: 500,
        applied_vat_rate: 21,
        scan_timestamp: "2026-10-20T10:00:00Z",
      },
      {
        client_uuid: "AUD-2",
        id_articulo: "ART-2",
        des_articulo: "Ibuprofeno 400mg",
        stock_fisico_contado: 15,
        stock_real: 20,
        delta_stock: -5,
        tipo_accion: TipoAccion.BAJA,
        cantidad_afectada: 5,
        audit_quantity: 15,
        monto_valorizado: 1200,
        applied_vat_rate: 21,
        scan_timestamp: "2026-10-20T10:05:00Z",
      },
    ];

    mockUseKPIs.mockReturnValue({
      kpis: auditorKPIs,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    mockUseAuditLogs.mockReturnValue({
      auditLogs: mockLogs,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<DashboardPage />);

    // Header greeting
    expect(screen.getByText(/Hola, Juan/i)).toBeDefined();

    // Auditor progress card shows values from useKPIs
    expect(screen.getByText("Progreso de Auditoría")).toBeDefined();
    expect(screen.getByText("25")).toBeDefined();
    expect(screen.getByText(/\/ 50/i)).toBeDefined();
    expect(screen.getByText(/50% del catálogo de hoy/i)).toBeDefined();

    // Shortage card calculates sum of deficits from useAuditLogs: |-2| + |-5| = 7
    expect(screen.getByText("-7 unidades")).toBeDefined();
  });

  it("renders administrator view with financial and valorized KPIs", () => {
    mockUseDataClient.mockReturnValue({
      currentUser: { id: "USR-ADMIN", name: "Valeria Admin", role: UserRole.ADMINISTRADOR },
      currentRole: UserRole.ADMINISTRADOR,
      logout: vi.fn(),
    });

    const adminKPIs: DashboardKPIsAdmin = {
      totalArticulos: 100,
      auditados: 80,
      pendientes: 20,
      porcentajeAvance: 80,
      discrepanciasAlta: 4,
      discrepanciasBaja: 6,
      sinAccion: 70,
      outOfStockCount: 12,
      montoValorizadoTotal: 154200,
      montoValorizadoAlta: 12400,
      montoValorizadoBaja: 8900,
    };

    mockUseKPIs.mockReturnValue({
      kpis: adminKPIs,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    mockUseAuditLogs.mockReturnValue({
      auditLogs: [],
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<DashboardPage />);

    expect(screen.getByText(/Hola, Valeria/i)).toBeDefined();
    expect(screen.getByText("PROGRESO DE AUDITORÍA")).toBeDefined();
    expect(screen.getByText("80")).toBeDefined();
    expect(screen.getByText(/\/ 100/i)).toBeDefined();

    // Financial KPI cards rendered for Admin
    expect(screen.getByText("FALTANTES REGISTRADOS HOY")).toBeDefined();
    expect(screen.getByText(/\$ 8,900\.00/)).toBeDefined();
    expect(screen.getByText("ALERTAS CRÍTICAS DE ALMACÉN")).toBeDefined();
    expect(screen.getByText("12")).toBeDefined();
  });

  it("handles loading and empty hook states gracefully without throwing", () => {
    mockUseDataClient.mockReturnValue({
      currentUser: { id: "USR-001", name: "Auditor Demo", role: UserRole.AUDITOR },
      currentRole: UserRole.AUDITOR,
      logout: vi.fn(),
    });

    mockUseKPIs.mockReturnValue({
      kpis: {
        totalArticulos: 0,
        auditados: 0,
        pendientes: 0,
        porcentajeAvance: 0,
        discrepanciasAlta: 0,
        discrepanciasBaja: 0,
        sinAccion: 0,
        outOfStockCount: 0,
      },
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    });

    mockUseAuditLogs.mockReturnValue({
      auditLogs: [],
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    });

    const { container } = render(<DashboardPage />);
    expect(container).toBeDefined();
    expect(screen.getByText("Progreso de Auditoría")).toBeDefined();
  });

  it("renders administrator view in loading state without throwing", () => {
    mockUseDataClient.mockReturnValue({
      currentUser: { id: "USR-ADMIN", name: "Valeria Admin", role: UserRole.ADMINISTRADOR },
      currentRole: UserRole.ADMINISTRADOR,
      logout: vi.fn(),
    });

    mockUseKPIs.mockReturnValue({
      kpis: {
        totalArticulos: 0,
        auditados: 0,
        pendientes: 0,
        porcentajeAvance: 0,
        discrepanciasAlta: 0,
        discrepanciasBaja: 0,
        sinAccion: 0,
        outOfStockCount: 0,
      },
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    });

    mockUseAuditLogs.mockReturnValue({
      auditLogs: [],
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    });

    const { container } = render(<DashboardPage />);
    expect(container).toBeDefined();
    expect(screen.getByText("FALTANTES REGISTRADOS HOY")).toBeDefined();
    expect(screen.getByText("$ ---")).toBeDefined();
  });

  it.each([
    [UserRole.ADMINISTRADOR, false],
    [UserRole.SUPERVISOR, true],
    [UserRole.AUDITOR, true],
  ])("quick access audit card for %s visible: %s", (role, visible) => {
    mockUseDataClient.mockReturnValue({
      currentUser: { id: "USR-X", name: "Test User", role },
      currentRole: role,
      logout: vi.fn(),
    });
    mockUseKPIs.mockReturnValue({
      kpis: { ...baseKPIsFixture },
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
    mockUseAuditLogs.mockReturnValue({ auditLogs: [], isLoading: false, error: null, refetch: vi.fn() });

    const { container } = render(<DashboardPage />);

    const auditLinks = container.querySelectorAll('main a[href="/audit"]');
    expect(auditLinks.length > 0).toBe(visible);
  });
});
