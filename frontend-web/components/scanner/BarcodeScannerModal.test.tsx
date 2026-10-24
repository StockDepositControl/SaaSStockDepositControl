// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
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
const mockRetryScanning = vi.fn().mockResolvedValue(undefined);
let mockIsInitializing = false;
let mockScannerError: string | null = null;
let mockScannerActive: boolean | undefined;
vi.mock("@/lib/hooks/useBarcodeScanner", () => ({
  useBarcodeScanner: ({
    onDetected,
    active,
  }: {
    onDetected: (code: string) => void;
    active: boolean;
  }) => {
    mockScannerActive = active;
    return {
      isScanning: !mockIsInitializing && !mockScannerError,
      isInitializing: mockIsInitializing,
      torchOn: false,
      hasTorch: true,
      error: mockScannerError,
      toggleTorch: vi.fn(),
      switchCamera: vi.fn(),
      stopScanning: mockStopScanning,
      retryScanning: mockRetryScanning,
      simulateScan: onDetected,
    };
  },
}));

describe("BarcodeScannerModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockPermissionStatus = "idle";
    mockErrorMessage = null;
    mockIsInitializing = false;
    mockScannerError = null;
    mockScannerActive = undefined;
  });

  afterEach(() => {
    vi.useRealTimers();
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

  it("switches from permission prompt to viewfinder and activates the scanner once granted", () => {
    const props = { isOpen: true, onClose: vi.fn(), onDetected: vi.fn() };
    const { rerender } = render(<BarcodeScannerModal {...props} />);

    expect(screen.getByText("Activar Cámara")).toBeDefined();
    expect(mockScannerActive).toBe(false);

    mockPermissionStatus = "granted";
    rerender(<BarcodeScannerModal {...props} />);

    expect(screen.queryByText("Activar Cámara")).toBeNull();
    expect(screen.getByText("Alinee el código de barras en el recuadro")).toBeDefined();
    expect(mockScannerActive).toBe(true);
  });

  it("stops scanning and resets permission when closed, and unmounts cleanly", async () => {
    mockPermissionStatus = "granted";
    const props = { onClose: vi.fn(), onDetected: vi.fn() };
    const { rerender, unmount } = render(
      <BarcodeScannerModal isOpen={true} {...props} />
    );

    rerender(<BarcodeScannerModal isOpen={false} {...props} />);

    expect(screen.queryByRole("dialog")).toBeNull();
    expect(mockScannerActive).toBe(false);
    expect(mockStopScanning).toHaveBeenCalled();
    expect(mockResetPermission).toHaveBeenCalled();

    await act(async () => {
      unmount();
    });
  });

  it("shows a slow-camera warning after 7 seconds of initialization and retries on demand", () => {
    vi.useFakeTimers();
    mockPermissionStatus = "granted";
    mockIsInitializing = true;

    render(
      <BarcodeScannerModal isOpen={true} onClose={vi.fn()} onDetected={vi.fn()} />
    );

    expect(screen.getByText("Iniciando cámara...")).toBeDefined();

    act(() => {
      vi.advanceTimersByTime(6999);
    });
    expect(screen.queryByText(/La cámara está tardando en responder/)).toBeNull();

    act(() => {
      vi.advanceTimersByTime(1);
    });
    expect(
      screen.getByText(
        "La cámara está tardando en responder. Asegúrese de que ninguna otra aplicación esté usando la cámara."
      )
    ).toBeDefined();

    fireEvent.click(screen.getByRole("button", { name: "Reintentar" }));
    expect(mockRetryScanning).toHaveBeenCalledTimes(1);
  });

  it("hides the slow-camera warning once initialization finishes", () => {
    vi.useFakeTimers();
    mockPermissionStatus = "granted";
    mockIsInitializing = true;
    const props = { isOpen: true, onClose: vi.fn(), onDetected: vi.fn() };

    const { rerender } = render(<BarcodeScannerModal {...props} />);

    act(() => {
      vi.advanceTimersByTime(7000);
    });
    expect(screen.getByRole("button", { name: "Reintentar" })).toBeDefined();

    mockIsInitializing = false;
    rerender(<BarcodeScannerModal {...props} />);

    expect(screen.queryByRole("button", { name: "Reintentar" })).toBeNull();
    expect(screen.getByText("Alinee el código de barras en el recuadro")).toBeDefined();
  });

  it("renders error overlay with retry button when scanner encounters an error", () => {
    mockPermissionStatus = "granted";
    mockScannerError = "Error al conectar con el sensor de la cámara.";

    render(
      <BarcodeScannerModal isOpen={true} onClose={vi.fn()} onDetected={vi.fn()} />
    );

    expect(screen.getByText("Error al iniciar cámara")).toBeDefined();
    expect(screen.getByText("Error al conectar con el sensor de la cámara.")).toBeDefined();

    const retryBtn = screen.getByRole("button", { name: "Reintentar" });
    expect(retryBtn).toBeDefined();
    fireEvent.click(retryBtn);
    expect(mockRetryScanning).toHaveBeenCalledTimes(1);
  });
});
