"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Html5Qrcode, Html5QrcodeSupportedFormats } from "html5-qrcode";
import { triggerScanHaptic } from "@/lib/utils/haptics";

export interface UseBarcodeScannerOptions {
  elementId: string;
  active: boolean;
  onDetected: (decodedText: string) => void;
  onError?: (errorMessage: string) => void;
}

export interface UseBarcodeScannerResult {
  isScanning: boolean;
  isInitializing: boolean;
  torchOn: boolean;
  hasTorch: boolean;
  error: string | null;
  toggleTorch: () => Promise<void>;
  switchCamera: () => Promise<void>;
  stopScanning: () => Promise<void>;
  startScanning: () => Promise<void>;
  retryScanning: () => Promise<void>;
}

const SCAN_FPS = 10;
const FALLBACK_QRBOX = { width: 200, height: 150 };

// Guards against zero/NaN viewfinder dimensions while the <video> surface is
// still mounting, which would otherwise feed invalid sizes into canvas drawing.
export function computeQrbox(
  viewfinderWidth: number,
  viewfinderHeight: number
): { width: number; height: number } {
  if (
    !Number.isFinite(viewfinderWidth) ||
    !Number.isFinite(viewfinderHeight) ||
    viewfinderWidth <= 0 ||
    viewfinderHeight <= 0
  ) {
    return FALLBACK_QRBOX;
  }

  const minEdge = Math.min(viewfinderWidth, viewfinderHeight);
  const edge = Math.floor(minEdge * 0.75);
  return { width: edge, height: Math.floor(edge * 0.6) };
}

