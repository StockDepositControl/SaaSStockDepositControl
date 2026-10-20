"use client";

import { useState, useEffect, useCallback } from "react";
import { useDataClient } from "@/lib/hooks/useDataClient";
import { AuditResult } from "@/lib/types/domain";
import type { DataClientPort } from "@/lib/ports/DataClientPort";
import type { MockUser } from "@/lib/types/domain";

export interface UseAuditLogsReturn {
  auditLogs: AuditResult[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

interface SettledAuditLogsResult {
  client: DataClientPort;
  currentUser: MockUser;
  tick: number;
  auditLogs: AuditResult[];
  error: string | null;
}

export function useAuditLogs(): UseAuditLogsReturn {
  const { client, currentUser } = useDataClient();
  const [tick, setTick] = useState(0);
  const [settled, setSettled] = useState<SettledAuditLogsResult | null>(null);

  useEffect(() => {
    // 🛑 Boundary Guard: Never fetch if not authenticated
    if (!currentUser) return;

    let cancelled = false;
    client
      .getAuditLog()
      .then((auditLogs) => {
        if (!cancelled) {
          setSettled({
            client,
            currentUser,
            tick,
            auditLogs,
            error: null,
          });
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const msg =
            err instanceof Error ? err.message : "Error cargando registros de auditoría";
          setSettled({
            client,
            currentUser,
            tick,
            auditLogs: [],
            error: msg,
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [client, currentUser, tick]);

  const refetch = useCallback(async () => {
    setTick((t) => t + 1);
  }, []);

  if (!currentUser) {
    return { auditLogs: [], isLoading: false, error: null, refetch };
  }

  const isCurrent =
    settled !== null &&
    settled.client === client &&
    settled.currentUser === currentUser &&
    settled.tick === tick;

  const sameIdentity = settled !== null && settled.currentUser === currentUser;

  return {
    auditLogs: sameIdentity ? settled.auditLogs : [],
    isLoading: !isCurrent,
    error: sameIdentity ? settled.error : null,
    refetch,
  };
}
