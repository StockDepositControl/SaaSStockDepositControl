"use client";

import React, { useState, useEffect, useCallback, useMemo } from "react";
import { DataContext, DataContextValue } from "./DataContext";
import { DataClientPort } from "../ports/DataClientPort";
import { ApiDataClient } from "../adapters/ApiDataClient";
import {
  UserRole,
  AuditResult,
  MockUser,
  AuditEntry,
} from "../types/domain";

export interface ApiDataProviderProps {
  children: React.ReactNode;
}

export function ApiDataProvider({ children }: ApiDataProviderProps) {
  const client = useMemo(() => new ApiDataClient(), []);

  const [currentUser, setCurrentUser] = useState<MockUser | null>(null);
  const [currentRole, setCurrentRole] = useState<UserRole | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize session from stored token on mount (zero prefetch for domain data)
  useEffect(() => {
    client.getCurrentUser().then((user) => {
      if (user) {
        setCurrentUser(user);
        setCurrentRole(user.role);
      }
      setIsLoading(false);
    });
  }, [client]);

  const login = useCallback(
    async (email: string, password?: string): Promise<MockUser> => {
      setIsLoading(true);
      setError(null);
      try {
        const user = await client.login(email, password);
        setCurrentUser(user);
        setCurrentRole(user.role);
        return user;
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Failed to authenticate";
        setError(msg);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [client]
  );

  const logout = useCallback(() => {
    client.logout();
    setCurrentUser(null);
    setCurrentRole(null);
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
        return await client.registerAudit(entry);
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
  }, [client]);

  const refreshData = useCallback(async () => {
    // Zero-prefetch architecture: individual domain hooks handle their own refresh
  }, []);

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
