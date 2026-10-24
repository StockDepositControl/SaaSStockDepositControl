// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import AuditPage from "./page";
import { UserRole } from "@/lib/types/domain";

// Mock useDataClient
const mockArticle = {
  id_articulo: "ART-001",
  des_articulo: "Ibuprofeno 400mg",
  cod_barras: ["7791234567890"],
  des_marca: "Bayer",
  des_familia: "Analgésicos",
  stock_real: 15,
  fue_auditado: false,
};

const mockGetArticuloByBarcode = vi.fn().mockResolvedValue(mockArticle);
const mockSearchArticulos = vi.fn().mockResolvedValue([mockArticle]);
const mockRegisterAudit = vi.fn().mockResolvedValue({
  success: true,
  nuevo_stock: 15,
  delta_stock: 0,
});

let mockRole: UserRole = UserRole.AUDITOR;
const mockPush = vi.fn();

vi.mock("@/lib/hooks/useDataClient", () => ({
  useDataClient: () => ({
    currentUser: { id: "USR-001", name: "Auditor Demo", role: mockRole },
    currentRole: mockRole,
    client: {
      getArticuloByBarcode: mockGetArticuloByBarcode,
      searchArticulos: mockSearchArticulos,
      registerAudit: mockRegisterAudit,
    },
    logout: vi.fn(),
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: mockPush }),
  usePathname: () => "/audit",
}));

describe("AuditPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRole = UserRole.AUDITOR;
  });

  it("redirects administrators to the dashboard and hides the audit form", () => {
    mockRole = UserRole.ADMINISTRADOR;
    render(<AuditPage />);

    expect(mockPush).toHaveBeenCalledWith("/dashboard");
    expect(screen.queryByText("Auditoría de Stock")).toBeNull();
  });

  it("renders search bar and camera scanner button", () => {
    render(<AuditPage />);
    expect(screen.getByPlaceholderText(/Buscar por código de barras/i)).toBeDefined();
    expect(screen.getByLabelText("Escanear con cámara")).toBeDefined();
  });

  it("opens scanner modal when camera button is clicked", () => {
    render(<AuditPage />);
    const cameraButton = screen.getByLabelText("Escanear con cámara");
    fireEvent.click(cameraButton);
    expect(screen.getByRole("dialog")).toBeDefined();
    expect(screen.getByText("Escáner de Código de Barras")).toBeDefined();
  });

  it("selects article when exact barcode match is submitted", async () => {
    render(<AuditPage />);
    const input = screen.getByPlaceholderText(/Buscar por código de barras/i);
    fireEvent.change(input, { target: { value: "7791234567890" } });

    const searchButton = screen.getByRole("button", { name: "Buscar" });
    fireEvent.click(searchButton);

    await waitFor(() => {
      expect(screen.getByText("Ibuprofeno 400mg")).toBeDefined();
      expect(screen.getByText("15")).toBeDefined();
    });
  });

  it("allows incrementing and decrementing count using stepper", async () => {
    render(<AuditPage />);
    const input = screen.getByPlaceholderText(/Buscar por código de barras/i);
    fireEvent.change(input, { target: { value: "7791234567890" } });
    fireEvent.click(screen.getByRole("button", { name: "Buscar" }));

    await waitFor(() => {
      expect(screen.getByLabelText("Aumentar cantidad")).toBeDefined();
    });

    const plusBtn = screen.getByLabelText("Aumentar cantidad");
    fireEvent.click(plusBtn);

    const countInput = screen.getByPlaceholderText("0") as HTMLInputElement;
    expect(countInput.value).toBe("1");

    fireEvent.click(plusBtn);
    expect(countInput.value).toBe("2");

    const minusBtn = screen.getByLabelText("Disminuir cantidad");
    fireEvent.click(minusBtn);
    expect(countInput.value).toBe("1");
  });
});