export function useBarcodeScanner({
  elementId,
  active,
  onDetected,
  onError,
}: UseBarcodeScannerOptions): UseBarcodeScannerResult {
  const [isScanning, setIsScanning] = useState(false);
  const [isInitializing, setIsInitializing] = useState(false);
  const [torchOn, setTorchOn] = useState(false);
  const [hasTorch, setHasTorch] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [facingMode, setFacingMode] = useState<"environment" | "user">("environment");

  const scannerRef = useRef<Html5Qrcode | null>(null);
  const isStartingRef = useRef(false);
  const startPromiseRef = useRef<Promise<void> | null>(null);
  const stopPromiseRef = useRef<Promise<void> | null>(null);
  // Incremented to abandon a hung initialization (see retryScanning)
  const attemptRef = useRef(0);

  // Keep latest callbacks in refs so inline handlers from the parent do not
  // change startScanning identity and restart the camera on every render.
  const onDetectedRef = useRef(onDetected);
  const onErrorRef = useRef(onError);
  useEffect(() => {
    onDetectedRef.current = onDetected;
    onErrorRef.current = onError;
  }, [onDetected, onError]);

  // Release camera tracks and DOM for the current scanner instance
  const teardownScanner = useCallback(async () => {
    const scanner = scannerRef.current;
    scannerRef.current = null;
    if (!scanner) return;

    try {
      if (scanner.isScanning) {
        await scanner.stop();
      }
    } catch (err) {
      console.warn("Scanner stop cleanup warning:", err);
    }

    try {
      await scanner.clear();
    } catch (err) {
      console.warn("Scanner clear cleanup warning:", err);
    }
  }, []);

  // Stop camera tracks explicitly. If a start is in flight, wait for it to
  // settle first so the stream it opens is never orphaned.
  const stopScanning = useCallback(async () => {
    if (stopPromiseRef.current) return stopPromiseRef.current;

    const stopPromise = (async () => {
      try {
        if (isStartingRef.current && startPromiseRef.current) {
          await startPromiseRef.current.catch(() => undefined);
        }
        await teardownScanner();
      } finally {
        setIsScanning(false);
        setIsInitializing(false);
        setTorchOn(false);
        setHasTorch(false);
        stopPromiseRef.current = null;
      }
    })();

    stopPromiseRef.current = stopPromise;
    return stopPromise;
  }, [teardownScanner]);

  const startScanning = useCallback(async () => {
    if (typeof window === "undefined") return;
    if (!elementId) return;

    // Never run two initializations against the same element
    if (isStartingRef.current && startPromiseRef.current) {
      return startPromiseRef.current;
    }

    // Check if element exists in DOM
    const targetEl = document.getElementById(elementId);
    if (!targetEl) return;

    isStartingRef.current = true;
    const attempt = ++attemptRef.current;
    const isStale = () => attempt !== attemptRef.current;

    const startPromise = (async () => {
      setIsInitializing(true);
      setError(null);

      try {
        // Let any pending shutdown finish before re-acquiring the camera
        if (stopPromiseRef.current) {
          await stopPromiseRef.current;
        }

        // Clean up any existing scanner instance first
        await teardownScanner();

        const scanner = new Html5Qrcode(elementId, {
          formatsToSupport: [
            Html5QrcodeSupportedFormats.EAN_13,
            Html5QrcodeSupportedFormats.CODE_128,
            Html5QrcodeSupportedFormats.QR_CODE,
            Html5QrcodeSupportedFormats.UPC_A,
          ],
          verbose: false,
          experimentalFeatures: {
            useBarCodeDetectorIfSupported: true,
          },
        });

        scannerRef.current = scanner;

        const config = {
          fps: SCAN_FPS,
          qrbox: computeQrbox,
          aspectRatio: 1.0,
        };

        await scanner.start(
          { facingMode },
          config,
          (decodedText: string) => {
            // Trigger subtle haptic vibration
            triggerScanHaptic();

            // Immediately stop scanner to release camera tracks
            stopScanning().then(() => {
              onDetectedRef.current(decodedText.trim());
            });
          },
          (errorMessage: string) => {
            // Transient frame scan failure - normal when reticle has no barcode in view
            const handleError = onErrorRef.current;
            if (handleError && !errorMessage.includes("No barcode or QR code detected")) {
              handleError(errorMessage);
            }
          }
        );

        // A retry abandoned this attempt while the camera was opening: release
        // its stream only. clear() would wipe the DOM now owned by the new scanner.
        if (isStale()) {
          await scanner.stop().catch((err: unknown) => {
            console.warn("Stale scanner stop cleanup warning:", err);
          });
          return;
        }

        setIsScanning(true);

        // Check for torch capability through the documented camera capabilities API
        try {
          if (typeof scanner.getRunningTrackCameraCapabilities === "function") {
            const torch = scanner.getRunningTrackCameraCapabilities().torchFeature();
            setHasTorch(torch.isSupported());
          }
        } catch {
          // Torch capability check is non-fatal
        }
      } catch (err: unknown) {
        if (isStale()) return;
        const errObj = err as { message?: string };
        const msg = errObj?.message || "Error al iniciar la cámara para escaneo.";
        setError(msg);
        setIsScanning(false);
      } finally {
        if (!isStale()) {
          setIsInitializing(false);
        }
      }
    })();

    startPromiseRef.current = startPromise;

    try {
      await startPromise;
    } finally {
      if (startPromiseRef.current === startPromise) {
        isStartingRef.current = false;
        startPromiseRef.current = null;
      }
    }
  }, [elementId, facingMode, stopScanning, teardownScanner]);

  // Restart the scan sequence even when the current start() never settles
  // (e.g. camera held by another app). The hung attempt is abandoned and
  // releases its own stream if it ever resolves.
  const retryScanning = useCallback(async () => {
    attemptRef.current += 1;
    isStartingRef.current = false;
    startPromiseRef.current = null;
    await teardownScanner();
    await startScanning();
  }, [startScanning, teardownScanner]);

  // Torch control toggle
  const toggleTorch = useCallback(async () => {
    if (!scannerRef.current || !hasTorch) return;

    try {
      const nextTorch = !torchOn;
      await scannerRef.current.applyVideoConstraints({
        advanced: [{ torch: nextTorch } as MediaTrackConstraintSet],
      });
      setTorchOn(nextTorch);
    } catch (err) {
      console.warn("Error toggling torch:", err);
    }
  }, [hasTorch, torchOn]);

  // Camera flip toggle (front vs back)
  const switchCamera = useCallback(async () => {
    const nextMode = facingMode === "environment" ? "user" : "environment";
    setFacingMode(nextMode);
  }, [facingMode]);

  // Control scanner based on active prop
  useEffect(() => {
    let isCancelled = false;
    if (active) {
      const timer = setTimeout(() => {
        if (!isCancelled) {
          startScanning();
        }
      }, 0);
      return () => {
        isCancelled = true;
        clearTimeout(timer);
        stopScanning();
      };
    } else {
      stopScanning();
    }
  }, [active, startScanning, stopScanning]);

  return {
    isScanning,
    isInitializing,
    torchOn,
    hasTorch,
    error,
    toggleTorch,
    switchCamera,
    stopScanning,
    startScanning,
    retryScanning,
  };
}
