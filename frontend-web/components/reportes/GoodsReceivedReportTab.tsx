"use client";

import React from "react";
import { AuditResult, TipoAccion } from "@/lib/types/domain";
import { SummaryKPICard } from "./SummaryKPICard";
import { EmptyState } from "./EmptyState";
import { TrendingUp, PackageCheck, Layers, DollarSign } from "lucide-react";

import { ApiGoodsReceivedReportResponse } from "@/lib/types/api";

export interface GoodsReceivedReportTabProps {
  auditLogs: AuditResult[];
  startDate?: string;
  endDate?: string;
  onClearFilters?: () => void;
  reportData?: ApiGoodsReceivedReportResponse | null;
}

export function GoodsReceivedReportTab({
  auditLogs,
  onClearFilters,
  reportData,
}: GoodsReceivedReportTabProps) {
  const hasBackendData = Boolean(reportData && reportData.line_items);

  // Filter for positive additions (ALTA) from local logs if backend data is absent
  const additions = auditLogs.filter((log) => log.tipo_accion === TipoAccion.ALTA);

  // Computed metrics
  const totalValuation = hasBackendData
    ? Number(reportData!.total_capital_inyectado ?? reportData!.total_capital_injected ?? 0)
    : additions.reduce((acc, log) => acc + log.monto_valorizado, 0);

  const totalEvents = hasBackendData
    ? reportData!.total_items
    : additions.length;

  const totalUnitsAdded = hasBackendData
    ? (reportData!.total_added_units ?? reportData!.total_goods_received_units ?? 0)
    : additions.reduce((acc, log) => acc + log.cantidad_afectada, 0);

  const avgValuation = totalEvents > 0 ? totalValuation / totalEvents : 0;

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
          title="Valorización Total de Altas"
          amount={totalValuation}
          quantity={totalUnitsAdded}
          quantityLabel="unidades ingresadas"
          subtitle={`${totalEvents} ${hasBackendData ? "artículos con alta / sobrante" : "ingresos o sobrantes auditados"}`}
          icon={TrendingUp}
        />
        <SummaryKPICard
          title="Promedio por Artículo / Evento"
          amount={avgValuation}
          subtitle="Valor medio por incorporación de stock"
          icon={DollarSign}
        />
        <SummaryKPICard
          title="Total Unidades Incorporadas"
          amount={totalUnitsAdded}
          quantityLabel="unidades"
          subtitle="Stock recuperado / ingresado"
          icon={PackageCheck}
        />
      </div>

      {/* Main Table View */}
      {(hasBackendData ? reportData!.line_items.length === 0 : additions.length === 0) ? (
        <EmptyState
          title="Sin ingresos ni altas registradas"
          description="No se han encontrado registros de altas o sobrantes para los filtros seleccionados."
          onClearFilters={onClearFilters}
          icon={Layers}
        />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
          <div className="p-4 sm:p-5 border-b border-slate-100 flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-800 tracking-tight">
              Detalle de Ingresos, Sobrantes y Valorización de Altas {hasBackendData && "(Capital Inyectado c/IVA)"}
            </h2>
            <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-full">
              {totalEvents} {hasBackendData ? "artículos" : "registros"}
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs sm:text-sm text-slate-600">
              <thead className="text-[11px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-200 bg-slate-50/70">
                <tr>
                  <th className="px-5 py-3.5 whitespace-nowrap">Código</th>
                  <th className="px-5 py-3.5 min-w-[200px]">Artículo</th>
                  <th className="px-5 py-3.5 whitespace-nowrap">Familia</th>
                  <th className="px-5 py-3.5 whitespace-nowrap">Motivo</th>
                  <th className="px-5 py-3.5 text-right whitespace-nowrap">Cantidad Ingreso</th>
                  <th className="px-5 py-3.5 text-right whitespace-nowrap">Costo Unitario</th>
                  <th className="px-5 py-3.5 text-right whitespace-nowrap">Capital Inyectado</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {hasBackendData ? (
                  reportData!.line_items.map((item) => (
                    <tr
                      key={`${item.article_code}-${item.reason}`}
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
                      <td className="px-5 py-4 text-slate-500 whitespace-nowrap">
                        {item.reason}
                      </td>
                      <td className="px-5 py-4 text-right font-bold text-emerald-600 font-mono">
                        +{item.quantity_added}
                      </td>
                      <td className="px-5 py-4 text-right font-mono text-slate-700">
                        $
                        {Number(item.total_unit_cost).toLocaleString("es-AR", {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </td>
                      <td className="px-5 py-4 text-right font-bold font-mono text-emerald-600 bg-emerald-50/20">
                        $
                        {Number(item.capital_inyectado).toLocaleString("es-AR", {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </td>
                    </tr>
                  ))
                ) : (
                  additions.map((log) => {
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
                        <td className="px-5 py-4 text-slate-500 whitespace-nowrap">
                          {log.lote || "S/L"}
                        </td>
                        <td className="px-5 py-4 text-right font-bold text-emerald-600 font-mono">
                          +{log.cantidad_afectada}
                        </td>
                        <td className="px-5 py-4 text-right font-mono text-slate-700">
                          $
                          {unitCost.toLocaleString("es-AR", {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2,
                          })}
                        </td>
                        <td className="px-5 py-4 text-right font-bold font-mono text-emerald-600 bg-emerald-50/20">
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
                  <td colSpan={4} className="px-5 py-3.5 text-xs uppercase tracking-wider">
                    Total — {totalEvents} {hasBackendData ? "artículos" : "eventos"}
                  </td>
                  <td className="px-5 py-3.5 text-right font-mono text-emerald-600">
                    +{totalUnitsAdded}
                  </td>
                  <td className="px-5 py-3.5"></td>
                  <td className="px-5 py-3.5 text-right text-emerald-600 font-mono text-sm bg-emerald-50/40">
                    $
                    {totalValuation.toLocaleString("es-AR", {
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
