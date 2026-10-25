// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { Html5Qrcode } from "html5-qrcode";
import { triggerScanHaptic } from "@/lib/utils/haptics";
import { useBarcodeScanner, computeQrbox } from "./useBarcodeScanner";

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
      getRunningTrackCameraCapabilities: () => ({
        torchFeature: () => ({ isSupported: () => true }),
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
    expect(triggerScanHaptic).toHaveBeenCalled();
    expect(mockStop).toHaveBeenCalled();
  });

  it("enables the native BarcodeDetector and restricts formats to the industrial set", async () => {
    mockStart.mockResolvedValue(undefined);

    renderHook(() =>
      useBarcodeScanner({
        elementId: "test-reader",
        active: true,
        onDetected: vi.fn(),
      })
    );

    await act(async () => {
      await new Promise((r) => setTimeout(r, 10));
    });

    expect(Html5Qrcode).toHaveBeenCalledWith("test-reader", {
      formatsToSupport: [0, 2, 6, 4],
      verbose: false,
      experimentalFeatures: { useBarCodeDetectorIfSupported: true },
    });
  });

  it("starts with flexible facingMode constraints at 10 fps", async () => {
    mockStart.mockResolvedValue(undefined);

    renderHook(() =>
      useBarcodeScanner({
        elementId: "test-reader",
        active: true,
        onDetected: vi.fn(),
      })
    );

    await act(async () => {
      await new Promise((r) => setTimeout(r, 10));
    });

    const [cameraConfig, scanConfig] = mockStart.mock.calls[0];
    expect(cameraConfig).toEqual({ facingMode: "environment" });
    expect(scanConfig.fps).toBe(10);
  });

  it("restarts with the opposite flexible facingMode when switching camera", async () => {
    mockStart.mockResolvedValue(undefined);

    const { result } = renderHook(() =>
      useBarcodeScanner({
        elementId: "test-reader",
        active: true,
        onDetected: vi.fn(),
      })
    );

    await act(async () => {
      await new Promise((r) => setTimeout(r, 10));
    });

    await act(async () => {
      await result.current.switchCamera();
    });

    await waitFor(() => expect(mockStart).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(result.current.isScanning).toBe(true));

    expect(mockStop).toHaveBeenCalled();
    expect(mockClear).toHaveBeenCalled();
    expect(mockStart).toHaveBeenLastCalledWith(
      { facingMode: "user" },
      expect.anything(),
      expect.any(Function),
      expect.any(Function)
    );
    expect(result.current.isScanning).toBe(true);
  });

  it("waits for an in-flight start before stopping and clearing on unmount", async () => {
    let resolveStart: () => void = () => {};
    mockStart.mockImplementation(
      () => new Promise<void>((resolve) => (resolveStart = resolve))
    );

    const { unmount } = renderHook(() =>
      useBarcodeScanner({
        elementId: "test-reader",
        active: true,
        onDetected: vi.fn(),
      })
    );

    await act(async () => {
      await new Promise((r) => setTimeout(r, 10));
    });

    expect(mockStart).toHaveBeenCalledTimes(1);

    await act(async () => {
      unmount();
      await new Promise((r) => setTimeout(r, 10));
    });

    // Stopping must not run against a half-initialized camera
    expect(mockStop).not.toHaveBeenCalled();
    expect(mockClear).not.toHaveBeenCalled();

    await act(async () => {
      resolveStart();
      await new Promise((r) => setTimeout(r, 10));
    });

    expect(mockStop).toHaveBeenCalledTimes(1);
    expect(mockClear).toHaveBeenCalledTimes(1);
    expect(mockStop.mock.invocationCallOrder[0]).toBeLessThan(
      mockClear.mock.invocationCallOrder[0]
    );
  });

  it("stopScanning during a failing start resolves cleanly and exposes the error", async () => {
    let rejectStart: (err: Error) => void = () => {};
    mockStart.mockImplementation(
      () => new Promise<void>((_resolve, reject) => (rejectStart = reject))
    );

    const { result } = renderHook(() =>
      useBarcodeScanner({
        elementId: "test-reader",
        active: true,
        onDetected: vi.fn(),
      })
    );

    await act(async () => {
      await new Promise((r) => setTimeout(r, 10));
    });

    let stopPromise: Promise<void> = Promise.resolve();
    await act(async () => {
      stopPromise = result.current.stopScanning();
      rejectStart(new Error("Could not start video source"));
      await expect(stopPromise).resolves.toBeUndefined();
    });

    expect(mockClear).toHaveBeenCalled();
    expect(result.current.isScanning).toBe(false);
    expect(result.current.isInitializing).toBe(false);
    expect(result.current.error).toBe("Could not start video source");
  });

  it("does not start the camera twice when startScanning is called concurrently", async () => {
    let resolveStart: () => void = () => {};
    mockStart.mockImplementation(
      () => new Promise<void>((resolve) => (resolveStart = resolve))
    );

    const { result } = renderHook(() =>
      useBarcodeScanner({
        elementId: "test-reader",
        active: false,
        onDetected: vi.fn(),
      })
    );

    await act(async () => {
      const first = result.current.startScanning();
      const second = result.current.startScanning();
      await new Promise((r) => setTimeout(r, 10));
      resolveStart();
      await Promise.all([first, second]);
    });

    expect(Html5Qrcode).toHaveBeenCalledTimes(1);
    expect(mockStart).toHaveBeenCalledTimes(1);
    expect(result.current.isScanning).toBe(true);
  });
});

