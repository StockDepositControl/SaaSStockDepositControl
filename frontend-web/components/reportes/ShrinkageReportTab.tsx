"use client";

import React from "react";
import { AuditResult, TipoAccion } from "@/lib/types/domain";
import { SummaryKPICard } from "./SummaryKPICard";
import { EmptyState } from "./EmptyState";
import { AlertTriangle, TrendingDown, Layers, DollarSign } from "lucide-react";

import { ApiShrinkageReportResponse } from "@/lib/types/api";

export interface ShrinkageReportTabProps {
  auditLogs: AuditResult[];
  startDate?: string;
  endDate?: string;
  onClearFilters?: () => void;
  reportData?: ApiShrinkageReportResponse | null;
}

export function ShrinkageReportTab({
  auditLogs,
  onClearFilters,
  reportData,
}: ShrinkageReportTabProps) {
  // Use backend report data when available
  const hasBackendData = Boolean(reportData && reportData.line_items);

  // Filter for shortages (BAJA) from local logs if backend data is not present
  const shortages = auditLogs.filter((log) => log.tipo_accion === TipoAccion.BAJA);

  // Computed metrics
  const totalLoss = hasBackendData
    ? Number(reportData!.total_financial_erosion)
    : shortages.reduce((acc, log) => acc + log.monto_valorizado, 0);

  const totalEvents = hasBackendData
    ? reportData!.total_items
    : shortages.length;

  const totalUnitsLost = hasBackendData
    ? reportData!.total_shrinkage_units
    : shortages.reduce((acc, log) => acc + log.cantidad_afectada, 0);

  const avgLoss = totalEvents > 0 ? totalLoss / totalEvents : 0;

  const highestLoss = hasBackendData
    ? (reportData!.line_items.length > 0
        ? Math.max(
            ...reportData!.line_items.map((i) =>
              Number(i.total_financial_loss || i.financial_erosion || 0)
            )
          )
        : 0)
    : shortages.length > 0
    ? Math.max(...shortages.map((l) => l.monto_valorizado))
    : 0;

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) return dateStr;
      return date.toLocaleDateString("es-AR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      });
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="space-y-6">
      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <SummaryKPICard
          title="Pérdida Total del Período"
          amount={totalLoss}
          quantity={totalUnitsLost}
          quantityLabel="unidades perdidas"
          isLoss={true}
          subtitle={`${totalEvents} eventos de faltantes registrados`}
          icon={TrendingDown}
        />
        <SummaryKPICard
          title="Pérdida Promedio / Evento"
          amount={avgLoss}
          subtitle="Costo medio por discrepancia negativa"
          icon={DollarSign}
        />
        <SummaryKPICard
          title="Mayor Pérdida Individual"
          amount={highestLoss}
          subtitle="Impacto económico unitario más alto"
          icon={AlertTriangle}
        />
      </div>

      {/* Main Table View */}
      {(hasBackendData ? reportData!.line_items.length === 0 : shortages.length === 0) ? (
        <EmptyState
          title="Sin faltantes registrados"
          description="No se han registrado bajas ni pérdidas financieras para los filtros seleccionados."
          onClearFilters={onClearFilters}
          icon={Layers}
        />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
          <div className="p-4 sm:p-5 border-b border-slate-100 flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-800 tracking-tight">
              Detalle de Mermas y Faltantes Financieros {hasBackendData && "(Consolidado Fiscal)"}
            </h2>
            <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-full">
              {totalEvents} {hasBackendData ? "artículos afectados" : "registros"}
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs sm:text-sm text-slate-600">
              <thead className="text-[11px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-200 bg-slate-50/70">
                <tr>
                  <th className="px-5 py-3.5 whitespace-nowrap">Código</th>
                  <th className="px-5 py-3.5 min-w-[200px]">Artículo</th>
                  <th className="px-5 py-3.5 whitespace-nowrap">Familia</th>
                  <th className="px-5 py-3.5 text-right whitespace-nowrap">Unidades Merma</th>
                  <th className="px-5 py-3.5 text-right whitespace-nowrap">Costo s/IVA</th>
                  <th className="px-5 py-3.5 text-right whitespace-nowrap">Alícuota IVA</th>
                  <th className="px-5 py-3.5 text-right whitespace-nowrap">Costo Final</th>
                  <th className="px-5 py-3.5 text-right whitespace-nowrap">Pérdida Total</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {hasBackendData ? (
                  reportData!.line_items.map((item) => {
                    const vatPercent = (Number(item.vat_rate) * 100).toFixed(0);
                    return (
                      <tr
                        key={item.article_code}
                        className="hover:bg-slate-50/60 transition-colors"
                      >
                        <td className="px-5 py-4 font-mono text-slate-600 whitespace-nowrap font-medium">
                          {item.article_code}
                        </td>
                        <td
                          className="px-5 py-4 font-semibold text-slate-900 max-w-[240px] truncate"
                          title={item.des_articulo}
                        >
                          {item.des_articulo}
                        </td>
                        <td className="px-5 py-4 text-slate-500 whitespace-nowrap">
                          {item.des_familia || "—"}
                        </td>
                        <td className="px-5 py-4 text-right font-bold text-red-600 font-mono">
                          -{item.total_quantity}
                        </td>
                        <td className="px-5 py-4 text-right font-mono text-slate-600">
                          $
                          {Number(item.pcio_com_siva).toLocaleString("es-AR", {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </td>
                        <td className="px-5 py-4 text-right font-mono text-slate-500">
                          {vatPercent}%
                        </td>
                        <td className="px-5 py-4 text-right font-mono text-slate-700">
                          $
                          {Number(item.total_unit_cost).toLocaleString("es-AR", {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </td>
                        <td className="px-5 py-4 text-right font-bold font-mono text-red-600 bg-red-50/20">
                          $
                          {Number(item.total_financial_loss).toLocaleString("es-AR", {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </td>
                      </tr>
                    );
                  })
                ) : (
                  shortages.map((log) => {
                    const unitCost =
                      log.cantidad_afectada > 0
                        ? log.monto_valorizado / log.cantidad_afectada
                        : 0;
                    return (
                      <tr
                        key={log.client_uuid}
                        className="hover:bg-slate-50/60 transition-colors"
                      >
                        <td className="px-5 py-4 font-mono text-slate-600 whitespace-nowrap font-medium">
                          {log.id_articulo}
                        </td>
                        <td
                          className="px-5 py-4 font-semibold text-slate-900 max-w-[240px] truncate"
                          title={log.des_articulo}
                        >
                          {log.des_articulo}
                        </td>
                        <td className="px-5 py-4 text-slate-500 whitespace-nowrap">
                          {formatDate(log.scan_timestamp)}
                        </td>
                        <td className="px-5 py-4 text-right font-bold text-red-600 font-mono">
                          -{log.cantidad_afectada}
                        </td>
                        <td className="px-5 py-4 text-right font-mono text-slate-600">
                          ${unitCost.toLocaleString("es-AR", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="px-5 py-4 text-right font-mono text-slate-500">
                          —
                        </td>
                        <td className="px-5 py-4 text-right font-mono text-slate-700">
                          ${unitCost.toLocaleString("es-AR", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="px-5 py-4 text-right font-bold font-mono text-red-600 bg-red-50/20">
                          $
                          {log.monto_valorizado.toLocaleString("es-AR", {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
              <tfoot className="border-t-2 border-slate-200 bg-slate-50/80 text-slate-900 font-bold">
                <tr>
                  <td colSpan={3} className="px-5 py-3.5 text-xs uppercase tracking-wider">
                    Total — {totalEvents} {hasBackendData ? "artículos" : "eventos"}
                  </td>
                  <td className="px-5 py-3.5 text-right font-mono text-red-600">
                    -{totalUnitsLost}
                  </td>
                  <td colSpan={3} className="px-5 py-3.5"></td>
                  <td className="px-5 py-3.5 text-right text-red-600 font-mono text-sm bg-red-50/40">
                    $
                    {totalLoss.toLocaleString("es-AR", {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
