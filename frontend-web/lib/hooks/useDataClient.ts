"use client";

import { useMockDataContext } from "../mocks/MockDataContext";
import { DataClientPort } from "../ports/DataClientPort";
import {
  UserRole,
  ArticuloPublicView,
  ArticuloAdminView,
  AuditResult,
  DashboardKPIsBase,
  DashboardKPIsAdmin,
  MockUser,
} from "../types/domain";

export interface UseDataClientReturn {
  client: DataClientPort;
  currentUser: MockUser | null;
  currentRole: UserRole | null;
  users: MockUser[];
  setRole: (role: UserRole) => void;
  switchUser: (userId: string) => void;
  login: (email: string, password?: string) => Promise<MockUser>;
  logout: () => void;
  articles: (ArticuloPublicView | ArticuloAdminView)[];
  auditLogs: AuditResult[];
  kpis: DashboardKPIsBase | DashboardKPIsAdmin;
}

/**
 * Primary hook to interact with the domain data port.
 * UI components must consume this hook rather than directly importing mock stores or fetch adapters.
 */
export function useDataClient(): UseDataClientReturn {
  const {
    client,
    currentUser,
    currentRole,
    users,
    setRole,
    switchUser,
    login,
    logout,
    articles,
    auditLogs,
    kpis,
  } = useMockDataContext();

  return {
    client,
    currentUser,
    currentRole,
    users,
    setRole,
    switchUser,
    login,
    logout,
    articles,
    auditLogs,
    kpis,
  };
}

