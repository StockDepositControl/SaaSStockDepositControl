"use client";

import { createContext, useContext } from "react";
import { DataClientPort } from "../ports/DataClientPort";
import {
  UserRole,
  MockUser,
} from "../types/domain";

export interface DataContextValue {
  client: DataClientPort;
  currentUser: MockUser | null;
  currentRole: UserRole | null;
  users: MockUser[];
  setRole: (role: UserRole) => void;
  switchUser: (userId: string) => void;
  login: (email: string, password?: string) => Promise<MockUser>;
  logout: () => void;
  isLoading?: boolean;
  error?: string | null;
  refreshData?: () => Promise<void>;
}

export const DataContext = createContext<DataContextValue | null>(null);

export function useDataContext(): DataContextValue {
  const context = useContext(DataContext);
  if (!context) {
    throw new Error("useDataContext must be used within a DataProvider (ApiDataProvider or MockDataProvider)");
  }
  return context;
}
