/**
 * Haptic feedback utility for mobile barcode scanning
 * Triggers subtle vibration feedback on supported devices
 */
export function triggerScanHaptic(): boolean {
  if (typeof navigator === "undefined") {
    return false;
  }

  try {
    if ("vibrate" in navigator && typeof navigator.vibrate === "function") {
      return navigator.vibrate([80]);
    }
  } catch {
    // Graceful no-op on platforms restricting vibration
  }

  return false;
}
