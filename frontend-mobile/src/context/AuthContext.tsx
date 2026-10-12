import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { ActiveTenantSession, LoginCredentials } from '../types/auth';
import { useMobileDataClient } from './DataContext';

interface AuthContextValue {
  session: ActiveTenantSession | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  loginError: string | null;
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const client = useMobileDataClient();
  const [session, setSession] = useState<ActiveTenantSession | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [loginError, setLoginError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function restore() {
      try {
        const restored = await client.restoreSession();
        if (isMounted) {
          setSession(restored);
        }
      } catch (err) {
        // Ignored
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }
    restore();
    return () => {
      isMounted = false;
    };
  }, [client]);

  const login = useCallback(
    async (credentials: LoginCredentials) => {
      setIsLoading(true);
      setLoginError(null);
      try {
        const active = await client.login(credentials);
        setSession(active);
      } catch (err) {
        const msg = err instanceof Error ? err.message : 'Error al iniciar sesión.';
        setLoginError(msg);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [client]
  );

  const logout = useCallback(async () => {
    setIsLoading(true);
    try {
      await client.logout();
      setSession(null);
      setLoginError(null);
    } finally {
      setIsLoading(false);
    }
  }, [client]);

  const clearError = useCallback(() => {
    setLoginError(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        session,
        isAuthenticated: !!session,
        isLoading,
        loginError,
        login,
        logout,
        clearError,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}
