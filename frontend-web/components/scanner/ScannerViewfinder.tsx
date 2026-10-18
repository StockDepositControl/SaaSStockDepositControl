"use client";

import React from "react";
import { Flashlight, FlipHorizontal, RefreshCw } from "lucide-react";

export interface ScannerViewfinderProps {
  elementId: string;
  isInitializing: boolean;
  isScanning: boolean;
  hasTorch: boolean;
  torchOn: boolean;
  onToggleTorch: () => void;
  onSwitchCamera: () => void;
}

export function ScannerViewfinder({
  elementId,
  isInitializing,
  isScanning,
  hasTorch,
  torchOn,
  onToggleTorch,
  onSwitchCamera,
}: ScannerViewfinderProps) {
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
