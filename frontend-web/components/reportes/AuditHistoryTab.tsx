"use client";

import React from "react";
import { AuditResult, TipoAccion } from "@/lib/types/domain";
import { SummaryKPICard } from "./SummaryKPICard";
import { EmptyState } from "./EmptyState";
import { History, CheckCircle2, AlertCircle, Layers } from "lucide-react";

export interface AuditHistoryTabProps {
  auditLogs: AuditResult[];
  startDate?: string;
  endDate?: string;
  onClearFilters?: () => void;
}

export function AuditHistoryTab({
  auditLogs,
  onClearFilters,
}: AuditHistoryTabProps) {
  const totalAudits = auditLogs.length;
  const exactMatches = auditLogs.filter((l) => l.tipo_accion === TipoAccion.SIN_ACCION).length;
  const discrepancies = auditLogs.filter((l) => l.tipo_accion !== TipoAccion.SIN_ACCION).length;

  const formatDateTime = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      if (isNaN(date.getTime())) return dateStr;
      return `${date.toLocaleDateString("es-AR", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      })} ${date.toLocaleTimeString("es-AR", {
        hour: "2-digit",
        minute: "2-digit",
      })}`;
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="space-y-6">
      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <SummaryKPICard
          title="Total Auditorías Realizadas"
          amount={totalAudits}
          quantity={totalAudits}
          quantityLabel="eventos"
          subtitle="Registros procesados por el equipo auditor"
          icon={History}
        />
        <SummaryKPICard
          title="Conteo Conforme (Sin Desvío)"
          amount={exactMatches}
          quantity={totalAudits > 0 ? `${Math.round((exactMatches / totalAudits) * 100)}%` : "0%"}
          quantityLabel="del total"
          subtitle="Stock físico idéntico al sistema"
          icon={CheckCircle2}
        />
        <SummaryKPICard
          title="Discrepancias Detectadas"
          amount={discrepancies}
          quantity={totalAudits > 0 ? `${Math.round((discrepancies / totalAudits) * 100)}%` : "0%"}
          quantityLabel="del total"
          isLoss={discrepancies > 0}
          subtitle="Eventos con ajuste de inventario (Alta/Baja)"
          icon={AlertCircle}
        />
      </div>

      {/* Main Table View */}
      {auditLogs.length === 0 ? (
        <EmptyState
          title="Sin auditorías registradas"
          description="No se registran eventos de auditoría para el período seleccionado."
          onClearFilters={onClearFilters}
          icon={Layers}
        />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
          <div className="p-4 sm:p-5 border-b border-slate-100 flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-800 tracking-tight">
              Trazabilidad Completa de Auditorías
            </h2>
            <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-full">
              {totalAudits} registros
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs sm:text-sm text-slate-600">
              <thead className="text-[11px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-200 bg-slate-50/70">
                <tr>
                  <th className="px-5 py-3.5 whitespace-nowrap">Fecha / Hora</th>
                  <th className="px-5 py-3.5 whitespace-nowrap">Código</th>
                  <th className="px-5 py-3.5 min-w-[180px]">Artículo</th>
                  <th className="px-5 py-3.5 text-right whitespace-nowrap">Stock Sist.</th>
                  <th className="px-5 py-3.5 text-right whitespace-nowrap">Físico</th>
                  <th className="px-5 py-3.5 text-right whitespace-nowrap">Delta</th>
                  <th className="px-5 py-3.5 text-center whitespace-nowrap">Acción</th>
                  <th className="px-5 py-3.5 text-right whitespace-nowrap">Monto Val.</th>
                  <th className="px-5 py-3.5 min-w-[160px]">Observación</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {auditLogs.map((log) => {
                  const isAlta = log.tipo_accion === TipoAccion.ALTA;
                  const isBaja = log.tipo_accion === TipoAccion.BAJA;

                  return (
                    <tr
                      key={log.client_uuid}
                      className="hover:bg-slate-50/60 transition-colors"
                    >
                      <td className="px-5 py-4 whitespace-nowrap font-mono text-slate-500 text-xs">
                        {formatDateTime(log.scan_timestamp)}
                      </td>
                      <td className="px-5 py-4 font-mono text-slate-600 whitespace-nowrap font-medium">
                        {log.id_articulo}
                      </td>
                      <td
                        className="px-5 py-4 font-semibold text-slate-900 max-w-[220px] truncate"
                        title={log.des_articulo}
                      >
                        {log.des_articulo}
                      </td>
                      <td className="px-5 py-4 text-right font-mono text-slate-600">
                        {log.stock_real}
                      </td>
                      <td className="px-5 py-4 text-right font-mono font-bold text-slate-900">
                        {log.stock_fisico_contado}
                      </td>
                      <td
                        className={`px-5 py-4 text-right font-mono font-bold ${
                          isAlta
                            ? "text-emerald-600"
                            : isBaja
                            ? "text-red-600"
                            : "text-slate-400"
                        }`}
                      >
                        {log.delta_stock > 0
                          ? `+${log.delta_stock}`
                          : log.delta_stock}
                      </td>
                      <td className="px-5 py-4 text-center whitespace-nowrap">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                            isAlta
                              ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                              : isBaja
                              ? "bg-red-50 text-red-700 border border-red-200"
                              : "bg-slate-100 text-slate-600 border border-slate-200"
                          }`}
                        >
                          {log.tipo_accion}
                        </span>
                      </td>
                      <td
                        className={`px-5 py-4 text-right font-mono font-semibold ${
                          isAlta
                            ? "text-emerald-600"
                            : isBaja
                            ? "text-red-600"
                            : "text-slate-400"
                        }`}
                      >
                        $
                        {log.monto_valorizado.toLocaleString("es-AR", {
                          minimumFractionDigits: 2,
                          maximumFractionDigits: 2,
                        })}
                      </td>
                      <td
                        className="px-5 py-4 text-slate-500 max-w-[180px] truncate text-xs"
                        title={log.observation || "Sin observaciones"}
                      >
                        {log.observation || "—"}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