describe("useBarcodeScanner retry", () => {
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

  it("abandons a hung start, starts a fresh scanner and releases the stale one when it settles", async () => {
    const resolvers: Array<() => void> = [];
    mockStart.mockImplementation(
      () => new Promise<void>((resolve) => resolvers.push(resolve))
    );

    const { result } = renderHook(() =>
      useBarcodeScanner({
        elementId: "test-reader",
        active: true,
        onDetected: vi.fn(),
      })
    );

    await act(async () => {
      await new Promise((r) => setTimeout(r, 10));
    });
    expect(mockStart).toHaveBeenCalledTimes(1);
    expect(result.current.isInitializing).toBe(true);

    let retryPromise: Promise<void> = Promise.resolve();
    await act(async () => {
      retryPromise = result.current.retryScanning();
    });

    await waitFor(() => expect(mockStart).toHaveBeenCalledTimes(2));
    expect(Html5Qrcode).toHaveBeenCalledTimes(2);
    expect(result.current.isInitializing).toBe(true);

    // The stale attempt settles late: it must release its own camera without touching state
    mockStop.mockClear();
    await act(async () => {
      resolvers[0]();
      await new Promise((r) => setTimeout(r, 10));
    });
    expect(mockStop).toHaveBeenCalledTimes(1);
    expect(result.current.isScanning).toBe(false);
    expect(result.current.isInitializing).toBe(true);

    await act(async () => {
      resolvers[1]();
      await retryPromise;
    });

    expect(result.current.isScanning).toBe(true);
    expect(result.current.isInitializing).toBe(false);
  });
});

describe("useBarcodeScanner callback stability", () => {
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

  it("does not restart the camera when the parent re-renders with a new inline onDetected", async () => {
    mockStart.mockResolvedValue(undefined);

    const { rerender } = renderHook(
      ({ onDetected }: { onDetected: (decodedText: string) => void }) =>
        useBarcodeScanner({ elementId: "test-reader", active: true, onDetected }),
      { initialProps: { onDetected: vi.fn() } }
    );

    await act(async () => {
      await new Promise((r) => setTimeout(r, 10));
    });

    const latestOnDetected = vi.fn();
    await act(async () => {
      rerender({ onDetected: latestOnDetected });
      await new Promise((r) => setTimeout(r, 10));
    });

    expect(mockStart).toHaveBeenCalledTimes(1);
    expect(mockStop).not.toHaveBeenCalled();

    const onSuccess = mockStart.mock.calls[0][2] as (text: string) => void;
    await act(async () => {
      onSuccess(" 7790001112223 ");
      await new Promise((r) => setTimeout(r, 0));
    });

    expect(latestOnDetected).toHaveBeenCalledWith("7790001112223");
  });

  it("surfaces error and sets isScanning to false when start fails", async () => {
    mockStart.mockRejectedValue(new Error("Camera device busy"));

    const { result } = renderHook(() =>
      useBarcodeScanner({
        elementId: "test-reader",
        active: true,
        onDetected: vi.fn(),
      })
    );

    await act(async () => {
      await new Promise((r) => setTimeout(r, 10));
    });

    expect(result.current.isScanning).toBe(false);
    expect(result.current.isInitializing).toBe(false);
    expect(result.current.error).toBe("Camera device busy");
  });
});

describe("computeQrbox", () => {
  it("falls back to a safe box when viewfinder dimensions are zero or invalid", () => {
    expect(computeQrbox(0, 0)).toEqual({ width: 200, height: 150 });
    expect(computeQrbox(0, 480)).toEqual({ width: 200, height: 150 });
    expect(computeQrbox(-10, 480)).toEqual({ width: 200, height: 150 });
    expect(computeQrbox(Number.NaN, 480)).toEqual({ width: 200, height: 150 });
  });

  it("derives a barcode-shaped box from the shortest viewfinder edge", () => {
    expect(computeQrbox(400, 300)).toEqual({ width: 225, height: 135 });
  });
});
