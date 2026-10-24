"use client";

import React, { useEffect } from "react";
import { X } from "lucide-react";
import { useCameraPermissions } from "@/lib/hooks/useCameraPermissions";
import { useBarcodeScanner } from "@/lib/hooks/useBarcodeScanner";
import { ScannerPermissionState } from "./ScannerPermissionState";
import { ScannerViewfinder } from "./ScannerViewfinder";

export interface BarcodeScannerModalProps {
  isOpen: boolean;
  onClose: () => void;
  onDetected: (barcode: string) => void;
}

const SCANNER_ELEMENT_ID = "barcode-scanner-viewfinder";

export function BarcodeScannerModal({
  isOpen,
  onClose,
  onDetected,
}: BarcodeScannerModalProps) {
  const {
    status: permissionStatus,
    errorMessage,
    requestPermission,
    resetPermission,
  } = useCameraPermissions();

  const isPermissionGranted = permissionStatus === "granted";

  const {
    isScanning,
    isInitializing,
    torchOn,
    hasTorch,
    error: scannerError,
    toggleTorch,
    switchCamera,
    stopScanning,
    retryScanning,
  } = useBarcodeScanner({
    elementId: SCANNER_ELEMENT_ID,
    active: isOpen && isPermissionGranted,
    onDetected: (code) => {
      onDetected(code);
      onClose();
    },
  });

  // Handle escape key
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // When modal closes, reset permissions and stop scanning
  useEffect(() => {
    if (!isOpen) {
      stopScanning();
      resetPermission();
    }
  }, [isOpen, stopScanning, resetPermission]);

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="scanner-modal-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/80 backdrop-blur-md transition-opacity"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal Dialog Content */}
      <div className="relative w-full max-w-md bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl overflow-hidden z-10 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800">
          <div>
            <h2
              id="scanner-modal-title"
              className="text-base font-bold text-white tracking-tight"
            >
              Escáner de Código de Barras
            </h2>
            <p className="text-xs text-slate-400">
              EAN-13, CODE-128, QR y UPC
            </p>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="w-12 h-12 rounded-xl flex items-center justify-center text-slate-400 hover:text-white hover:bg-slate-800 active:scale-95 transition cursor-pointer"
            aria-label="Cerrar escáner"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-4 sm:p-6 flex flex-col items-center justify-center">
          {isPermissionGranted ? (
            <ScannerViewfinder
              elementId={SCANNER_ELEMENT_ID}
              isInitializing={isInitializing}
              isScanning={isScanning}
              hasTorch={hasTorch}
              torchOn={torchOn}
              error={scannerError}
              onToggleTorch={toggleTorch}
              onSwitchCamera={switchCamera}
              onRetry={retryScanning}
            />
          ) : (
            <ScannerPermissionState
              status={permissionStatus}
              errorMessage={errorMessage}
              onRequestPermission={requestPermission}
              onCancel={onClose}
            />
          )}
        </div>
      </div>
    </div>
  );
}
