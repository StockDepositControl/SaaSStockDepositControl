"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import { DataContext, DataContextValue } from "./DataContext";
import { DataClientPort } from "../ports/DataClientPort";
import { ApiDataClient } from "../adapters/ApiDataClient";
import {
  UserRole,
  ArticuloPublicView,
  ArticuloAdminView,
  AuditResult,
  DashboardKPIsBase,
  DashboardKPIsAdmin,
  MockUser,
  AuditEntry,
} from "../types/domain";

const defaultKPIs: DashboardKPIsBase = {
  totalArticulos: 0,
  auditados: 0,
  pendientes: 0,
  porcentajeAvance: 0,
  discrepanciasAlta: 0,
  discrepanciasBaja: 0,
  sinAccion: 0,
};

export interface ApiDataProviderProps {
  children: React.ReactNode;
}

export function ApiDataProvider({ children }: ApiDataProviderProps) {
  const client = useMemo(() => new ApiDataClient(), []);

  const [currentUser, setCurrentUser] = useState<MockUser | null>(null);
  const [currentRole, setCurrentRole] = useState<UserRole | null>(null);
  const [articles, setArticles] = useState<(ArticuloPublicView | ArticuloAdminView)[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditResult[]>([]);
  const [kpis, setKpis] = useState<DashboardKPIsBase | DashboardKPIsAdmin>(defaultKPIs);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchBackendData = useCallback(
    async (role: UserRole) => {
      setIsLoading(true);
      setError(null);
      try {
        const [loadedArticles, loadedKpis, loadedLogs] = await Promise.all([
          client.getArticulos(role).catch((e) => {
            console.error("Error fetching articles:", e);
            return [];
          }),
          client.getKPIs(role).catch((e) => {
            console.error("Error fetching KPIs:", e);
            return defaultKPIs;
          }),
          client.getAuditLog().catch((e) => {
            console.error("Error fetching audit logs:", e);
            return [];
          }),
        ]);

        setArticles(loadedArticles);
        setKpis(loadedKpis);
        setAuditLogs(loadedLogs);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Error loading backend data";
        setError(msg);
      } finally {
        setIsLoading(false);
      }
    },
    [client]
  );

  // Initialize session from stored token on mount
  useEffect(() => {
    client.getCurrentUser().then((user) => {
      if (user) {
        setCurrentUser(user);
        setCurrentRole(user.role);
        fetchBackendData(user.role);
      } else {
        setIsLoading(false);
      }
    });
  }, [client, fetchBackendData]);

  const login = useCallback(
    async (email: string, password?: string): Promise<MockUser> => {
      setIsLoading(true);
      setError(null);
      try {
        const user = await client.login(email, password);
        setCurrentUser(user);
        setCurrentRole(user.role);
        await fetchBackendData(user.role);
        return user;
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Failed to authenticate";
        setError(msg);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [client, fetchBackendData]
  );

  const logout = useCallback(() => {
    client.logout();
    setCurrentUser(null);
    setCurrentRole(null);
    setArticles([]);
    setAuditLogs([]);
    setKpis(defaultKPIs);
    if (typeof window !== "undefined") {
      window.location.href = "/login";
    }
  }, [client]);

  const setRole = useCallback(
    (role: UserRole) => {
      client.setRole(role);
      setCurrentRole(role);
    },
    [client]
  );

  const switchUser = useCallback(
    (userId: string) => {
      client.switchUser(userId);
    },
    [client]
  );

  const wrappedClient: DataClientPort = useMemo(() => {
    return {
      getArticulos: (role) => client.getArticulos(role),
      getArticuloByBarcode: (barcode, role) => client.getArticuloByBarcode(barcode, role),
      searchArticulos: (query, role) => client.searchArticulos(query, role),
      registerAudit: async (entry: AuditEntry): Promise<AuditResult> => {
        const result = await client.registerAudit(entry);
        if (currentRole) {
          await fetchBackendData(currentRole);
        }
        return result;
      },
      getKPIs: (role) => client.getKPIs(role),
      getAuditLog: () => client.getAuditLog(),
      getCurrentRole: () => client.getCurrentRole(),
      setRole: (role) => client.setRole(role),
      getUsers: () => client.getUsers(),
      getCurrentUser: () => client.getCurrentUser(),
      login: (email, password) => client.login(email, password),
      switchUser: (id) => client.switchUser(id),
      logout: () => client.logout(),
      resetData: () => client.resetData(),
    };
  }, [client, currentRole, fetchBackendData]);

  const refreshData = useCallback(async () => {
    if (currentRole) {
      await fetchBackendData(currentRole);
    }
  }, [currentRole, fetchBackendData]);

  const contextValue: DataContextValue = useMemo(
    () => ({
      client: wrappedClient,
      currentUser,
      currentRole,
      users: currentUser ? [currentUser] : [],
      setRole,
      switchUser,
      login,
      logout,
      articles,
      auditLogs,
      kpis,
      isLoading,
      error,
      refreshData,
    }),
    [
      wrappedClient,
      currentUser,
      currentRole,
      setRole,
      switchUser,
      login,
      logout,
      articles,
      auditLogs,
      kpis,
      isLoading,
      error,
      refreshData,
    ]
  );

  return (
    <DataContext.Provider value={contextValue}>
      {children}
    </DataContext.Provider>
  );
}
