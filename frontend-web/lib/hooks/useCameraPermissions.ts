"use client";

import { useState, useCallback } from "react";

export type CameraPermissionStatus =
  | "idle"
  | "requesting"
  | "granted"
  | "denied"
  | "unsupported";

export interface UseCameraPermissionsResult {
  status: CameraPermissionStatus;
  errorMessage: string | null;
  requestPermission: () => Promise<boolean>;
  resetPermission: () => void;
}

export function useCameraPermissions(): UseCameraPermissionsResult {
  const [status, setStatus] = useState<CameraPermissionStatus>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const resetPermission = useCallback(() => {
    setStatus("idle");
    setErrorMessage(null);
  }, []);

  const requestPermission = useCallback(async (): Promise<boolean> => {
    if (typeof window === "undefined" || typeof navigator === "undefined") {
      setStatus("unsupported");
      setErrorMessage("Entorno de navegador no disponible.");
      return false;
    }

    // 1. Secure context check (camera requires HTTPS or localhost)
    const isLocalhost =
      typeof window.location !== "undefined" &&
      (window.location.hostname === "localhost" ||
        window.location.hostname === "127.0.0.1");

    if (!window.isSecureContext && !isLocalhost) {
      setStatus("unsupported");
      setErrorMessage(
        "El acceso a la cámara requiere una conexión segura HTTPS o localhost."
      );
      return false;
    }

    // 2. MediaDevices availability check
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      setStatus("unsupported");
      setErrorMessage(
        "Su navegador o dispositivo no soporta acceso a la cámara."
      );
      return false;
    }

    setStatus("requesting");
    setErrorMessage(null);

    try {
      const testStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment" },
      });

      // Immediately stop all tracks to avoid leaving hardware open
      testStream.getTracks().forEach((track) => track.stop());

      setStatus("granted");
      return true;
    } catch (err: unknown) {
      const error = err as { name?: string; message?: string };
      if (
        error.name === "NotAllowedError" ||
        error.name === "PermissionDeniedError"
      ) {
        setStatus("denied");
        setErrorMessage(
          "Permiso denegado. Active el acceso a la cámara en los permisos del navegador."
        );
      } else if (
        error.name === "NotFoundError" ||
        error.name === "DevicesNotFoundError"
      ) {
        setStatus("unsupported");
        setErrorMessage(
          "No se encontró ninguna cámara disponible en este dispositivo."
        );
      } else {
        setStatus("denied");
        setErrorMessage(
          error.message || "Error al solicitar acceso a la cámara."
        );
      }
      return false;
    }
  }, []);

  return {
    status,
    errorMessage,
    requestPermission,
    resetPermission,
  };
}
