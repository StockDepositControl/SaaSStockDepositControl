// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import CatalogPage from "./page";
import { UserRole } from "@/lib/types/domain";

const mockUseArticles = vi.fn();
const mockUseDataClient = vi.fn();

vi.mock("@/lib/hooks/useArticles", () => ({
  useArticles: () => mockUseArticles(),
}));

vi.mock("@/lib/hooks/useDataClient", () => ({
  useDataClient: () => mockUseDataClient(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  usePathname: () => "/catalog",
}));

describe("CatalogPage integration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseDataClient.mockReturnValue({
      currentUser: { id: "USR-001", name: "Auditor Demo", role: UserRole.AUDITOR },
      currentRole: UserRole.AUDITOR,
      users: [],
      client: {},
      logout: vi.fn(),
    });
  });

  it("renders loading state in DataTable while fetching articles", () => {
    mockUseArticles.mockReturnValue({
      articles: [],
      isLoading: true,
      error: null,
      refetch: vi.fn(),
    });

    render(<CatalogPage />);

    expect(
      screen.getByRole("heading", { level: 1, name: "Catálogo de Artículos" })
    ).toBeDefined();
    expect(screen.getAllByText(/Cargando artículos.../i).length).toBeGreaterThan(0);
  });

  it("renders error banner when useArticles returns an error", () => {
    mockUseArticles.mockReturnValue({
      articles: [],
      isLoading: false,
      error: "Error de red al consultar el catálogo",
      refetch: vi.fn(),
    });

    render(<CatalogPage />);

    const alert = screen.getByRole("alert");
    expect(alert).toBeDefined();
    expect(alert.textContent).toContain("Error de red al consultar el catálogo");
  });

  it("renders articles list and auditor subtitle for AUDITOR role", () => {
    const mockArticles = [
      {
        id_articulo: "ART-001",
        des_articulo: "Amoxicilina 500mg",
        cod_barras: ["7790001"],
        des_marca: "Roemmers",
        des_familia: "Antibióticos",
        stock_real: 42,
        fue_auditado: false,
      },
    ];

    mockUseArticles.mockReturnValue({
      articles: mockArticles,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<CatalogPage />);

    expect(screen.getByText("1 artículos · Stock y estado de auditoría")).toBeDefined();
    expect(screen.getAllByText("Amoxicilina 500mg").length).toBeGreaterThan(0);
    expect(screen.queryByText(/Columna de costo — restringido/i)).toBeNull();
  });

  it("displays admin restriction banner and admin subtitle for ADMINISTRADOR role", () => {
    mockUseDataClient.mockReturnValue({
      currentUser: { id: "USR-ADMIN", name: "Admin Demo", role: UserRole.ADMINISTRADOR },
      currentRole: UserRole.ADMINISTRADOR,
      users: [],
      client: {},
      logout: vi.fn(),
    });

    const mockArticles = [
      {
        id_articulo: "ART-002",
        des_articulo: "Ibuprofeno 600mg",
        cod_barras: ["7790002"],
        des_marca: "Bayer",
        des_familia: "Analgésicos",
        stock_real: 15,
        fue_auditado: true,
        pcio_com_siva: 250,
      },
    ];

    mockUseArticles.mockReturnValue({
      articles: mockArticles,
      isLoading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<CatalogPage />);

    expect(
      screen.getByText("1 artículos · Precios visibles (Vista de administrador)")
    ).toBeDefined();
    expect(screen.getByText(/Columna de costo — restringido/i)).toBeDefined();
    expect(screen.getAllByText("Ibuprofeno 600mg").length).toBeGreaterThan(0);
  });
});
