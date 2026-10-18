// @vitest-environment jsdom
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useCameraPermissions } from "./useCameraPermissions";

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
});
