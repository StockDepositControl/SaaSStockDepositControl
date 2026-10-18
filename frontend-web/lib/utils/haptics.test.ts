import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { triggerScanHaptic } from "./haptics";

describe("triggerScanHaptic", () => {
  const originalNavigator = globalThis.navigator;

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    Object.defineProperty(globalThis, "navigator", {
      value: originalNavigator,
      writable: true,
      configurable: true,
    });
  });

  it("triggers navigator.vibrate with 80ms when available", () => {
    const vibrateMock = vi.fn().mockReturnValue(true);
    Object.defineProperty(globalThis, "navigator", {
      value: { vibrate: vibrateMock },
      writable: true,
      configurable: true,
    });

    const result = triggerScanHaptic();
    expect(result).toBe(true);
    expect(vibrateMock).toHaveBeenCalledWith([80]);
  });

  it("safely returns false when navigator.vibrate is undefined", () => {
    Object.defineProperty(globalThis, "navigator", {
      value: {},
      writable: true,
      configurable: true,
    });

    const result = triggerScanHaptic();
    expect(result).toBe(false);
  });
});
