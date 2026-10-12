import React, { createContext, useContext, useMemo } from 'react';
import { MobileDataClientPort } from '../ports/MobileDataClientPort';
import { mockMobileDataClient } from '../adapters/mockMobileDataClient';
import { apiMobileDataClient } from '../adapters/apiMobileDataClient';
import { API_CONFIG } from '../utils/constants';

interface DataContextValue {
  client: MobileDataClientPort;
}

const DataContext = createContext<DataContextValue | null>(null);

export interface DataProviderProps {
  children: React.ReactNode;
  customClient?: MobileDataClientPort;
}

export const DataProvider: React.FC<DataProviderProps> = ({ children, customClient }) => {
  const defaultClient = API_CONFIG.USE_MOCK ? mockMobileDataClient : apiMobileDataClient;
  const value = useMemo<DataContextValue>(() => ({
    client: customClient || defaultClient,
  }), [customClient, defaultClient]);

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>;
};

export function useMobileDataClient(): MobileDataClientPort {
  const ctx = useContext(DataContext);
  if (!ctx) {
    throw new Error('useMobileDataClient must be used within a DataProvider');
  }
  return ctx.client;
}
