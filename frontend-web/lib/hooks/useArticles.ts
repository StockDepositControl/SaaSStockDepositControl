"use client";

import { useState, useEffect, useCallback } from "react";
import { useDataClient } from "@/lib/hooks/useDataClient";
import { ArticuloPublicView, ArticuloAdminView, UserRole } from "@/lib/types/domain";
import type { DataClientPort } from "@/lib/ports/DataClientPort";
import type { MockUser } from "@/lib/types/domain";

export interface UseArticlesReturn {
  articles: (ArticuloPublicView | ArticuloAdminView)[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

interface SettledResult {
  client: DataClientPort;
  currentUser: MockUser;
  currentRole: UserRole | null;
  tick: number;
  articles: (ArticuloPublicView | ArticuloAdminView)[];
  error: string | null;
}

export function useArticles(): UseArticlesReturn {
  const { client, currentRole, currentUser } = useDataClient();
  const [tick, setTick] = useState(0);
  const [settled, setSettled] = useState<SettledResult | null>(null);

  useEffect(() => {
    // Boundary guard: never fetch if not authenticated
    if (!currentUser) return;

    let cancelled = false;
    client
      .getArticulos(currentRole || UserRole.AUDITOR)
      .then((articles) => {
        if (!cancelled) {
          setSettled({ client, currentUser, currentRole, tick, articles, error: null });
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const msg = err instanceof Error ? err.message : "Error cargando artículos del catálogo";
          setSettled({ client, currentUser, currentRole, tick, articles: [], error: msg });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [client, currentRole, currentUser, tick]);

  const refetch = useCallback(async () => {
    setTick((t) => t + 1);
  }, []);

  if (!currentUser) {
    return { articles: [], isLoading: false, error: null, refetch };
  }

  const isCurrent =
    settled !== null &&
    settled.client === client &&
    settled.currentUser === currentUser &&
    settled.currentRole === currentRole &&
    settled.tick === tick;

  // Never expose data fetched for another user/role (field-level RBAC safety).
  const sameIdentity =
    settled !== null && settled.currentUser === currentUser && settled.currentRole === currentRole;

  return {
    articles: sameIdentity ? settled.articles : [],
    isLoading: !isCurrent,
    error: sameIdentity ? settled.error : null,
    refetch,
  };
}
