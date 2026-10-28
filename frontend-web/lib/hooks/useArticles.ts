"use client";

import { useState, useEffect, useCallback } from "react";
import { useDataClient } from "@/lib/hooks/useDataClient";
import {
  ArticuloPublicView,
  ArticuloAdminView,
  UserRole,
  type ArticleCatalogQuery,
  type ArticleFamily,
} from "@/lib/types/domain";
import type { DataClientPort } from "@/lib/ports/DataClientPort";
import type { MockUser } from "@/lib/types/domain";

export const SEARCH_DEBOUNCE_MS = 250;
const DEFAULT_PAGE_LIMIT = 10;

export interface UseArticlesOptions {
  /** Opt-in server-side pagination; without it the full list is loaded (legacy callers). */
  paginated?: boolean;
  limit?: number;
}

export interface UseArticlesReturn {
  articles: (ArticuloPublicView | ArticuloAdminView)[];
  total: number;
  page: number;
  limit: number;
  pages: number;
  families: ArticleFamily[];
  search: string;
  idFamilia: string | undefined;
  status: boolean | undefined;
  setPage: (page: number) => void;
  setSearch: (term: string) => void;
  setFamily: (idFamilia: string | undefined) => void;
  setStatus: (status: boolean | undefined) => void;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

interface SettledResult {
  client: DataClientPort;
  currentUser: MockUser;
  currentRole: UserRole | null;
  tick: number;
  queryKey: string;
  articles: (ArticuloPublicView | ArticuloAdminView)[];
  total: number;
  pages: number;
  error: string | null;
}

interface SettledFamilies {
  client: DataClientPort;
  currentUser: MockUser;
  families: ArticleFamily[];
}

function buildQuery(
  page: number,
  limit: number,
  search: string,
  idFamilia: string | undefined,
  status: boolean | undefined
): ArticleCatalogQuery {
  const query: ArticleCatalogQuery = { page, limit };
  if (search) query.search = search;
  if (idFamilia) query.id_familia = idFamilia;
  if (status !== undefined) query.fue_auditado = status;
  return query;
}

export function useArticles(options: UseArticlesOptions = {}): UseArticlesReturn {
  const paginated = options.paginated ?? false;
  const limit = options.limit ?? DEFAULT_PAGE_LIMIT;
  const { client, currentRole, currentUser } = useDataClient();
  const [tick, setTick] = useState(0);
  const [settled, setSettled] = useState<SettledResult | null>(null);
  const [settledFamilies, setSettledFamilies] = useState<SettledFamilies | null>(null);
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [idFamilia, setIdFamilia] = useState<string | undefined>(undefined);
  const [status, setStatusState] = useState<boolean | undefined>(undefined);

  const queryKey = paginated
    ? JSON.stringify(buildQuery(page, limit, debouncedSearch, idFamilia, status))
    : "all";

  // Commit the search term only after the user stops typing; page resets in the same batch.
  useEffect(() => {
    if (!paginated) return;
    const term = searchInput.trim();
    if (term === debouncedSearch) return;
    const timer = setTimeout(() => {
      setDebouncedSearch(term);
      setPage(1);
    }, SEARCH_DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [paginated, searchInput, debouncedSearch]);

  useEffect(() => {
    // Boundary guard: never fetch if not authenticated
    if (!currentUser) return;

    // Superseded queries flip `cancelled`, so late responses never overwrite current state.
    let cancelled = false;
    const role = currentRole || UserRole.AUDITOR;
    const request = paginated
      ? client.getPaginatedArticles(JSON.parse(queryKey) as ArticleCatalogQuery, role)
      : client.getArticulos(role).then((items) => ({ items, total: items.length, pages: 1 }));

    request
      .then(({ items, total, pages }) => {
        if (!cancelled) {
          setSettled({
            client,
            currentUser,
            currentRole,
            tick,
            queryKey,
            articles: items,
            total,
            pages,
            error: null,
          });
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          const msg = err instanceof Error ? err.message : "Error cargando artículos del catálogo";
          setSettled({
            client,
            currentUser,
            currentRole,
            tick,
            queryKey,
            articles: [],
            total: 0,
            pages: 0,
            error: msg,
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [client, currentRole, currentUser, tick, paginated, queryKey]);

  useEffect(() => {
    if (!paginated || !currentUser) return;

    let cancelled = false;
    client
      .getFamilies()
      .then((families) => {
        if (!cancelled) setSettledFamilies({ client, currentUser, families });
      })
      .catch(() => {
        // Graceful degradation: the family filter stays empty, the catalog keeps working.
        if (!cancelled) setSettledFamilies({ client, currentUser, families: [] });
      });

    return () => {
      cancelled = true;
    };
  }, [client, currentUser, paginated]);

  const refetch = useCallback(async () => {
    setTick((t) => t + 1);
  }, []);

  const setFamily = useCallback((id: string | undefined) => {
    setIdFamilia(id || undefined);
    setPage(1);
  }, []);

  const setStatus = useCallback((value: boolean | undefined) => {
    setStatusState(value);
    setPage(1);
  }, []);

  const controls = {
    search: searchInput,
    idFamilia,
    status,
    setPage,
    setSearch: setSearchInput,
    setFamily,
    setStatus,
    refetch,
  };

  if (!currentUser) {
    return {
      ...controls,
      articles: [],
      total: 0,
      page,
      limit,
      pages: 0,
      families: [],
      isLoading: false,
      error: null,
    };
  }

  const isCurrent =
    settled !== null &&
    settled.client === client &&
    settled.currentUser === currentUser &&
    settled.currentRole === currentRole &&
    settled.tick === tick &&
    settled.queryKey === queryKey;

  // Never expose data fetched for another user/role (field-level RBAC safety).
  const sameIdentity =
    settled !== null && settled.currentUser === currentUser && settled.currentRole === currentRole;

  const articles = sameIdentity ? settled.articles : [];
  const total = sameIdentity ? settled.total : 0;
  const families =
    settledFamilies !== null &&
    settledFamilies.client === client &&
    settledFamilies.currentUser === currentUser
      ? settledFamilies.families
      : [];

  return {
    ...controls,
    articles,
    total,
    page: paginated ? page : 1,
    limit: paginated ? limit : total,
    pages: sameIdentity ? (paginated ? settled.pages : total ? 1 : 0) : 0,
    families: paginated ? families : [],
    isLoading: !isCurrent,
    error: sameIdentity ? settled.error : null,
  };
}
