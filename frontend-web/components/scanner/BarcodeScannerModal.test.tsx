// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { BarcodeScannerModal } from "./BarcodeScannerModal";

// Mock child hooks to isolate modal component logic
const mockRequestPermission = vi.fn();
const mockResetPermission = vi.fn();
let mockPermissionStatus = "idle";
let mockErrorMessage: string | null = null;

vi.mock("@/lib/hooks/useCameraPermissions", () => ({
  useCameraPermissions: () => ({
    status: mockPermissionStatus,
    errorMessage: mockErrorMessage,
    requestPermission: mockRequestPermission,
    resetPermission: mockResetPermission,
  }),
}));

const mockStopScanning = vi.fn().mockResolvedValue(undefined);
vi.mock("@/lib/hooks/useBarcodeScanner", () => ({
  useBarcodeScanner: ({ onDetected }: { onDetected: (code: string) => void }) => ({
    isScanning: true,
    isInitializing: false,
    torchOn: false,
    hasTorch: true,
    toggleTorch: vi.fn(),
    switchCamera: vi.fn(),
    stopScanning: mockStopScanning,
    simulateScan: onDetected,
  }),
}));

describe("BarcodeScannerModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockPermissionStatus = "idle";
    mockErrorMessage = null;
  });

  it("does not render when isOpen is false", () => {
    render(
      <BarcodeScannerModal
        isOpen={false}
        onClose={vi.fn()}
        onDetected={vi.fn()}
      />
    );
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("renders permission prompt when permission is idle", () => {
    render(
      <BarcodeScannerModal
        isOpen={true}
        onClose={vi.fn()}
        onDetected={vi.fn()}
      />
    );
    expect(screen.getByRole("dialog")).toBeDefined();
    expect(screen.getByText("Activar Cámara")).toBeDefined();
  });

  it("calls onClose when close button is clicked", () => {
    const onClose = vi.fn();
    render(
      <BarcodeScannerModal
        isOpen={true}
        onClose={onClose}
        onDetected={vi.fn()}
      />
    );

    const closeButton = screen.getByLabelText("Cerrar escáner");
    fireEvent.click(closeButton);
    expect(onClose).toHaveBeenCalled();
  });

  it("renders viewfinder when permission is granted", () => {
    mockPermissionStatus = "granted";
    render(
      <BarcodeScannerModal
        isOpen={true}
        onClose={vi.fn()}
        onDetected={vi.fn()}
      />
    );

    expect(screen.getByText("Alinee el código de barras en el recuadro")).toBeDefined();
  });

  it("renders denied state with recovery instructions when denied", () => {
    mockPermissionStatus = "denied";
    mockErrorMessage = "Permiso denegado";
    render(
      <BarcodeScannerModal
        isOpen={true}
        onClose={vi.fn()}
        onDetected={vi.fn()}
      />
    );

    expect(screen.getByText("Acceso a la cámara bloqueado")).toBeDefined();
    expect(screen.getByText("Reintentar Permiso")).toBeDefined();
  });
});
