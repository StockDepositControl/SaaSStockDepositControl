// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import CatalogPage from "./page";
import { UserRole } from "@/lib/types/domain";

const mockUseArticles = vi.fn();
const mockUseDataClient = vi.fn();

vi.mock("@/lib/hooks/useArticles", () => ({
  useArticles: (opts: unknown) => mockUseArticles(opts),
}));

function makeArticlesState(overrides: Record<string, unknown> = {}) {
  const articles = (overrides.articles as unknown[]) ?? [];
  return {
    articles,
    total: articles.length,
    page: 1,
    limit: 10,
    pages: articles.length > 0 ? 1 : 0,
    families: [],
    search: "",
    idFamilia: undefined,
    status: undefined,
    setPage: vi.fn(),
    setSearch: vi.fn(),
    setFamily: vi.fn(),
    setStatus: vi.fn(),
    isLoading: false,
    error: null,
    refetch: vi.fn(),
    ...overrides,
  };
}

function makeArticle(i: number, prefix = "ART") {
  const id = `ART-${String(i).padStart(5, "0")}`;
  return {
    id_articulo: id,
    des_articulo: `${prefix} producto ${i}`,
    cod_barras: [],
    des_familia: "Perfumería",
    stock_real: 5,
    fue_auditado: false,
  };
}

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
    mockUseArticles.mockReturnValue(makeArticlesState({
      articles: [],
      isLoading: true,
      error: null,
    }));

    render(<CatalogPage />);

    expect(
      screen.getByRole("heading", { level: 1, name: "Catálogo de Artículos" })
    ).toBeDefined();
    expect(screen.getAllByText(/Cargando artículos.../i).length).toBeGreaterThan(0);
  });

  it("renders error banner when useArticles returns an error", () => {
    mockUseArticles.mockReturnValue(makeArticlesState({
      articles: [],
      isLoading: false,
      error: "Error de red al consultar el catálogo",
    }));

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

    mockUseArticles.mockReturnValue(makeArticlesState({
      articles: mockArticles,
      isLoading: false,
      error: null,
    }));

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

    mockUseArticles.mockReturnValue(makeArticlesState({
      articles: mockArticles,
      isLoading: false,
      error: null,
    }));

    render(<CatalogPage />);

    expect(
      screen.getByText("1 artículos · Precios visibles (Vista de administrador)")
    ).toBeDefined();
    expect(screen.getByText(/Columna de costo — restringido/i)).toBeDefined();
    expect(screen.getAllByText("Ibuprofeno 600mg").length).toBeGreaterThan(0);
  });
  it("requests paginated mode and shows server total and footer range (S1)", () => {
    const articles = Array.from({ length: 10 }, (_, i) => makeArticle(i, "MED"));
    mockUseArticles.mockReturnValue(makeArticlesState({ articles, total: 500, pages: 50 }));

    render(<CatalogPage />);

    expect(mockUseArticles).toHaveBeenCalledWith(expect.objectContaining({ paginated: true }));
    expect(screen.getByText("500 artículos · Stock y estado de auditoría")).toBeDefined();
    expect(screen.getByText("1-10 de 500 ítems")).toBeDefined();
    expect(screen.getByRole("button", { name: "50" })).toBeDefined();
  });

  it("pagination buttons invoke setPage", () => {
    const state = makeArticlesState({ articles: [makeArticle(0)], total: 500, pages: 50 });
    mockUseArticles.mockReturnValue(state);

    render(<CatalogPage />);
    fireEvent.click(screen.getByLabelText("Página siguiente"));
    fireEvent.click(screen.getByLabelText("Última página"));

    expect(state.setPage).toHaveBeenCalledWith(2);
    expect(state.setPage).toHaveBeenCalledWith(50);
  });

  it("renders ART articles returned for a later page (S2)", () => {
    const articles = Array.from({ length: 10 }, (_, i) => makeArticle(250 + i, "ART"));
    mockUseArticles.mockReturnValue(
      makeArticlesState({ articles, total: 500, pages: 50, page: 26 })
    );

    render(<CatalogPage />);

    expect(screen.getAllByText("ART producto 250").length).toBeGreaterThan(0);
    expect(screen.getByText("251-260 de 500 ítems")).toBeDefined();
  });

  it("search input invokes setSearch (S3)", () => {
    const state = makeArticlesState();
    mockUseArticles.mockReturnValue(state);

    render(<CatalogPage />);
    fireEvent.change(screen.getByPlaceholderText(/Buscar código de barras/i), {
      target: { value: "7791234567890" },
    });

    expect(state.setSearch).toHaveBeenCalledWith("7791234567890");
  });

  it("family dropdown lists server families by id and invokes setFamily (S4)", () => {
    const state = makeArticlesState({
      families: [
        { id_familia: "01", des_familia: "Medicamentos" },
        { id_familia: "02", des_familia: "Perfumería" },
      ],
    });
    mockUseArticles.mockReturnValue(state);

    render(<CatalogPage />);
    const option = screen.getByRole("option", { name: "Perfumería" }) as HTMLOptionElement;
    expect(option.value).toBe("02");

    fireEvent.change(option.parentElement as HTMLSelectElement, { target: { value: "02" } });
    expect(state.setFamily).toHaveBeenCalledWith("02");

    fireEvent.change(option.parentElement as HTMLSelectElement, { target: { value: "" } });
    expect(state.setFamily).toHaveBeenCalledWith(undefined);
  });

  it("status dropdown maps to setStatus", () => {
    const state = makeArticlesState();
    mockUseArticles.mockReturnValue(state);

    render(<CatalogPage />);
    const select = screen.getByRole("option", { name: "Auditado" }).parentElement as HTMLSelectElement;
    fireEvent.change(select, { target: { value: "audited" } });
    fireEvent.change(select, { target: { value: "pending" } });
    fireEvent.change(select, { target: { value: "all" } });

    expect(state.setStatus).toHaveBeenNthCalledWith(1, true);
    expect(state.setStatus).toHaveBeenNthCalledWith(2, false);
    expect(state.setStatus).toHaveBeenNthCalledWith(3, undefined);
  });

  it("shows empty footer with disabled navigation when no results", () => {
    mockUseArticles.mockReturnValue(makeArticlesState({ articles: [], total: 0, pages: 0 }));

    render(<CatalogPage />);

    expect(screen.getByText("0-0 de 0 ítems")).toBeDefined();
    expect((screen.getByLabelText("Página siguiente") as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByLabelText("Página anterior") as HTMLButtonElement).disabled).toBe(true);
  });

  it("hides cost column for AUDITOR and shows it for ADMINISTRADOR (S5)", () => {
    mockUseArticles.mockReturnValue(makeArticlesState({ articles: [makeArticle(1)] }));
    const { unmount } = render(<CatalogPage />);
    expect(screen.queryByText("COSTO")).toBeNull();
    unmount();

    mockUseDataClient.mockReturnValue({
      currentUser: { id: "USR-ADMIN", name: "Admin Demo", role: UserRole.ADMINISTRADOR },
      currentRole: UserRole.ADMINISTRADOR,
      users: [],
      client: {},
      logout: vi.fn(),
    });
    mockUseArticles.mockReturnValue(
      makeArticlesState({ articles: [{ ...makeArticle(1), pcio_com_siva: 250 }] })
    );
    render(<CatalogPage />);
    expect(screen.getByText("COSTO")).toBeDefined();
  });
});
