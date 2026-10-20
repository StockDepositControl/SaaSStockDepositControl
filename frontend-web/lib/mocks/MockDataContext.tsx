"use client";

import React, { createContext, useContext, useState, useMemo, useCallback } from "react";
import {
  UserRole,
  TipoAccion,
  ArticuloInternal,
  ArticuloPublicView,
  ArticuloAdminView,
  AuditEntry,
  AuditResult,
  DashboardKPIsBase,
  DashboardKPIsAdmin,
  MockUser,
} from "../types/domain";
import { DataClientPort } from "../ports/DataClientPort";
import {
  INITIAL_ARTICULOS_SEED,
  INITIAL_AUDIT_LOGS_SEED,
  MOCK_USERS_SEED,
} from "./seed-data";
import { DataContext } from "../context/DataContext";

/**
 * Strips confidential financial fields strictly at the data layer
 * for any role other than ADMINISTRADOR.
 */
function projectArticleForRole(
  article: ArticuloInternal,
  role: UserRole
): ArticuloPublicView | ArticuloAdminView {
  if (role === UserRole.ADMINISTRADOR) {
    return { ...article };
  }

  // Non-admin roles: structurally omit pcio_com_siva
  const { pcio_com_siva: _omitted, ...publicView } = article;
  return publicView as ArticuloPublicView;
}

function calculateKPIs(
  articles: ArticuloInternal[],
  auditLogs: AuditResult[],
  role: UserRole
): DashboardKPIsBase | DashboardKPIsAdmin {
  const totalArticulos = articles.length;
  const auditados = articles.filter((a) => a.fue_auditado).length;
  const pendientes = Math.max(0, totalArticulos - auditados);
  const porcentajeAvance =
    totalArticulos > 0 ? Math.round((auditados / totalArticulos) * 100) : 0;

  const discrepanciasAlta = auditLogs.filter(
    (log) => log.tipo_accion === TipoAccion.ALTA
  ).length;
  const discrepanciasBaja = auditLogs.filter(
    (log) => log.tipo_accion === TipoAccion.BAJA
  ).length;
  const sinAccion = auditLogs.filter(
    (log) => log.tipo_accion === TipoAccion.SIN_ACCION
  ).length;

  const outOfStockCount = articles.filter((a) =>
    a.lotes && a.lotes.length > 0
      ? a.lotes.reduce((sum, l) => sum + l.stock_real, 0) === 0
      : a.stock_real === 0
  ).length;

  const baseKPIs: DashboardKPIsBase = {
    totalArticulos,
    auditados,
    pendientes,
    porcentajeAvance,
    discrepanciasAlta,
    discrepanciasBaja,
    sinAccion,
    outOfStockCount,
  };

  if (role === UserRole.ADMINISTRADOR) {
    const montoValorizadoAlta = auditLogs
      .filter((log) => log.tipo_accion === TipoAccion.ALTA)
      .reduce((sum, log) => sum + log.monto_valorizado, 0);

    const montoValorizadoBaja = auditLogs
      .filter((log) => log.tipo_accion === TipoAccion.BAJA)
      .reduce((sum, log) => sum + log.monto_valorizado, 0);

    const montoValorizadoTotal = auditLogs.reduce(
      (sum, log) => sum + log.monto_valorizado,
      0
    );

    const adminKPIs: DashboardKPIsAdmin = {
      ...baseKPIs,
      montoValorizadoTotal: Math.round(montoValorizadoTotal * 100) / 100,
      montoValorizadoAlta: Math.round(montoValorizadoAlta * 100) / 100,
      montoValorizadoBaja: Math.round(montoValorizadoBaja * 100) / 100,
    };
    return adminKPIs;
  }

  return baseKPIs;
}

interface MockDataContextType {
  client: DataClientPort;
  currentUser: MockUser | null;
  currentRole: UserRole | null;
  users: MockUser[];
  setRole: (role: UserRole) => void;
  switchUser: (userId: string) => void;
  login: (email: string, password?: string) => Promise<MockUser>;
  logout: () => void;
  articles: (ArticuloPublicView | ArticuloAdminView)[];
}

export const MockDataContext = createContext<MockDataContextType | null>(null);

export interface MockDataProviderProps {
  children: React.ReactNode;
  initialRole?: UserRole;
}

