"use client";

import { useDataContext } from "../context/DataContext";
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
  isLoading?: boolean;
  error?: string | null;
  refreshData?: () => Promise<void>;
}

/**
 * Primary hook to interact with the domain data port.
 * UI components consume this hook rather than directly importing mock stores or fetch adapters.
 */
export function useDataClient(): UseDataClientReturn {
  const context = useDataContext();

  return {
    client: context.client,
    currentUser: context.currentUser,
    currentRole: context.currentRole,
    users: context.users,
    setRole: context.setRole,
    switchUser: context.switchUser,
    login: context.login,
    logout: context.logout,
    articles: context.articles,
    auditLogs: context.auditLogs,
    kpis: context.kpis,
    isLoading: context.isLoading,
    error: context.error,
    refreshData: context.refreshData,
  };
}
