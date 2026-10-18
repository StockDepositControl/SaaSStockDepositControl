"use client";

import React from "react";
import { Camera, ShieldAlert, ArrowLeft, RefreshCw } from "lucide-react";
import { CameraPermissionStatus } from "@/lib/hooks/useCameraPermissions";

export interface ScannerPermissionStateProps {
  status: CameraPermissionStatus;
  errorMessage: string | null;
  onRequestPermission: () => void;
  onCancel: () => void;
}

export function ScannerPermissionState({
  status,
  errorMessage,
  onRequestPermission,
  onCancel,
}: ScannerPermissionStateProps) {
  if (status === "denied" || status === "unsupported") {
    return (
      <div className="flex flex-col items-center justify-center p-6 text-center max-w-sm mx-auto space-y-5">
        <div className="w-16 h-16 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-500 flex items-center justify-center shrink-0">
          <ShieldAlert className="w-8 h-8" />
        </div>

        <div className="space-y-2">
          <h3 className="text-lg font-bold text-white tracking-tight">
            {status === "unsupported"
              ? "Cámara no disponible"
              : "Acceso a la cámara bloqueado"}
          </h3>
          <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
            {errorMessage ||
              "Para escanear códigos de barras en el depósito, es necesario habilitar el acceso a la cámara en su dispositivo."}
          </p>
        </div>

        {/* Step-by-step instructions */}
        <div className="bg-slate-800/80 border border-slate-700/60 rounded-xl p-4 text-left w-full space-y-2 text-xs text-slate-300">
          <div className="font-semibold text-slate-200">Cómo habilitar:</div>
          <ul className="list-disc pl-4 space-y-1 text-slate-400">
            <li>
              <strong className="text-slate-300">Android Chrome:</strong> Toque el candado o menú junto a la URL → Permisos → Cámara → Permitir.
            </li>
            <li>
              <strong className="text-slate-300">iOS Safari:</strong> Toque &quot;aA&quot; en la barra de navegación → Configuración de sitio web → Cámara → Permitir.
            </li>
          </ul>
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-3 w-full pt-2">
          <button
            type="button"
            onClick={onRequestPermission}
            className="w-full sm:flex-1 h-12 rounded-xl bg-blue-600 hover:bg-blue-500 active:scale-95 text-white font-semibold text-sm flex items-center justify-center gap-2 transition cursor-pointer shadow-lg shadow-blue-500/20"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Reintentar Permiso</span>
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="w-full sm:flex-1 h-12 rounded-xl bg-slate-800 hover:bg-slate-700 active:scale-95 text-slate-300 font-semibold text-sm flex items-center justify-center gap-2 transition cursor-pointer border border-slate-700"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Entrada Manual</span>
          </button>
        </div>
      </div>
    );
  }

  // Initial prompt state
  return (
    <div className="flex flex-col items-center justify-center p-6 text-center max-w-sm mx-auto space-y-5">
      <div className="w-16 h-16 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center shrink-0">
        <Camera className="w-8 h-8" />
      </div>

      <div className="space-y-2">
        <h3 className="text-lg font-bold text-white tracking-tight">
          Escanear Código de Barras
        </h3>
        <p className="text-xs sm:text-sm text-slate-400 leading-relaxed">
          Permita el acceso a la cámara para apuntar a los códigos de barras (EAN-13, CODE-128, QR) de los artículos en las estanterías del depósito.
        </p>
      </div>

      {status === "requesting" ? (
        <div className="flex items-center gap-2 text-blue-400 text-sm font-medium py-2">
          <RefreshCw className="w-5 h-5 animate-spin" />
          <span>Solicitando permiso al navegador...</span>
        </div>
      ) : (
        <div className="flex flex-col sm:flex-row items-center gap-3 w-full pt-2">
          <button
            type="button"
            onClick={onRequestPermission}
            className="w-full sm:flex-1 h-12 rounded-xl bg-blue-600 hover:bg-blue-500 active:scale-95 text-white font-semibold text-sm flex items-center justify-center gap-2 transition cursor-pointer shadow-lg shadow-blue-500/20"
          >
            <Camera className="w-4 h-4" />
            <span>Activar Cámara</span>
          </button>
          <button
            type="button"
            onClick={onCancel}
            className="w-full sm:flex-1 h-12 rounded-xl bg-slate-800 hover:bg-slate-700 active:scale-95 text-slate-300 font-semibold text-sm flex items-center justify-center gap-2 transition cursor-pointer border border-slate-700"
          >
            <span>Cancelar</span>
          </button>
        </div>
      )}
    </div>
  );
}
