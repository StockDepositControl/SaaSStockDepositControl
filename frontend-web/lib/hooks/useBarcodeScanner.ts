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
  const isStoppingRef = useRef(false);

  // Stop camera tracks explicitly
  const stopScanning = useCallback(async () => {
    if (isStoppingRef.current) return;
    isStoppingRef.current = true;

    try {
      if (scannerRef.current) {
        if (scannerRef.current.isScanning) {
          await scannerRef.current.stop();
        }
        await scannerRef.current.clear();
        scannerRef.current = null;
      }
    } catch (err) {
      console.warn("Scanner stop cleanup warning:", err);
    } finally {
      setIsScanning(false);
      setIsInitializing(false);
      setTorchOn(false);
      setHasTorch(false);
      isStoppingRef.current = false;
    }
  }, []);

  const startScanning = useCallback(async () => {
    if (typeof window === "undefined") return;
    if (!elementId) return;

    // Check if element exists in DOM
    const targetEl = document.getElementById(elementId);
    if (!targetEl) return;

    setIsInitializing(true);
    setError(null);

    try {
      // Clean up any existing scanner instance first
      if (scannerRef.current) {
        await stopScanning();
      }

      const scanner = new Html5Qrcode(elementId, {
        formatsToSupport: [
          Html5QrcodeSupportedFormats.EAN_13,
          Html5QrcodeSupportedFormats.EAN_8,
          Html5QrcodeSupportedFormats.CODE_128,
          Html5QrcodeSupportedFormats.CODE_39,
          Html5QrcodeSupportedFormats.UPC_A,
          Html5QrcodeSupportedFormats.UPC_E,
          Html5QrcodeSupportedFormats.QR_CODE,
        ],
        verbose: false,
      });

      scannerRef.current = scanner;

      const config = {
        fps: 15,
        qrbox: (viewfinderWidth: number, viewfinderHeight: number) => {
          const minEdge = Math.min(viewfinderWidth, viewfinderHeight);
          const edge = Math.floor(minEdge * 0.75);
          return { width: edge, height: Math.floor(edge * 0.6) };
        },
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
            onDetected(decodedText.trim());
          });
        },
        (errorMessage: string) => {
          // Transient frame scan failure - normal when reticle has no barcode in view
          if (onError && !errorMessage.includes("No barcode or QR code detected")) {
            onError(errorMessage);
          }
        }
      );

      setIsScanning(true);

      // Check for torch capability if supported by running track
      try {
        const videoTrack = (scanner as unknown as { getRunningTrack?: () => MediaStreamTrack | null }).getRunningTrack?.();
        if (videoTrack && typeof videoTrack.getCapabilities === "function") {
          const capabilities = videoTrack.getCapabilities() as unknown as Record<string, unknown>;
          if (capabilities && Boolean(capabilities["torch"])) {
            setHasTorch(true);
          }
        }
      } catch {
        // Torch capability check is non-fatal
      }
    } catch (err: unknown) {
      const errObj = err as { message?: string };
      const msg = errObj?.message || "Error al iniciar la cámara para escaneo.";
      setError(msg);
      setIsScanning(false);
    } finally {
      setIsInitializing(false);
    }
  }, [elementId, facingMode, onDetected, onError, stopScanning]);

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
  };
}
