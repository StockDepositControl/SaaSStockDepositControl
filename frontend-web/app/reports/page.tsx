"use client";

import React, { useState, useMemo, useEffect, useCallback } from "react";
import { useDataClient } from "@/lib/hooks/useDataClient";
import { DemoShell } from "@/components/layout/DemoShell";
import { UserRole } from "@/lib/types/domain";
import { AlertCircle, RefreshCw } from "lucide-react";
import { GlobalFilters } from "@/components/reportes/GlobalFilters";
import {
  ReportsTabNavigation,
  ReportTabId,
} from "@/components/reportes/ReportsTabNavigation";
import { ShrinkageReportTab } from "@/components/reportes/ShrinkageReportTab";
import { GoodsReceivedReportTab } from "@/components/reportes/GoodsReceivedReportTab";
import { NetInventoryBalanceTab } from "@/components/reportes/NetInventoryBalanceTab";
import { AuditHistoryTab } from "@/components/reportes/AuditHistoryTab";
import { ReportSkeleton } from "@/components/reportes/ReportSkeleton";
import { httpClient } from "@/lib/adapters/httpClient";
import {
  ApiShrinkageReportResponse,
  ApiGoodsReceivedReportResponse,
  ApiDailyInventoryBalanceResponse,
} from "@/lib/types/api";

function getDefaultDateRange() {
  const now = new Date();
  const past7Days = new Date();
  past7Days.setDate(now.getDate() - 7);

  return {
    startDate: past7Days.toISOString().split("T")[0],
    endDate: now.toISOString().split("T")[0],
  };
}