export function MockDataProvider({
  children,
  initialRole,
}: MockDataProviderProps) {
  const [users] = useState<MockUser[]>(MOCK_USERS_SEED);
  const [currentUser, setCurrentUser] = useState<MockUser | null>(null);
  const [currentRole, setCurrentRole] = useState<UserRole | null>(null);

  const [articles, setArticles] = useState<ArticuloInternal[]>(INITIAL_ARTICULOS_SEED);
  const [auditLogs, setAuditLogs] = useState<AuditResult[]>(INITIAL_AUDIT_LOGS_SEED);

  const switchUser = useCallback(
    (userId: string) => {
      const found = users.find((u) => u.id === userId);
      if (found) {
        setCurrentUser(found);
        setCurrentRole(found.role);
      }
    },
    [users]
  );

  const login = useCallback(
    async (email: string, _password?: string): Promise<MockUser> => {
      const found = users.find(
        (u) => u.email.toLowerCase().trim() === email.toLowerCase().trim()
      );
      if (!found) {
        throw new Error(`Credenciales incorrectas: usuario '${email}' no encontrado.`);
      }
      setCurrentUser(found);
      setCurrentRole(found.role);
      return found;
    },
    [users]
  );

  const logout = useCallback(() => {
    setCurrentUser(null);
    setCurrentRole(null);
  }, []);

  const getUsers = useCallback(async (): Promise<MockUser[]> => {
    return users;
  }, [users]);

  const getCurrentUser = useCallback(async (): Promise<MockUser | null> => {
    return currentUser;
  }, [currentUser]);

  const getArticulos = useCallback(
    async (role?: UserRole): Promise<ArticuloPublicView[] | ArticuloAdminView[]> => {
      const activeRole = role ?? currentRole ?? UserRole.AUDITOR;
      return articles.map((art) => projectArticleForRole(art, activeRole));
    },
    [articles, currentRole]
  );

  const getArticuloByBarcode = useCallback(
    async (
      barcodeOrId: string,
      role?: UserRole
    ): Promise<ArticuloPublicView | ArticuloAdminView | null> => {
      const activeRole = role ?? currentRole ?? UserRole.AUDITOR;
      const cleanTerm = barcodeOrId.trim();
      const match = articles.find(
        (a) =>
          a.id_articulo === cleanTerm ||
          a.cod_barras.some((cb) => cb === cleanTerm)
      );

      if (!match) return null;
      return projectArticleForRole(match, activeRole);
    },
    [articles, currentRole]
  );

  const searchArticulos = useCallback(
    async (
      query: string,
      role?: UserRole
    ): Promise<(ArticuloPublicView | ArticuloAdminView)[]> => {
      const activeRole = role ?? currentRole ?? UserRole.AUDITOR;
      const cleanTerm = query.trim().toLowerCase();
      if (!cleanTerm) return [];

      const matches = articles
        .filter((a) => {
          const matchName = a.des_articulo.toLowerCase().includes(cleanTerm);
          const matchId = a.id_articulo.toLowerCase().includes(cleanTerm);
          const matchBarcode = a.cod_barras.some((cb) =>
            cb.toLowerCase().includes(cleanTerm)
          );
          const matchBrand = (a.des_marca || "").toLowerCase().includes(cleanTerm);
          return matchName || matchId || matchBarcode || matchBrand;
        })
        .sort((a, b) => {
          // Surface pending articles first for faster audit workflow
          if (a.fue_auditado === b.fue_auditado) return 0;
          return a.fue_auditado ? 1 : -1;
        })
        .slice(0, 8);

      return matches.map((art) => projectArticleForRole(art, activeRole));
    },
    [articles, currentRole]
  );

  const registerAudit = useCallback(
    async (entry: AuditEntry): Promise<AuditResult> => {
      const target = articles.find(
        (a) =>
          a.id_articulo === entry.id_articulo ||
          a.cod_barras.includes(entry.id_articulo)
      );

      if (!target) {
        throw new Error(`Artículo con identificador '${entry.id_articulo}' no encontrado.`);
      }

      const delta = entry.stock_fisico_contado - target.stock_real;
      let tipoAccion: TipoAccion = TipoAccion.SIN_ACCION;
      if (delta > 0) tipoAccion = TipoAccion.ALTA;
      else if (delta < 0) tipoAccion = TipoAccion.BAJA;

      const cantidadAfectada = Math.abs(delta);

      // VAT logic replicated from domain AuditService:
      // Medicamentos = 0.00 VAT rate, other families = 0.21
      const isMedicamento =
        (target.des_familia || "").trim().toLowerCase() === "medicamentos";
      const appliedVatRate = isMedicamento ? 0.0 : 0.21;
      const unitCostWithVat = target.pcio_com_siva * (1 + appliedVatRate);
      const montoValorizado = Math.round(unitCostWithVat * cantidadAfectada * 100) / 100;

      const newAuditResult: AuditResult = {
        client_uuid: `uuid-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
        audit_id: auditLogs.length + 1,
        id_articulo: target.id_articulo,
        des_articulo: target.des_articulo,
        stock_real: target.stock_real,
        stock_fisico_contado: entry.stock_fisico_contado,
        delta_stock: delta,
        tipo_accion: tipoAccion,
        cantidad_afectada: cantidadAfectada,
        audit_quantity: entry.stock_fisico_contado,
        monto_valorizado: montoValorizado,
        applied_vat_rate: appliedVatRate,
        lote: entry.lote || target.lotes[0]?.lote,
        observation: entry.observation,
        scan_timestamp: new Date().toISOString(),
      };

      // Mutate state in memory
      setArticles((prev) =>
        prev.map((art) => {
          if (art.id_articulo === target.id_articulo) {
            return {
              ...art,
              fue_auditado: true,
              ultimo_conteo_fisico: entry.stock_fisico_contado,
              stock_real: entry.stock_fisico_contado,
            };
          }
          return art;
        })
      );

      setAuditLogs((prev) => [newAuditResult, ...prev]);

      return newAuditResult;
    },
    [articles, auditLogs.length]
  );

  const getKPIs = useCallback(
    async (role?: UserRole): Promise<DashboardKPIsBase | DashboardKPIsAdmin> => {
      const activeRole = role ?? currentRole ?? UserRole.AUDITOR;
      return calculateKPIs(articles, auditLogs, activeRole);
    },
    [articles, auditLogs, currentRole]
  );

  const getAuditLog = useCallback(async (): Promise<AuditResult[]> => {
    return auditLogs;
  }, [auditLogs]);

  const getCurrentRole = useCallback((): UserRole => {
    return currentRole ?? UserRole.AUDITOR;
  }, [currentRole]);

  const setRole = useCallback((newRole: UserRole): void => {
    setCurrentRole(newRole);
    // Also adjust current user if current user role does not match
    const matchingUser = users.find((u) => u.role === newRole);
    if (matchingUser) {
      setCurrentUser(matchingUser);
    }
  }, [users]);

  const resetData = useCallback((): void => {
    setArticles(INITIAL_ARTICULOS_SEED);
    setAuditLogs(INITIAL_AUDIT_LOGS_SEED);
  }, []);

  const client: DataClientPort = useMemo(
    () => ({
      getArticulos,
      getArticuloByBarcode,
      searchArticulos,
      registerAudit,
      getKPIs,
      getAuditLog,
      getCurrentRole,
      setRole,
      getUsers,
      getCurrentUser,
      login,
      switchUser,
      logout,
      resetData,
    }),
    [
      getArticulos,
      getArticuloByBarcode,
      searchArticulos,
      registerAudit,
      getKPIs,
      getAuditLog,
      getCurrentRole,
      setRole,
      getUsers,
      getCurrentUser,
      login,
      switchUser,
      logout,
      resetData,
    ]
  );

  const activeArticles = useMemo(
    () => articles.map((art) => projectArticleForRole(art, currentRole ?? UserRole.AUDITOR)),
    [articles, currentRole]
  );

  const contextValue: MockDataContextType = useMemo(
    () => ({
      client,
      currentUser,
      currentRole,
      users,
      setRole,
      switchUser,
      login,
      logout,
      articles: activeArticles,
    }),
    [
      client,
      currentUser,
      currentRole,
      users,
      setRole,
      switchUser,
      login,
      logout,
      activeArticles,
    ]
  );

  return (
    <DataContext.Provider value={contextValue}>
      <MockDataContext.Provider value={contextValue}>
        {children}
      </MockDataContext.Provider>
    </DataContext.Provider>
  );
}

export function useMockDataContext(): MockDataContextType {
  const context = useContext(MockDataContext);
  if (!context) {
    throw new Error("useMockDataContext must be used within a MockDataProvider");
  }
  return context;
}

