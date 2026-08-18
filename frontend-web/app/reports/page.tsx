"use client";

import React from "react";
import { useDataClient } from "@/lib/hooks/useDataClient";
import { DemoShell } from "@/components/layout/DemoShell";
import { UserRole, TipoAccion, DashboardKPIsAdmin } from "@/lib/types/domain";
import { BarChart3, AlertCircle, TrendingDown, TrendingUp } from "lucide-react";

export default function ReportsPage() {
  const { currentRole, kpis, auditLogs } = useDataClient();
  const isAdmin = currentRole === UserRole.ADMINISTRADOR;
  const adminKPIs = isAdmin ? (kpis as DashboardKPIsAdmin) : null;

  return (
    <DemoShell>
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
              <BarChart3 className="w-8 h-8 text-indigo-400" />
              <span>Reportes & Valorización Financiera</span>
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Visualiza el impacto de mermas y sobrantes a costo de compra (s/IVA / c/IVA).
            </p>
          </div>
        </div>

        {isAdmin ? (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="glass-panel p-6 rounded-2xl border border-slate-800">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
                    <TrendingUp className="w-5 h-5" />
                  </div>
                  <h3 className="text-lg font-bold text-white">Ingresos (Altas)</h3>
                </div>
                <p className="text-3xl font-mono text-emerald-400 font-bold mt-4">
                  ${adminKPIs?.montoValorizadoAlta.toLocaleString("es-AR", { minimumFractionDigits: 2 })}
                </p>
                <p className="text-xs text-slate-400 mt-2">Valorización de sobrantes de inventario descubiertos en la auditoría.</p>
              </div>

              <div className="glass-panel p-6 rounded-2xl border border-slate-800">
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400">
                    <TrendingDown className="w-5 h-5" />
                  </div>
                  <h3 className="text-lg font-bold text-white">Mermas (Bajas)</h3>
                </div>
                <p className="text-3xl font-mono text-rose-400 font-bold mt-4">
                  ${adminKPIs?.montoValorizadoBaja.toLocaleString("es-AR", { minimumFractionDigits: 2 })}
                </p>
                <p className="text-xs text-slate-400 mt-2">Impacto financiero total por faltantes y vencimientos FEFO críticos.</p>
              </div>
            </div>

            <div className="glass-panel rounded-2xl p-6 border border-slate-800 overflow-x-auto">
              <h3 className="text-lg font-bold text-white mb-4">Detalle de Movimientos con Impacto</h3>
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-900 text-slate-400 uppercase border-b border-slate-800">
                  <tr>
                    <th className="p-3">ID / Artículo</th>
                    <th className="p-3 text-center">Tipo</th>
                    <th className="p-3 text-right">Cantidad</th>
                    <th className="p-3 text-right">Tasa IVA</th>
                    <th className="p-3 text-right text-amber-400">Valorización Final</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/50">
                  {auditLogs.filter(log => log.tipo_accion !== TipoAccion.SIN_ACCION).map(log => (
                    <tr key={log.client_uuid}>
                      <td className="p-3">
                        <div className="font-bold text-white">{log.id_articulo}</div>
                        <div className="text-slate-500 truncate max-w-[200px]">{log.des_articulo}</div>
                      </td>
                      <td className="p-3 text-center font-bold">
                        {log.tipo_accion === TipoAccion.ALTA ? (
                          <span className="text-emerald-400">ALTA</span>
                        ) : (
                          <span className="text-rose-400">BAJA</span>
                        )}
                      </td>
                      <td className="p-3 text-right">{log.cantidad_afectada}</td>
                      <td className="p-3 text-right">{(log.applied_vat_rate * 100).toFixed(0)}%</td>
                      <td className="p-3 text-right font-mono text-amber-300">
                        ${log.monto_valorizado.toLocaleString("es-AR", { minimumFractionDigits: 2 })}
                      </td>
                    </tr>
                  ))}
                  {auditLogs.filter(l => l.tipo_accion !== TipoAccion.SIN_ACCION).length === 0 && (
                    <tr>
                      <td colSpan={5} className="p-6 text-center text-slate-500">No hay movimientos con impacto financiero registrados.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-[50vh] text-center p-6 bg-slate-900/50 rounded-3xl border border-slate-800 border-dashed">
            <AlertCircle className="w-16 h-16 text-slate-600 mb-4" />
            <h2 className="text-xl font-bold text-white">Acceso Restringido</h2>
            <p className="text-sm text-slate-400 max-w-sm mt-2">
              Su rol operativo (<strong>{currentRole}</strong>) no posee los permisos requeridos para visualizar información de costos ni valorizaciones financieras (RBAC).
            </p>
          </div>
        )}
      </div>
    </DemoShell>
  );
}
