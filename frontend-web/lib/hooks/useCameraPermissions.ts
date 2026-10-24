"use client";

import { useState, useCallback, useEffect } from "react";

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

// Time given to the OS / camera HAL (e.g. Samsung Camera2) to release the
// sensor lock after the probe stream is stopped, before the scanner re-acquires it.
export const PERMISSION_RELEASE_DELAY_MS = 150;

// Non-destructive permission lookup. Returns null when the Permissions API
// is unavailable or does not support the "camera" name (e.g. older Firefox/Safari).
async function queryCameraPermission(): Promise<PermissionState | null> {
  if (
    typeof navigator === "undefined" ||
    !navigator.permissions ||
    typeof navigator.permissions.query !== "function"
  ) {
    return null;
  }

  try {
    const result = await navigator.permissions.query({
      name: "camera" as PermissionName,
    });
    return result.state;
  } catch {
    return null;
  }
}

function wait(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function useCameraPermissions(): UseCameraPermissionsResult {
  const [status, setStatus] = useState<CameraPermissionStatus>("idle");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Silent check on mount: skip the permission prompt entirely when already granted
  useEffect(() => {
    let isCancelled = false;

    queryCameraPermission().then((state) => {
      if (!isCancelled && state === "granted") {
        setStatus((prev) => (prev === "idle" ? "granted" : prev));
      }
    });

    return () => {
      isCancelled = true;
    };
  }, []);

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

    // 3. Fast path: already granted, no need to touch the camera hardware
    if ((await queryCameraPermission()) === "granted") {
      setStatus("granted");
      return true;
    }

    try {
      const testStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
      });

      // Immediately stop all tracks to avoid leaving hardware open
      testStream.getTracks().forEach((track) => track.stop());

      // Let the driver release the sensor lock before the scanner re-acquires it
      await wait(PERMISSION_RELEASE_DELAY_MS);

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
