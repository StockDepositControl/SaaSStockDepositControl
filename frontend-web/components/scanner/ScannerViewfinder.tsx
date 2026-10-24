"use client";

import React, { useEffect, useState } from "react";
import { AlertCircle, Flashlight, FlipHorizontal, RefreshCw } from "lucide-react";

// After this long "initializing", the camera is likely held by another app
export const SLOW_INIT_WARNING_MS = 7000;

export interface ScannerViewfinderProps {
  elementId: string;
  isInitializing: boolean;
  isScanning: boolean;
  hasTorch: boolean;
  torchOn: boolean;
  error?: string | null;
  onToggleTorch: () => void;
  onSwitchCamera: () => void;
  onRetry: () => void;
}

export function ScannerViewfinder({
  elementId,
  isInitializing,
  isScanning,
  hasTorch,
  torchOn,
  error,
  onToggleTorch,
  onSwitchCamera,
  onRetry,
}: ScannerViewfinderProps) {
  const [isSlowInit, setIsSlowInit] = useState(false);

  useEffect(() => {
    if (!isInitializing) return;

    const timer = setTimeout(() => setIsSlowInit(true), SLOW_INIT_WARNING_MS);
    return () => {
      clearTimeout(timer);
      setIsSlowInit(false);
    };
  }, [isInitializing]);

  return (
    <div className="relative w-full aspect-square max-h-[70vh] bg-black rounded-2xl overflow-hidden flex items-center justify-center border border-slate-700/80 shadow-2xl">
      {/* HTML5-QRCode Target Element */}
      <div id={elementId} className="w-full h-full [&_video]:object-cover" />

      {/* Loading Overlay */}
      {isInitializing && (
        <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-xs flex flex-col items-center justify-center gap-3 z-20 text-white">
          <RefreshCw className="w-8 h-8 text-blue-400 animate-spin" />
          <span className="text-xs font-semibold text-slate-300">
            Iniciando cámara...
          </span>

          {isSlowInit && (
            <div
              role="alert"
              className="mx-6 mt-2 flex flex-col items-center gap-3 rounded-xl border border-amber-400/30 bg-amber-400/10 px-4 py-3 text-center backdrop-blur-md"
            >
              <p className="text-xs font-medium text-amber-200">
                La cámara está tardando en responder. Asegúrese de que ninguna otra aplicación esté usando la cámara.
              </p>
              <button
                type="button"
                onClick={onRetry}
                className="min-h-11 px-4 rounded-xl bg-amber-400 text-slate-950 text-xs font-bold flex items-center gap-2 transition cursor-pointer active:scale-95 hover:bg-amber-300"
              >
                <RefreshCw className="w-4 h-4" />
                Reintentar
              </button>
            </div>
          )}
        </div>
      )}

      {/* Error Overlay */}
      {error && !isInitializing && !isScanning && (
        <div
          role="alert"
          className="absolute inset-0 bg-slate-950/90 backdrop-blur-xs flex flex-col items-center justify-center p-6 text-center z-20 text-white gap-3"
        >
          <div className="w-12 h-12 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center">
            <AlertCircle className="w-6 h-6" />
          </div>
          <div className="flex flex-col gap-1 max-w-xs">
            <h3 className="text-sm font-bold text-white">Error al iniciar cámara</h3>
            <p className="text-xs text-slate-400 leading-relaxed">{error}</p>
          </div>
          <button
            type="button"
            onClick={onRetry}
            className="min-h-11 px-5 rounded-xl bg-amber-400 text-slate-950 text-xs font-bold flex items-center gap-2 transition cursor-pointer active:scale-95 hover:bg-amber-300 shadow-md mt-1"
          >
            <RefreshCw className="w-4 h-4" />
            Reintentar
          </button>
        </div>
      )}

      {/* Viewfinder Reticle & Laser (Visible when scanning) */}
      {isScanning && (
        <div className="absolute inset-0 pointer-events-none flex items-center justify-center z-10">
          {/* Target Reticle Box */}
          <div className="relative w-4/5 h-3/5 max-w-[280px] max-h-[180px]">
            {/* Top-Left Corner */}
            <div className="absolute top-0 left-0 w-7 h-7 border-t-4 border-l-4 border-emerald-400 rounded-tl-lg shadow-sm" />
            {/* Top-Right Corner */}
            <div className="absolute top-0 right-0 w-7 h-7 border-t-4 border-r-4 border-emerald-400 rounded-tr-lg shadow-sm" />
            {/* Bottom-Left Corner */}
            <div className="absolute bottom-0 left-0 w-7 h-7 border-b-4 border-l-4 border-emerald-400 rounded-bl-lg shadow-sm" />
            {/* Bottom-Right Corner */}
            <div className="absolute bottom-0 right-0 w-7 h-7 border-b-4 border-r-4 border-emerald-400 rounded-br-lg shadow-sm" />

            {/* Animated Scanning Laser Line */}
            <div className="absolute inset-x-0 top-1/2 h-0.5 bg-gradient-to-r from-transparent via-emerald-400 to-transparent shadow-[0_0_12px_#34d399] animate-pulse" />
          </div>

          {/* Prompt Label */}
          <div className="absolute bottom-4 inset-x-4 flex justify-center">
            <span className="px-3 py-1.5 rounded-full bg-black/60 backdrop-blur-md border border-white/10 text-white text-[11px] font-medium tracking-wide shadow-md">
              Alinee el código de barras en el recuadro
            </span>
          </div>
        </div>
      )}

      {/* Floating Action Controls on Top */}
      <div className="absolute top-3 right-3 flex items-center gap-2 z-20">
        {hasTorch && (
          <button
            type="button"
            onClick={onToggleTorch}
            aria-label={torchOn ? "Apagar linterna" : "Encender linterna"}
            className={`w-11 h-11 rounded-full flex items-center justify-center transition cursor-pointer active:scale-95 shadow-md ${
              torchOn
                ? "bg-amber-400 text-slate-950 font-bold"
                : "bg-black/60 text-white hover:bg-black/80 backdrop-blur-md border border-white/20"
            }`}
          >
            <Flashlight className="w-5 h-5" />
          </button>
        )}

        <button
          type="button"
          onClick={onSwitchCamera}
          aria-label="Cambiar de cámara"
          className="w-11 h-11 rounded-full bg-black/60 hover:bg-black/80 backdrop-blur-md border border-white/20 text-white flex items-center justify-center transition cursor-pointer active:scale-95 shadow-md"
        >
          <FlipHorizontal className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