export default function ReportesPage() {
  const { currentRole, auditLogs, articles } = useDataClient();
  const isAdmin = currentRole === UserRole.ADMINISTRADOR;

  const defaultDates = useMemo(() => getDefaultDateRange(), []);
  const [startDate, setStartDate] = useState<string>(defaultDates.startDate);
  const [endDate, setEndDate] = useState<string>(defaultDates.endDate);
  const [activeTab, setActiveTab] = useState<ReportTabId>("shrinkage");
  const [isExporting, setIsExporting] = useState(false);

  // Backend direct reports state
  const [shrinkageReport, setShrinkageReport] = useState<ApiShrinkageReportResponse | null>(null);
  const [goodsReceivedReport, setGoodsReceivedReport] = useState<ApiGoodsReceivedReportResponse | null>(null);
  const [balanceReport, setBalanceReport] = useState<ApiDailyInventoryBalanceResponse | null>(null);
  const [isLoadingReports, setIsLoadingReports] = useState<boolean>(true);
  const [reportsError, setReportsError] = useState<string | null>(null);

  // Direct backend query function
  const fetchReports = useCallback(
    async (start: string, end: string) => {
      if (!isAdmin) return;
      setIsLoadingReports(true);
      setReportsError(null);

      try {
        const [shrinkage, goodsReceived, balance] = await Promise.all([
          httpClient
            .get<ApiShrinkageReportResponse>("/api/v1/reports/shrinkage", {
              params: { start_date: start, end_date: end },
            })
            .catch((err) => {
              console.warn("Direct backend call to /api/v1/reports/shrinkage failed:", err);
              return null;
            }),
          httpClient
            .get<ApiGoodsReceivedReportResponse>("/api/v1/reports/goods-received", {
              params: { start_date: start, end_date: end },
            })
            .catch((err) => {
              console.warn("Direct backend call to /api/v1/reports/goods-received failed:", err);
              return null;
            }),
          httpClient
            .get<ApiDailyInventoryBalanceResponse>("/api/v1/reports/inventory-balance", {
              params: { start_date: start, end_date: end },
            })
            .catch((err) => {
              console.warn("Direct backend call to /api/v1/reports/inventory-balance failed:", err);
              return null;
            }),
        ]);

        setShrinkageReport(shrinkage);
        setGoodsReceivedReport(goodsReceived);
        setBalanceReport(balance);

        if (!shrinkage && !goodsReceived && !balance) {
          setReportsError(
            "No se pudo conectar con los reportes consolidados del backend. Mostrando datos locales de auditoría como respaldo."
          );
        }
      } catch (err: unknown) {
        const msg =
          err instanceof Error
            ? err.message
            : "Error al consultar los reportes del backend";
        setReportsError(msg);
      } finally {
        setIsLoadingReports(false);
      }
    },
    [isAdmin]
  );

  // Trigger backend fetch on mount and whenever date filters change
  useEffect(() => {
    if (isAdmin && startDate && endDate) {
      fetchReports(startDate, endDate);
    }
  }, [isAdmin, startDate, endDate, fetchReports]);

  // Filter audit logs based on the date range (used for AuditHistoryTab and fallback)
  const filteredAuditLogs = useMemo(() => {
    if (!startDate && !endDate) return auditLogs;

    return auditLogs.filter((log) => {
      if (!log.scan_timestamp) return true;
      const logDate = log.scan_timestamp.split("T")[0];

      if (startDate && logDate < startDate) return false;
      if (endDate && logDate > endDate) return false;
      return true;
    });
  }, [auditLogs, startDate, endDate]);

  const handleExport = () => {
    setIsExporting(true);
    setTimeout(() => {
      let exportData: unknown = filteredAuditLogs;
      const filename = `reporte_${activeTab}_${startDate}_${endDate}.json`;

      if (activeTab === "shrinkage" && shrinkageReport) {
        exportData = shrinkageReport;
      } else if (activeTab === "goods_received" && goodsReceivedReport) {
        exportData = goodsReceivedReport;
      } else if (activeTab === "net_balance" && balanceReport) {
        exportData = balanceReport;
      }

      const dataStr =
        "data:text/json;charset=utf-8," +
        encodeURIComponent(JSON.stringify(exportData, null, 2));
      const downloadAnchor = document.createElement("a");
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", filename);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
      setIsExporting(false);
    }, 400);
  };

  const handleClearFilters = () => {
    setStartDate(defaultDates.startDate);
    setEndDate(defaultDates.endDate);
  };

  return (
    <DemoShell>
      <div className="max-w-7xl mx-auto space-y-6 pb-12">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
              Reportes y Métricas Financieras
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-1">
              Consolidación en tiempo real de valorizaciones, existencias, pérdidas y auditoría de stock
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-[#0F2C59]/10 text-[#0F2C59] border border-[#0F2C59]/20">
              Acceso Exclusivo Administrador
            </span>
          </div>
        </div>

        {isAdmin ? (
          <div className="space-y-6">
            {/* Sticky Global Date Filter & Export Button */}
            <GlobalFilters
              startDate={startDate}
              endDate={endDate}
              onStartDateChange={setStartDate}
              onEndDateChange={setEndDate}
              onExport={handleExport}
              isExporting={isExporting}
            />

            {/* Backend Connection Alert if Fallback is in use */}
            {reportsError && (
              <div className="flex items-center justify-between p-4 bg-amber-50 border border-amber-200 rounded-xl text-amber-800 text-xs sm:text-sm">
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 text-amber-600" />
                  <span>{reportsError}</span>
                </div>
                <button
                  type="button"
                  onClick={() => fetchReports(startDate, endDate)}
                  className="inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold bg-amber-100 hover:bg-amber-200 text-amber-900 rounded-lg transition-colors cursor-pointer"
                >
                  <RefreshCw className="w-3 h-3" />
                  Reintentar
                </button>
              </div>
            )}

            {/* Tab Navigation */}
            <ReportsTabNavigation
              activeTab={activeTab}
              onTabChange={setActiveTab}
            />

            {/* Active Tab Content or Loading Skeleton */}
            <div className="mt-6">
              {isLoadingReports ? (
                <ReportSkeleton />
              ) : (
                <>
                  {activeTab === "shrinkage" && (
                    <ShrinkageReportTab
                      auditLogs={filteredAuditLogs}
                      startDate={startDate}
                      endDate={endDate}
                      onClearFilters={handleClearFilters}
                      reportData={shrinkageReport}
                    />
                  )}

                  {activeTab === "goods_received" && (
                    <GoodsReceivedReportTab
                      auditLogs={filteredAuditLogs}
                      startDate={startDate}
                      endDate={endDate}
                      onClearFilters={handleClearFilters}
                      reportData={goodsReceivedReport}
                    />
                  )}

                  {activeTab === "net_balance" && (
                    <NetInventoryBalanceTab
                      articles={articles}
                      auditLogs={filteredAuditLogs}
                      startDate={startDate}
                      endDate={endDate}
                      onClearFilters={handleClearFilters}
                      reportData={balanceReport}
                    />
                  )}

                  {activeTab === "audit_history" && (
                    <AuditHistoryTab
                      auditLogs={filteredAuditLogs}
                      startDate={startDate}
                      endDate={endDate}
                      onClearFilters={handleClearFilters}
                    />
                  )}
                </>
              )}
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-20 px-6 bg-white rounded-2xl border border-slate-200 border-dashed text-center mt-6 shadow-sm">
            <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center text-slate-400 mb-4">
              <AlertCircle className="w-8 h-8 text-slate-400" />
            </div>
            <h2 className="text-xl font-bold text-slate-900 mb-2">Acceso Restringido</h2>
            <p className="text-sm text-slate-500 max-w-md mb-4">
              Su rol actual (<strong>{currentRole}</strong>) no tiene autorización para acceder a reportes financieros, valuación de costos ni balances de auditoría.
            </p>
            <p className="text-xs text-slate-400">
              Solicite permisos de Administrador para visualizar este módulo.
            </p>
          </div>
        )}
      </div>
    </DemoShell>
  );
}
