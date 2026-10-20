"use client";

import { useState, useEffect, useCallback } from "react";
import { useDataClient } from "@/lib/hooks/useDataClient";
import {
  DashboardKPIsBase,
  DashboardKPIsAdmin,
  UserRole,
} from "@/lib/types/domain";
import type { DataClientPort } from "@/lib/ports/DataClientPort";
import type { MockUser } from "@/lib/types/domain";

export const defaultKPIs: DashboardKPIsBase = {
  totalArticulos: 0,
  auditados: 0,
  pendientes: 0,
  porcentajeAvance: 0,
  discrepanciasAlta: 0,
  discrepanciasBaja: 0,
  sinAccion: 0,
};

export interface UseKPIsReturn {
  kpis: DashboardKPIsBase | DashboardKPIsAdmin;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

interface SettledKPIsResult {
  client: DataClientPort;
  currentUser: MockUser;
  currentRole: UserRole | null;
  tick: number;
  kpis: DashboardKPIsBase | DashboardKPIsAdmin;
  error: string | null;
}

export function useKPIs(overrideRole?: UserRole): UseKPIsReturn {
  const { client, currentRole, currentUser } = useDataClient();
  const [tick, setTick] = useState(0);
  const [settled, setSettled] = useState<SettledKPIsResult | null>(null);

  const effectiveRole = overrideRole ?? currentRole ?? UserRole.AUDITOR;

  useEffect(() => {
    // 🛑 Boundary Guard: Never fetch if not authenticated
    if (!currentUser) return;

    let cancelled = false;
    client
      .getKPIs(effectiveRole)
      .then((kpis) => {
        if (!cancelled) {
          setSettled({
            client,
            currentUser,
            currentRole: effectiveRole,
            tick,
            kpis,
            error: null,
          });
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const msg =
            err instanceof Error ? err.message : "Error cargando KPIs del dashboard";
          setSettled({
            client,
            currentUser,
            currentRole: effectiveRole,
            tick,
            kpis: defaultKPIs,
            error: msg,
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [client, effectiveRole, currentUser, tick]);

  const refetch = useCallback(async () => {
    setTick((t) => t + 1);
  }, []);

  if (!currentUser) {
    return { kpis: defaultKPIs, isLoading: false, error: null, refetch };
  }

  const isCurrent =
    settled !== null &&
    settled.client === client &&
    settled.currentUser === currentUser &&
    settled.currentRole === effectiveRole &&
    settled.tick === tick;

  // RBAC safety check: Never expose KPIs calculated for a different role or session
  const sameIdentity =
    settled !== null &&
    settled.currentUser === currentUser &&
    settled.currentRole === effectiveRole;

  return {
    kpis: sameIdentity ? settled.kpis : defaultKPIs,
    isLoading: !isCurrent,
    error: sameIdentity ? settled.error : null,
    refetch,
  };
}
