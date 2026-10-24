// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import {
  useCameraPermissions,
  PERMISSION_RELEASE_DELAY_MS,
} from "./useCameraPermissions";

describe("useCameraPermissions", () => {
  const originalWindow = globalThis.window;
  const originalNavigator = globalThis.navigator;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    globalThis.window = originalWindow;
    globalThis.navigator = originalNavigator;
  });

  it("initializes with idle status", () => {
    const { result } = renderHook(() => useCameraPermissions());
    expect(result.current.status).toBe("idle");
    expect(result.current.errorMessage).toBeNull();
  });

  it("sets unsupported when window.isSecureContext is false and not localhost", async () => {
    Object.defineProperty(globalThis, "window", {
      value: {
        isSecureContext: false,
        location: { hostname: "192.168.1.50" },
      },
      writable: true,
      configurable: true,
    });

    const { result } = renderHook(() => useCameraPermissions());

    let granted = false;
    await act(async () => {
      granted = await result.current.requestPermission();
    });

    expect(granted).toBe(false);
    expect(result.current.status).toBe("unsupported");
    expect(result.current.errorMessage).toContain("HTTPS");
  });

  it("grants permission and releases track immediately on success", async () => {
    const trackStopMock = vi.fn();
    const streamMock = {
      getTracks: () => [{ stop: trackStopMock }],
    };

    Object.defineProperty(globalThis, "window", {
      value: {
        isSecureContext: true,
        location: { hostname: "localhost" },
      },
      writable: true,
      configurable: true,
    });

    Object.defineProperty(globalThis, "navigator", {
      value: {
        mediaDevices: {
          getUserMedia: vi.fn().mockResolvedValue(streamMock),
        },
      },
      writable: true,
      configurable: true,
    });

    const { result } = renderHook(() => useCameraPermissions());

    let granted = false;
    await act(async () => {
      granted = await result.current.requestPermission();
    });

    expect(granted).toBe(true);
    expect(result.current.status).toBe("granted");
    expect(trackStopMock).toHaveBeenCalled();
  });

  it("handles NotAllowedError as denied", async () => {
    Object.defineProperty(globalThis, "window", {
      value: {
        isSecureContext: true,
        location: { hostname: "localhost" },
      },
      writable: true,
      configurable: true,
    });

    const deniedError = new Error("Permission denied");
    deniedError.name = "NotAllowedError";

    Object.defineProperty(globalThis, "navigator", {
      value: {
        mediaDevices: {
          getUserMedia: vi.fn().mockRejectedValue(deniedError),
        },
      },
      writable: true,
      configurable: true,
    });

    const { result } = renderHook(() => useCameraPermissions());

    let granted = true;
    await act(async () => {
      granted = await result.current.requestPermission();
    });

    expect(granted).toBe(false);
    expect(result.current.status).toBe("denied");
    expect(result.current.errorMessage).toContain("Permiso denegado");
  });

  it("transitions to granted on mount without touching hardware when permissions.query reports granted", async () => {
    const getUserMediaMock = vi.fn();
    const queryMock = vi.fn().mockResolvedValue({ state: "granted" });

    Object.defineProperty(globalThis, "navigator", {
      value: {
        permissions: { query: queryMock },
        mediaDevices: { getUserMedia: getUserMediaMock },
      },
      writable: true,
      configurable: true,
    });

    const { result } = renderHook(() => useCameraPermissions());

    await act(async () => {
      await Promise.resolve();
    });

    expect(queryMock).toHaveBeenCalledWith({ name: "camera" });
    expect(result.current.status).toBe("granted");
    expect(getUserMediaMock).not.toHaveBeenCalled();
  });

  it("stays idle on mount when permissions.query reports prompt", async () => {
    Object.defineProperty(globalThis, "navigator", {
      value: {
        permissions: { query: vi.fn().mockResolvedValue({ state: "prompt" }) },
        mediaDevices: { getUserMedia: vi.fn() },
      },
      writable: true,
      configurable: true,
    });

    const { result } = renderHook(() => useCameraPermissions());

    await act(async () => {
      await Promise.resolve();
    });

    expect(result.current.status).toBe("idle");
  });

  it("requestPermission returns true via permissions.query fast path without calling getUserMedia", async () => {
    const getUserMediaMock = vi.fn();

    Object.defineProperty(globalThis, "window", {
      value: {
        isSecureContext: true,
        location: { hostname: "localhost" },
      },
      writable: true,
      configurable: true,
    });

    Object.defineProperty(globalThis, "navigator", {
      value: {
        permissions: { query: vi.fn().mockResolvedValue({ state: "granted" }) },
        mediaDevices: { getUserMedia: getUserMediaMock },
      },
      writable: true,
      configurable: true,
    });

    const { result } = renderHook(() => useCameraPermissions());

    let granted = false;
    await act(async () => {
      granted = await result.current.requestPermission();
    });

    expect(granted).toBe(true);
    expect(result.current.status).toBe("granted");
    expect(getUserMediaMock).not.toHaveBeenCalled();
  });

  it("falls back to getUserMedia with flexible constraints when permissions.query throws", async () => {
    const trackStopMock = vi.fn();
    const getUserMediaMock = vi.fn().mockResolvedValue({
      getTracks: () => [{ stop: trackStopMock }],
    });

    Object.defineProperty(globalThis, "window", {
      value: {
        isSecureContext: true,
        location: { hostname: "localhost" },
      },
      writable: true,
      configurable: true,
    });

    Object.defineProperty(globalThis, "navigator", {
      value: {
        permissions: {
          query: vi.fn().mockRejectedValue(new TypeError("camera is not a valid PermissionName")),
        },
        mediaDevices: { getUserMedia: getUserMediaMock },
      },
      writable: true,
      configurable: true,
    });

    const { result } = renderHook(() => useCameraPermissions());

    let granted = false;
    await act(async () => {
      granted = await result.current.requestPermission();
    });

    expect(granted).toBe(true);
    expect(getUserMediaMock).toHaveBeenCalledWith({
      video: { facingMode: { ideal: "environment" } },
    });
    expect(trackStopMock).toHaveBeenCalled();
    expect(result.current.status).toBe("granted");
  });

  it("waits for the hardware release cooldown after stopping probe tracks before resolving", async () => {
    vi.useFakeTimers();
    try {
      const trackStopMock = vi.fn();

      Object.defineProperty(globalThis, "window", {
        value: {
          isSecureContext: true,
          location: { hostname: "localhost" },
        },
        writable: true,
        configurable: true,
      });

      Object.defineProperty(globalThis, "navigator", {
        value: {
          mediaDevices: {
            getUserMedia: vi.fn().mockResolvedValue({
              getTracks: () => [{ stop: trackStopMock }],
            }),
          },
        },
        writable: true,
        configurable: true,
      });

      const { result } = renderHook(() => useCameraPermissions());

      let settled = false;
      let granted = false;
      let pending: Promise<boolean> = Promise.resolve(false);
      act(() => {
        pending = result.current.requestPermission().then((value) => {
          settled = true;
          granted = value;
          return value;
        });
      });

      await act(async () => {
        await vi.advanceTimersByTimeAsync(PERMISSION_RELEASE_DELAY_MS - 1);
      });

      expect(trackStopMock).toHaveBeenCalled();
      expect(settled).toBe(false);
      expect(result.current.status).toBe("requesting");

      await act(async () => {
        await vi.advanceTimersByTimeAsync(1);
        await pending;
      });

      expect(PERMISSION_RELEASE_DELAY_MS).toBe(150);
      expect(settled).toBe(true);
      expect(granted).toBe(true);
      expect(result.current.status).toBe("granted");
    } finally {
      vi.useRealTimers();
    }
  });

  it("maps NotFoundError to unsupported", async () => {
    Object.defineProperty(globalThis, "window", {
      value: {
        isSecureContext: true,
        location: { hostname: "localhost" },
      },
      writable: true,
      configurable: true,
    });

    const notFoundError = new Error("Requested device not found");
    notFoundError.name = "NotFoundError";

    Object.defineProperty(globalThis, "navigator", {
      value: {
        mediaDevices: {
          getUserMedia: vi.fn().mockRejectedValue(notFoundError),
        },
      },
      writable: true,
      configurable: true,
    });

    const { result } = renderHook(() => useCameraPermissions());

    let granted = true;
    await act(async () => {
      granted = await result.current.requestPermission();
    });

    expect(granted).toBe(false);
    expect(result.current.status).toBe("unsupported");
    expect(result.current.errorMessage).toContain("No se encontró ninguna cámara");
  });
});
