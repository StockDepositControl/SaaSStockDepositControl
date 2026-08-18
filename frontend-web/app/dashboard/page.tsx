"use client";

import React, { useState } from "react";
import { useDataClient } from "@/lib/hooks/useDataClient";
import { UserRole, DashboardKPIsAdmin, ArticuloPublicView, ArticuloAdminView } from "@/lib/types/domain";
import { KPICard } from "@/components/ui/KPICard";
import { DataTable } from "@/components/ui/DataTable";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { DemoShell } from "@/components/layout/DemoShell";
import {
  TrendingUp,
  AlertCircle,
  Clock,
  DollarSign,
  ScanLine,
  Layers,
  Sparkles,
  Calendar,
  ArrowRight,
  Shield,
  Activity,
} from "lucide-react";

export default function DashboardPage() {
  const {
    currentUser,
    currentRole,
    articles,
    kpis,
    auditLogs,
  } = useDataClient();

  const isAdmin = currentRole === UserRole.ADMINISTRADOR;
  const adminKPIs = isAdmin ? (kpis as DashboardKPIsAdmin) : null;

  const urgentLots = React.useMemo(() => {
    const lots: Array<{
      id_articulo: string;
      des_articulo: string;
      lote: string;
      vencimiento: string;
      stock_real: number;
    }> = [];

    articles.forEach((art) => {
      art.lotes?.forEach((l) => {
        lots.push({
          id_articulo: art.id_articulo,
          des_articulo: art.des_articulo,
          lote: l.lote,
          vencimiento: l.vencimiento || "",
          stock_real: l.stock_real,
        });
      });
    });

    lots.sort((a, b) => new Date(a.vencimiento).getTime() - new Date(b.vencimiento).getTime());
    return lots.slice(0, 4);
  }, [articles]);

  return (
    <DemoShell>
      <div className="max-w-7xl mx-auto space-y-8">
        {/* Top Hero Banner */}
        <div className="glass-panel-elevated rounded-3xl p-6 md:p-8 relative overflow-hidden border border-slate-800 shadow-2xl">
          <div className="absolute top-0 right-0 -mt-8 -mr-8 w-64 h-64 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute bottom-0 left-1/3 -mb-8 w-64 h-64 bg-emerald-600/10 rounded-full blur-3xl pointer-events-none" />

          <div className="relative z-10 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
            <div className="space-y-2">
              <div className="flex items-center gap-2.5">
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Control de Depósito Inteligente</span>
                </span>
                <span className="text-xs text-slate-400 flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5" />
                  <span>18 Ago 2026</span>
                </span>
              </div>

              <h1 className="text-2xl md:text-3xl lg:text-4xl font-extrabold text-white tracking-tight">
                Panel de Auditoría & Control de Stock
              </h1>

              <p className="text-xs md:text-sm text-slate-300 max-w-2xl leading-relaxed">
                Supervisión en tiempo real de inventario físico, cálculo automatizado de
                discrepancias (<span className="text-emerald-400 font-medium">Altas</span> /{" "}
                <span className="text-rose-400 font-medium">Bajas</span>) y semáforo de
                vencimientos FEFO.
              </p>
            </div>

            {/* Profile Status Badge in Banner */}
            <div className="p-4 rounded-2xl bg-slate-950/80 border border-slate-800/90 shrink-0 space-y-2 text-xs">
              <div className="text-slate-400 font-medium flex items-center justify-between gap-3">
                <span>Perfil Activo:</span>
                <StatusBadge type="role" value={currentRole} size="sm" />
              </div>
              <div className="text-slate-200 font-bold text-sm flex items-center gap-2">
                <div className="h-6 w-6 rounded-lg bg-indigo-600/30 flex items-center justify-center text-indigo-300 font-bold text-xs">
                  {currentUser?.name?.charAt(0) || "U"}
                </div>
                <span>{currentUser?.name}</span>
              </div>
              <div className="text-[11px] text-slate-400 font-mono">
                {isAdmin ? (
                  <span className="text-amber-400 flex items-center gap-1">
                    <Shield className="w-3 h-3" /> Costos s/IVA Desbloqueados
                  </span>
                ) : (
                  <span className="text-emerald-400 flex items-center gap-1">
                    <Shield className="w-3 h-3" /> Modo Ciego (Sin Costos)
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Live KPI Cards Row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <KPICard
            title="Progreso Auditoría"
            value={`${kpis.porcentajeAvance}%`}
            subtitle={`${kpis.auditados} de ${kpis.totalArticulos} artículos auditados`}
            icon={TrendingUp}
            variant="primary"
            trend={{
              value: `${kpis.pendientes} pendientes`,
              isPositive: true,
            }}
          />

          <KPICard
            title="Discrepancias (Alta)"
            value={kpis.discrepanciasAlta}
            subtitle="Artículos con sobrante físico"
            icon={Activity}
            variant="success"
            trend={{
              value: "Movimientos de Entrada",
              isPositive: true,
            }}
          />

          <KPICard
            title="Discrepancias (Baja)"
            value={kpis.discrepanciasBaja}
            subtitle="Faltantes o mermas operativas"
            icon={AlertCircle}
            variant="danger"
            trend={{
              value: "Pérdidas Registradas",
              isPositive: false,
            }}
          />

          <KPICard
            title="Impacto Financiero"
            value={
              isAdmin && adminKPIs
                ? `$${adminKPIs.montoValorizadoTotal.toLocaleString("es-AR", {
                    minimumFractionDigits: 2,
                  })}`
                : "Restringido"
            }
            subtitle={
              isAdmin && adminKPIs
                ? `Alta: $${adminKPIs.montoValorizadoAlta.toLocaleString()} | Baja: $${adminKPIs.montoValorizadoBaja.toLocaleString()}`
                : "Confidencial"
            }
            icon={DollarSign}
            variant="warning"
            isRestricted={!isAdmin}
            restrictedMessage="Solo Administrador"
          />
        </div>

        {/* Middle Section: FEFO Expiration Matrix & Quick Scan / Audit Box */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* FEFO Semaphoric Matrix */}
          <div className="lg:col-span-2 glass-panel rounded-2xl p-5 border border-slate-800/80 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Clock className="w-5 h-5 text-amber-400" />
                <h3 className="font-bold text-white text-base">
                  Matriz de Vencimientos FEFO (Primeros Lotes a Vencer)
                </h3>
              </div>
              <span className="text-xs text-slate-400 font-mono">
                Ordenado por proximidad
              </span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {urgentLots.map((lot, idx) => (
                <div
                  key={`${lot.id_articulo}-${lot.lote}-${idx}`}
                  className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800/90 flex flex-col justify-between space-y-2 hover:border-slate-700 transition"
                >
                  <div>
                    <div className="text-xs font-semibold text-white truncate" title={lot.des_articulo}>
                      {lot.des_articulo}
                    </div>
                    <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                      Lote: <span className="text-indigo-300 font-medium">{lot.lote}</span> (
                      {lot.stock_real} un.)
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-slate-800/60">
                    <span className="text-[11px] text-slate-500 font-mono">
                      Vencimiento:
                    </span>
                    <StatusBadge type="fefo" value={lot.vencimiento} size="sm" />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Quick Floor Audit Trigger */}
          <div className="glass-panel rounded-2xl p-5 border border-slate-800/80 flex flex-col justify-between space-y-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-white font-bold">
                <ScanLine className="w-5 h-5 text-indigo-400" />
                <h3>Registro de Conteo Rápido</h3>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Ir al módulo de auditoría operativa para escanear artículos y registrar conteo.
              </p>
            </div>

            <div className="space-y-3">
              <div className="p-4 rounded-xl bg-slate-950/60 border border-dashed border-slate-800 text-center text-xs text-slate-400">
                Utiliza un escáner láser o ingresa el código manualmente en la pantalla de auditoría.
              </div>
              <a
                href="/audit"
                className="flex items-center justify-center gap-2 w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-sm font-semibold transition"
              >
                <span>Abrir Escáner Operativo</span>
                <ArrowRight className="w-4 h-4" />
              </a>
            </div>
          </div>
        </div>



        {/* Chronological Audit Log History */}
        <div id="reports" className="glass-panel rounded-2xl p-5 border border-slate-800/80 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div className="flex items-center gap-2">
              <Layers className="w-5 h-5 text-indigo-400" />
              <h3 className="font-bold text-white text-base">
                Registro de Movimientos & Auditorías Recientes
              </h3>
            </div>
            <span className="text-xs text-slate-400 font-mono">
              {auditLogs.length} operaciones registradas
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-300">
              <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800 uppercase tracking-wider">
                <tr>
                  <th className="p-3">Artículo</th>
                  <th className="p-3 text-right">Teórico</th>
                  <th className="p-3 text-right">Físico</th>
                  <th className="p-3 text-center">Delta (Δ)</th>
                  <th className="p-3 text-center">Tipo Acción</th>
                  {isAdmin && (
                    <th className="p-3 text-right text-amber-400">Valorización</th>
                  )}
                  <th className="p-3">Observaciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {auditLogs.map((log) => (
                  <tr key={log.client_uuid} className="hover:bg-slate-800/30">
                    <td className="p-3 font-sans">
                      <div className="font-semibold text-white">{log.id_articulo}</div>
                      <div className="text-slate-400 text-[11px] truncate max-w-[200px]">
                        {log.des_articulo}
                      </div>
                    </td>
                    <td className="p-3 text-right text-slate-400">{log.stock_real} un.</td>
                    <td className="p-3 text-right font-bold text-white">
                      {log.stock_fisico_contado} un.
                    </td>
                    <td
                      className={`p-3 text-center font-bold ${
                        log.delta_stock > 0
                          ? "text-emerald-400"
                          : log.delta_stock < 0
                          ? "text-rose-400"
                          : "text-slate-400"
                      }`}
                    >
                      {log.delta_stock > 0 ? `+${log.delta_stock}` : log.delta_stock}
                    </td>
                    <td className="p-3 text-center">
                      <StatusBadge type="movement" value={log.tipo_accion} size="sm" />
                    </td>
                    {isAdmin && (
                      <td className="p-3 text-right font-semibold text-amber-300">
                        ${log.monto_valorizado.toLocaleString("es-AR", { minimumFractionDigits: 2 })}
                      </td>
                    )}
                    <td className="p-3 text-slate-400 font-sans max-w-[200px] truncate" title={log.observation || undefined}>
                      {log.observation || "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </DemoShell>
  );
}
