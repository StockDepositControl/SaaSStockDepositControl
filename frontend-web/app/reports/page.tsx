"use client";

import React, { useState } from "react";
import { useDataClient } from "@/lib/hooks/useDataClient";
import { DemoShell } from "@/components/layout/DemoShell";
import { UserRole, TipoAccion } from "@/lib/types/domain";
import { AlertCircle, Download, DollarSign, Clock } from "lucide-react";

export default function ReportsPage() {
  const { currentRole, auditLogs } = useDataClient();
  const isAdmin = currentRole === UserRole.ADMINISTRADOR;

  // KPIs Calculations
  const shortages = auditLogs.filter((log) => log.tipo_accion === TipoAccion.BAJA);
  const totalLoss = shortages.reduce((acc, log) => acc + log.monto_valorizado, 0);
  const totalEvents = shortages.length;
  const totalUnitsLost = shortages.reduce((acc, log) => acc + log.cantidad_afectada, 0);
  const avgLoss = totalEvents > 0 ? totalLoss / totalEvents : 0;
  const highestLoss = shortages.length > 0 ? Math.max(...shortages.map((l) => l.monto_valorizado)) : 0;

  const formatDate = (index: number) => {
    const date = new Date(2026, 7, 14); // 14/08/2026
    date.setDate(date.getDate() - Math.floor(index / 2));
    return date.toLocaleDateString("es-AR", { day: "2-digit", month: "2-digit", year: "numeric" });
  };

  return (
    <DemoShell>
      <div className="max-w-6xl mx-auto py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-slate-900 tracking-tight">
            Reportes
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Reportes financieros y operativos de auditoría — Acceso exclusivo para administradores
          </p>
        </div>

        {isAdmin ? (
          <div className="space-y-6">
            {/* Filter and Tabs Card */}
            <div className="bg-white rounded-xl border border-slate-200">
              <div className="p-6 flex flex-col sm:flex-row items-end justify-between gap-4">
                <div className="flex items-center gap-6">
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 mb-1.5">Desde</label>
                    <input
                      type="date"
                      className="border border-slate-200 rounded-lg px-3 py-2.5 text-sm text-slate-700 focus:outline-none focus:border-blue-500 w-40"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 mb-1.5">Hasta</label>
                    <input
                      type="date"
                      className="border border-slate-200 rounded-lg px-3 py-2.5 text-sm text-slate-700 focus:outline-none focus:border-blue-500 w-40"
                    />
                  </div>
                </div>
                <button className="flex items-center gap-2 border border-slate-300 bg-white hover:bg-slate-50 text-slate-700 font-medium px-4 py-2.5 rounded-lg text-sm transition-colors shadow-sm">
                  <Download className="w-4 h-4" />
                  <span>Exportar Excel</span>
                </button>
              </div>

              {/* Tabs */}
              <div className="px-6 flex items-center border-b border-slate-200">
                <button className="flex items-center gap-2 px-4 py-3 border-b-2 border-red-500 text-red-600 font-medium text-sm">
                  <DollarSign className="w-4 h-4" />
                  <span>Faltantes Financieros</span>
                </button>
                <button className="flex items-center gap-2 px-4 py-3 border-b-2 border-transparent text-slate-500 hover:text-slate-700 font-medium text-sm transition-colors">
                  <Clock className="w-4 h-4" />
                  <span>Historial de Auditoría</span>
                </button>
              </div>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Total Loss */}
              <div className="bg-white rounded-xl border border-red-500 p-6 shadow-sm flex items-start justify-between">
                <div>
                  <h3 className="text-[11px] font-bold text-red-600 uppercase tracking-widest mb-3">
                    PÉRDIDA TOTAL DEL PERÍODO
                  </h3>
                  <div className="text-4xl font-bold text-[#c81e1e] mb-2">
                    $ {totalLoss.toLocaleString("es-AR", { minimumFractionDigits: 2 })}
                  </div>
                  <div className="text-sm text-slate-500 font-medium">
                    {totalEvents} eventos de faltantes · {totalUnitsLost} unidades perdidas
                  </div>
                </div>
                <div className="bg-red-50 text-red-500 p-3 rounded-xl">
                  <DollarSign className="w-6 h-6" />
                </div>
              </div>

              {/* Avg Loss */}
              <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col justify-center">
                <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-3">
                  PÉRDIDA PROM. / EVENTO
                </h3>
                <div className="text-2xl font-bold text-slate-900 mb-2">
                  $ {avgLoss.toLocaleString("es-AR", { minimumFractionDigits: 2 })}
                </div>
                <div className="text-sm text-slate-500 font-medium">
                  por evento de faltante
                </div>
              </div>

              {/* Highest Loss */}
              <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col justify-center">
                <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-3">
                  MAYOR PÉRDIDA INDIVIDUAL
                </h3>
                <div className="text-2xl font-bold text-amber-600 mb-2">
                  $ {highestLoss.toLocaleString("es-AR", { minimumFractionDigits: 2 })}
                </div>
                <div className="text-sm text-slate-500 font-medium">
                  evento individual
                </div>
              </div>
            </div>

            {/* Data Table */}
            <div className="bg-white rounded-xl border border-slate-200 overflow-x-auto shadow-sm">
              <table className="w-full text-left text-sm text-slate-600">
                <thead className="text-[11px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-200 bg-white">
                  <tr>
                    <th className="px-6 py-4">FECHA</th>
                    <th className="px-6 py-4">CÓDIGO</th>
                    <th className="px-6 py-4">ARTÍCULO</th>
                    <th className="px-6 py-4 text-right">FALTANTE</th>
                    <th className="px-6 py-4">MOTIVO</th>
                    <th className="px-6 py-4 text-right">COSTO UNITARIO</th>
                    <th className="px-6 py-4 text-right bg-red-50/50 text-red-600">PÉRDIDA TOTAL</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {shortages.map((log, index) => {
                    const unitCost = log.cantidad_afectada > 0 ? log.monto_valorizado / log.cantidad_afectada : 0;
                    return (
                      <tr key={log.client_uuid} className="hover:bg-slate-50/50 transition-colors">
                        <td className="px-6 py-4 whitespace-nowrap text-slate-500">
                          {formatDate(index)}
                        </td>
                        <td className="px-6 py-4 font-mono text-slate-500 whitespace-nowrap">
                          {log.id_articulo}
                        </td>
                        <td className="px-6 py-4 font-medium text-slate-900 max-w-[200px] truncate" title={log.des_articulo}>
                          {log.des_articulo}
                        </td>
                        <td className="px-6 py-4 text-right font-bold text-red-600">
                          -{log.cantidad_afectada}
                        </td>
                        <td className="px-6 py-4 text-slate-500 max-w-[150px] truncate" title={log.observation || "Ajuste operativo"}>
                          {log.observation || "Ajuste operativo"}
                        </td>
                        <td className="px-6 py-4 text-right font-mono text-slate-900">
                          $ {unitCost.toLocaleString("es-AR", { minimumFractionDigits: 2 })}
                        </td>
                        <td className="px-6 py-4 text-right font-bold font-mono text-red-600 bg-red-50/30">
                          $ {log.monto_valorizado.toLocaleString("es-AR", { minimumFractionDigits: 2 })}
                        </td>
                      </tr>
                    );
                  })}
                  {shortages.length === 0 && (
                    <tr>
                      <td colSpan={7} className="px-6 py-12 text-center text-slate-500 font-medium">
                        No se registraron faltantes financieros.
                      </td>
                    </tr>
                  )}
                </tbody>
                {shortages.length > 0 && (
                  <tfoot className="border-t border-slate-200 bg-slate-50/50 text-slate-900 font-bold">
                    <tr>
                      <td colSpan={3} className="px-6 py-4">
                        Total — {totalEvents} eventos
                      </td>
                      <td className="px-6 py-4 text-right">
                        {totalUnitsLost}
                      </td>
                      <td colSpan={2} className="px-6 py-4"></td>
                      <td className="px-6 py-4 text-right text-red-600 bg-red-50/50">
                        $ {totalLoss.toLocaleString("es-AR", { minimumFractionDigits: 2 })}
                      </td>
                    </tr>
                  </tfoot>
                )}
              </table>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-20 px-6 bg-white rounded-3xl border border-slate-200 border-dashed text-center mt-6">
            <AlertCircle className="w-16 h-16 text-slate-300 mb-6" />
            <h2 className="text-xl font-bold text-slate-900 mb-2">Acceso Restringido</h2>
            <p className="text-sm text-slate-500 max-w-sm">
              Su rol operativo (<strong>{currentRole}</strong>) no posee los permisos requeridos para visualizar reportes financieros ni valorizaciones de costos.
            </p>
          </div>
        )}
      </div>
    </DemoShell>
  );
}
