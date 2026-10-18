// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useBarcodeScanner } from "./useBarcodeScanner";

const mockStart = vi.fn();
const mockStop = vi.fn().mockResolvedValue(undefined);
const mockClear = vi.fn().mockResolvedValue(undefined);
const mockApplyVideoConstraints = vi.fn().mockResolvedValue(undefined);

vi.mock("html5-qrcode", () => {
  return {
    Html5Qrcode: vi.fn().mockImplementation(() => ({
      start: mockStart,
      stop: mockStop,
      clear: mockClear,
      applyVideoConstraints: mockApplyVideoConstraints,
      isScanning: true,
      getRunningTrack: () => ({
        getCapabilities: () => ({ torch: true }),
      }),
    })),
    Html5QrcodeSupportedFormats: {
      EAN_13: 0,
      EAN_8: 1,
      CODE_128: 2,
      CODE_39: 3,
      UPC_A: 4,
      UPC_E: 5,
      QR_CODE: 6,
    },
  };
});

vi.mock("@/lib/utils/haptics", () => ({
  triggerScanHaptic: vi.fn(),
}));

describe("useBarcodeScanner", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    const div = document.createElement("div");
    div.id = "test-reader";
    document.body.appendChild(div);
  });

  afterEach(() => {
    const div = document.getElementById("test-reader");
    if (div) document.body.removeChild(div);
  });

  it("initializes scanner when active=true", async () => {
    mockStart.mockResolvedValue(undefined);

    const onDetected = vi.fn();
    const { result } = renderHook(() =>
      useBarcodeScanner({
        elementId: "test-reader",
        active: true,
        onDetected,
      })
    );

    await act(async () => {
      // allow effects to execute
      await new Promise((r) => setTimeout(r, 10));
    });

    expect(mockStart).toHaveBeenCalled();
    expect(result.current.isScanning).toBe(true);
    expect(result.current.hasTorch).toBe(true);
  });

  it("stops and clears scanner when unmounting", async () => {
    mockStart.mockResolvedValue(undefined);

    const onDetected = vi.fn();
    const { unmount } = renderHook(() =>
      useBarcodeScanner({
        elementId: "test-reader",
        active: true,
        onDetected,
      })
    );

    await act(async () => {
      await new Promise((r) => setTimeout(r, 10));
    });

    await act(async () => {
      unmount();
    });

    expect(mockStop).toHaveBeenCalled();
    expect(mockClear).toHaveBeenCalled();
  });

  it("handles onDetected callback and stops scanner", async () => {
    let scanSuccessCallback: ((text: string) => void) | null = null;
    mockStart.mockImplementation((_camera, _config, onSuccess) => {
      scanSuccessCallback = onSuccess;
      return Promise.resolve();
    });

    const onDetected = vi.fn();
    renderHook(() =>
      useBarcodeScanner({
        elementId: "test-reader",
        active: true,
        onDetected,
      })
    );

    await act(async () => {
      await new Promise((r) => setTimeout(r, 10));
    });

    expect(scanSuccessCallback).toBeDefined();

    await act(async () => {
      scanSuccessCallback!("7791234567890");
    });

    expect(onDetected).toHaveBeenCalledWith("7791234567890");
    expect(mockStop).toHaveBeenCalled();
  });
});
