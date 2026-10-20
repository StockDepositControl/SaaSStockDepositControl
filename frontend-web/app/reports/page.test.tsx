// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import React from "react";
import ReportesPage from "./page";
import { UserRole, AuditResult, TipoAccion } from "@/lib/types/domain";

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/reports",
}));

// Mock httpClient to prevent real backend network calls
vi.mock("@/lib/adapters/httpClient", () => ({
  httpClient: {
    get: vi.fn().mockResolvedValue({
      start_date: "2026-10-13",
      end_date: "2026-10-20",
      total_records: 0,
    }),
  },
}));

// Mock domain hooks
const mockUseDataClient = vi.fn();
const mockUseArticles = vi.fn();
const mockUseAuditLogs = vi.fn();

vi.mock("@/lib/hooks/useDataClient", () => ({
  useDataClient: () => mockUseDataClient(),
}));

vi.mock("@/lib/hooks/useArticles", () => ({
  useArticles: () => mockUseArticles(),
}));

vi.mock("@/lib/hooks/useAuditLogs", () => ({
  useAuditLogs: () => mockUseAuditLogs(),
}));

const mockAuditLogsList: AuditResult[] = [
  {
    client_uuid: "AUD-101",
    id_articulo: "ART-101",
    des_articulo: "Paracetamol 500mg",
    stock_fisico_contado: 10,
    stock_real: 12,
    delta_stock: -2,
    tipo_accion: TipoAccion.BAJA,
    cantidad_afectada: 2,
    audit_quantity: 10,
    monto_valorizado: 600,
    applied_vat_rate: 21,
    scan_timestamp: "2026-10-20T10:00:00Z",
  },
];

describe("ReportesPage (Integration with decoupled hooks)", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    mockUseArticles.mockReturnValue({
      articles: [],
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    mockUseAuditLogs.mockReturnValue({
      auditLogs: mockAuditLogsList,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });
  });

  it("shows restricted access message when current role is not ADMINISTRADOR", () => {
    mockUseDataClient.mockReturnValue({
      currentUser: { id: "USR-002", name: "Auditor Demo", role: UserRole.AUDITOR },
      currentRole: UserRole.AUDITOR,
      logout: vi.fn(),
    });

    render(<ReportesPage />);

    expect(screen.getByText("Acceso Restringido")).toBeDefined();
    expect(screen.getByText(/no tiene autorización para acceder a reportes financieros/i)).toBeDefined();
  });

  it("renders report dashboard and consumes audit logs for audit history tab when ADMINISTRADOR", async () => {
    mockUseDataClient.mockReturnValue({
      currentUser: { id: "USR-ADMIN", name: "Admin Demo", role: UserRole.ADMINISTRADOR },
      currentRole: UserRole.ADMINISTRADOR,
      logout: vi.fn(),
    });

    render(<ReportesPage />);

    expect(screen.getByText("Reportes y Métricas Financieras")).toBeDefined();

    // Click on "Historial de Auditoría" tab
    const historyTabBtn = screen.getByText("Historial de Auditoría");
    fireEvent.click(historyTabBtn);

    // Wait for the tab content to render with mockAuditLogsList
    await waitFor(() => {
      expect(screen.getByText("Paracetamol 500mg")).toBeDefined();
    });
  });

  it("handles empty audit logs gracefully on history tab", async () => {
    mockUseDataClient.mockReturnValue({
      currentUser: { id: "USR-ADMIN", name: "Admin Demo", role: UserRole.ADMINISTRADOR },
      currentRole: UserRole.ADMINISTRADOR,
      logout: vi.fn(),
    });

    mockUseAuditLogs.mockReturnValue({
      auditLogs: [],
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<ReportesPage />);

    const historyTabBtn = screen.getByText("Historial de Auditoría");
    fireEvent.click(historyTabBtn);

    await waitFor(() => {
      // Empty state text in AuditHistoryTab
      expect(screen.getByText("Sin auditorías registradas")).toBeDefined();
    });
  });
});
