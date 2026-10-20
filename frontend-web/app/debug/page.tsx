"use client";

import React, { useState } from "react";
import { useDataClient } from "../../lib/hooks/useDataClient";
import { useArticles } from "../../lib/hooks/useArticles";
import { useKPIs } from "../../lib/hooks/useKPIs";
import { useAuditLogs } from "../../lib/hooks/useAuditLogs";
import { UserRole, ArticuloAdminView, TipoAccion } from "../../lib/types/domain";

export default function DebugPage() {
  const {
    currentUser,
    currentRole,
    users,
    switchUser,
    client,
  } = useDataClient();
  const { articles, refetch: refetchArticles } = useArticles();
  const { kpis, refetch: refetchKPIs } = useKPIs();
  const { auditLogs, refetch: refetchAuditLogs } = useAuditLogs();

  const [selectedArticleId, setSelectedArticleId] = useState<string>(
    articles[0]?.id_articulo || ""
  );
  const [physicalCount, setPhysicalCount] = useState<string>("50");
  const [lotNumber, setLotNumber] = useState<string>("");
  const [notes, setNotes] = useState<string>("");
  const [auditFeedback, setAuditFeedback] = useState<string | null>(null);

  const selectedArticle = articles.find((a) => a.id_articulo === selectedArticleId);

  const handleAuditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedArticleId) return;

    const countNum = parseInt(physicalCount, 10);
    if (isNaN(countNum) || countNum < 0) {
      setAuditFeedback("Por favor ingrese un conteo físico válido (>= 0)");
      return;
    }

    try {
      const result = await client.registerAudit({
        id_articulo: selectedArticleId,
        stock_fisico_contado: countNum,
        lote: lotNumber || undefined,
        observation: notes || undefined,
      });

      setAuditFeedback(
        `✅ Auditoría registrada para ${result.des_articulo}: Delta = ${
          result.delta_stock > 0 ? `+${result.delta_stock}` : result.delta_stock
        } (${result.tipo_accion}) | Valorización: $${result.monto_valorizado.toLocaleString()}`
      );
      setNotes("");

      // Trigger targeted domain refetches for debug console
      await Promise.all([
        refetchArticles(),
        refetchKPIs(),
        refetchAuditLogs(),
      ]);
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : String(err);
      setAuditFeedback(`❌ Error: ${errorMsg}`);
    }
  };

  const isAdmin = currentRole === UserRole.ADMINISTRADOR;
  const adminKPIs = isAdmin ? (kpis as import("../../lib/types/domain").DashboardKPIsAdmin) : null;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between pb-6 border-b border-slate-800 gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">
            Deposit Control — Mock & Stateful Layer Test
          </h1>
          <p className="text-slate-400 mt-1">
            Simulación de usuarios mock, token de credencial/badge y aislamiento RBAC a nivel de campo.
          </p>
        </div>

        <button
          onClick={() => client.resetData()}
          className="px-3.5 py-2 text-xs text-rose-400 hover:text-rose-300 hover:bg-rose-950/40 rounded-xl border border-rose-900/50 transition font-medium"
          title="Restablecer datos a estado inicial"
        >
          🔄 Reset Datos Seed
        </button>
      </div>

      {/* Mock Users Selection Deck */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            👥 Base de Datos Mock de Usuarios (Haz clic para cambiar identidad):
          </span>
          <span className="text-xs text-slate-500 font-mono">
            {users.length} usuarios registrados
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {users.map((u) => {
            const isCurrent = currentUser?.id === u.id;
            return (
              <button
                key={u.id}
                onClick={() => switchUser(u.id)}
                className={`p-3.5 rounded-xl border text-left transition-all duration-150 relative overflow-hidden flex flex-col justify-between ${
                  isCurrent
                    ? "bg-slate-900 border-indigo-500 ring-2 ring-indigo-500/30 shadow-lg shadow-indigo-500/10"
                    : "bg-slate-900/50 border-slate-800 hover:border-slate-700 hover:bg-slate-900"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="font-semibold text-sm text-white flex items-center gap-1.5">
                      <span>{u.name}</span>
                      {isCurrent && (
                        <span className="h-2 w-2 rounded-full bg-indigo-400 animate-ping" />
                      )}
                    </div>
                    <div className="text-xs text-slate-400">{u.email}</div>
                  </div>
                  <span
                    className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                      u.role === UserRole.ADMINISTRADOR
                        ? "bg-amber-950 text-amber-300 border border-amber-800/80"
                        : u.role === UserRole.SUPERVISOR
                        ? "bg-indigo-950 text-indigo-300 border border-indigo-800/80"
                        : "bg-emerald-950 text-emerald-300 border border-emerald-800/80"
                    }`}
                  >
                    {u.role}
                  </span>
                </div>

                <div className="mt-3 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] font-mono text-slate-500">
                  <span>Badge:</span>
                  <span className="text-slate-300 bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800">
                    {u.badgeToken}
                  </span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Active User Session & RBAC Status Bar */}
      <div className="p-4 rounded-xl border bg-slate-900/80 border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4 text-sm">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center font-bold text-white">
            {currentUser?.name.charAt(0) || "U"}
          </div>
          <div>
            <div className="text-slate-200 font-medium">
              Sesión activa: <span className="text-white font-bold">{currentUser?.name}</span> (
              <span className="text-indigo-400 font-semibold">{currentUser?.email}</span>)
            </div>
            <div className="text-xs text-slate-400 flex items-center gap-2 mt-0.5">
              <span>Token: <code className="text-slate-300 font-mono">{currentUser?.badgeToken}</code></span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 self-start md:self-auto">
          <span className="text-xs text-slate-400">Estado de Acceso:</span>
          {isAdmin ? (
            <span className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-amber-950/70 text-amber-300 border border-amber-800 flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
              Admin (Acceso total con costos)
            </span>
          ) : (
            <span className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-emerald-950/70 text-emerald-300 border border-emerald-800 flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              Restringido (Costos ocultos a nivel DTO)
            </span>
          )}
        </div>
      </div>


      {/* Live KPIs Section */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 p-5 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-400 font-medium">Progreso Auditoría</span>
          <div className="text-2xl font-bold text-white mt-1">
            {kpis.porcentajeAvance}%
          </div>
          <p className="text-xs text-slate-400 mt-1">
            {kpis.auditados} auditados de {kpis.totalArticulos} ({kpis.pendientes} pendientes)
          </p>
        </div>

        <div className="bg-slate-900 p-5 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-400 font-medium">Discrepancias (Alta / Sobrante)</span>
          <div className="text-2xl font-bold text-emerald-400 mt-1">
            {kpis.discrepanciasAlta}
          </div>
          <p className="text-xs text-slate-400 mt-1">Movimientos tipo ALTA</p>
        </div>

        <div className="bg-slate-900 p-5 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-400 font-medium">Discrepancias (Baja / Faltante)</span>
          <div className="text-2xl font-bold text-rose-400 mt-1">
            {kpis.discrepanciasBaja}
          </div>
          <p className="text-xs text-slate-400 mt-1">Movimientos tipo BAJA</p>
        </div>

        <div className="bg-slate-900 p-5 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-400 font-medium">
            {isAdmin ? "Impacto Financiero Total (IVA incl.)" : "Sin Discrepancia"}
          </span>
          <div className="text-2xl font-bold text-amber-400 mt-1">
            {isAdmin && adminKPIs ? (
              `$${adminKPIs.montoValorizadoTotal.toLocaleString("es-AR", {
                minimumFractionDigits: 2,
              })}`
            ) : (
              `${kpis.sinAccion} ítems`
            )}
          </div>
          <p className="text-xs text-slate-400 mt-1">
            {isAdmin && adminKPIs
              ? `Alta: $${adminKPIs.montoValorizadoAlta.toLocaleString()} | Baja: $${adminKPIs.montoValorizadoBaja.toLocaleString()}`
              : "Stock físico coincide"}
          </p>
        </div>
      </div>

      {/* Main Interactive Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Audit Action Form */}
        <div className="bg-slate-900 p-6 rounded-2xl border border-slate-800 space-y-4">
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <span>📝</span> Registrar Auditoría de Stock
          </h2>
          <p className="text-xs text-slate-400">
            Simula el escaneo con colector o ingreso de conteo físico. Actualiza el estado del
            artículo y recalcula los KPIs en tiempo real.
          </p>

          <form onSubmit={handleAuditSubmit} className="space-y-4 pt-2">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Artículo a auditar
              </label>
              <select
                value={selectedArticleId}
                onChange={(e) => {
                  setSelectedArticleId(e.target.value);
                  const matched = articles.find((a) => a.id_articulo === e.target.value);
                  if (matched) {
                    setPhysicalCount(String(matched.stock_real));
                  }
                }}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-sm text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
              >
                {articles.map((art) => (
                  <option key={art.id_articulo} value={art.id_articulo}>
                    {art.fue_auditado ? "✓" : "○"} {art.id_articulo} - {art.des_articulo.substring(0, 35)}...
                  </option>
                ))}
              </select>
            </div>

            {selectedArticle && (
              <div className="p-3 bg-slate-950/70 rounded-lg border border-slate-800/80 text-xs space-y-1">
                <div className="text-slate-300">
                  <strong>Stock Sistema (Teórico):</strong>{" "}
                  <span className="text-indigo-400 font-bold">{selectedArticle.stock_real}</span> un.
                </div>
                <div className="text-slate-300">
                  <strong>Familia:</strong> {selectedArticle.des_familia} (
                  {selectedArticle.des_familia?.toLowerCase() === "medicamentos"
                    ? "IVA 0%"
                    : "IVA 21%"}
                  )
                </div>
                {isAdmin && "pcio_com_siva" in selectedArticle && (
                  <div className="text-amber-400">
                    <strong>Costo Unitario (s/IVA):</strong> $
                    {(selectedArticle as ArticuloAdminView).pcio_com_siva.toLocaleString()}
                  </div>
                )}
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Conteo Físico Observado
              </label>
              <input
                type="number"
                min="0"
                value={physicalCount}
                onChange={(e) => setPhysicalCount(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-sm text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                placeholder="Ej. 48"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Lote (Opcional)
              </label>
              <input
                type="text"
                value={lotNumber}
                onChange={(e) => setLotNumber(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-sm text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                placeholder="Ej. L-2026-X"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">
                Observaciones del Operador
              </label>
              <textarea
                rows={2}
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-sm text-white focus:ring-2 focus:ring-indigo-500 focus:outline-none resize-none"
                placeholder="Motivo de discrepancia, estado del lote..."
              />
            </div>

            <button
              type="submit"
              className="w-full py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-semibold shadow transition"
            >
              Registrar Auditoría en Memoria
            </button>
          </form>

          {auditFeedback && (
            <div className="p-3 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200">
              {auditFeedback}
            </div>
          )}
        </div>

        {/* Articles Table & Audit Log */}
        <div className="lg:col-span-2 space-y-6">
          {/* Article List */}
          <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800">
            <h2 className="text-lg font-bold text-white mb-3 flex items-center justify-between">
              <span>📦 Catálogo de Artículos (Vista Reactiva: {currentRole})</span>
              <span className="text-xs font-normal text-slate-400">
                {articles.filter((a) => a.fue_auditado).length}/{articles.length} Auditados
              </span>
            </h2>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
                  <tr>
                    <th className="p-2.5">Código / Barras</th>
                    <th className="p-2.5">Descripción</th>
                    <th className="p-2.5">Familia</th>
                    <th className="p-2.5 text-right">Stock Real</th>
                    {isAdmin && <th className="p-2.5 text-right text-amber-400">Costo s/IVA</th>}
                    <th className="p-2.5 text-center">Estado</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {articles.map((art) => {
                    const hasAdminCost = "pcio_com_siva" in art;
                    return (
                      <tr
                        key={art.id_articulo}
                        className={`hover:bg-slate-800/40 transition ${
                          art.fue_auditado ? "bg-slate-900/30" : ""
                        }`}
                      >
                        <td className="p-2.5 font-mono">
                          <div className="text-white font-medium">{art.id_articulo}</div>
                          <div className="text-slate-500 text-[10px]">
                            {art.cod_barras.join(", ")}
                          </div>
                        </td>
                        <td className="p-2.5 max-w-[200px] truncate" title={art.des_articulo}>
                          <div className="text-slate-200 font-medium">{art.des_articulo}</div>
                          <div className="text-slate-500">{art.presentacion || "-"}</div>
                        </td>
                        <td className="p-2.5">{art.des_familia}</td>
                        <td className="p-2.5 text-right font-bold text-white">
                          {art.stock_real}
                        </td>
                        {isAdmin && (
                          <td className="p-2.5 text-right font-mono text-amber-400">
                            {hasAdminCost
                              ? `$${(art as ArticuloAdminView).pcio_com_siva.toLocaleString()}`
                              : "N/A"}
                          </td>
                        )}
                        <td className="p-2.5 text-center">
                          {art.fue_auditado ? (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-950 text-emerald-300 border border-emerald-800/60">
                              Auditado ({art.ultimo_conteo_fisico})
                            </span>
                          ) : (
                            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-800 text-slate-400 border border-slate-700">
                              Pendiente
                            </span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          {/* Audit Logs Table */}
          <div className="bg-slate-900 p-5 rounded-2xl border border-slate-800">
            <h2 className="text-lg font-bold text-white mb-3">
              📋 Historial de Registros de Auditoría
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs text-slate-300">
                <thead className="bg-slate-950 text-slate-400 font-semibold border-b border-slate-800">
                  <tr>
                    <th className="p-2.5">Artículo</th>
                    <th className="p-2.5 text-right">Teórico</th>
                    <th className="p-2.5 text-right">Físico</th>
                    <th className="p-2.5 text-center">Discrepancia</th>
                    <th className="p-2.5 text-center">Tipo</th>
                    {isAdmin && (
                      <th className="p-2.5 text-right text-amber-400">Valorización</th>
                    )}
                    <th className="p-2.5">Observación</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {auditLogs.map((log) => (
                    <tr key={log.client_uuid} className="hover:bg-slate-800/30">
                      <td className="p-2.5">
                        <div className="font-medium text-white">{log.id_articulo}</div>
                        <div className="text-slate-500 text-[10px] truncate max-w-[150px]">
                          {log.des_articulo}
                        </div>
                      </td>
                      <td className="p-2.5 text-right">{log.stock_real}</td>
                      <td className="p-2.5 text-right font-bold text-white">
                        {log.stock_fisico_contado}
                      </td>
                      <td
                        className={`p-2.5 text-center font-bold ${
                          log.delta_stock > 0
                            ? "text-emerald-400"
                            : log.delta_stock < 0
                            ? "text-rose-400"
                            : "text-slate-400"
                        }`}
                      >
                        {log.delta_stock > 0 ? `+${log.delta_stock}` : log.delta_stock}
                      </td>
                      <td className="p-2.5 text-center">
                        <span
                          className={`inline-flex px-2 py-0.5 rounded text-[10px] font-semibold ${
                            log.tipo_accion === TipoAccion.ALTA
                              ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                              : log.tipo_accion === TipoAccion.BAJA
                              ? "bg-rose-950 text-rose-300 border border-rose-800"
                              : "bg-slate-800 text-slate-300 border border-slate-700"
                          }`}
                        >
                          {log.tipo_accion}
                        </span>
                      </td>
                      {isAdmin && (
                        <td className="p-2.5 text-right font-mono text-amber-400">
                          ${log.monto_valorizado.toLocaleString()}
                        </td>
                      )}
                      <td className="p-2.5 text-slate-400 max-w-[200px] truncate" title={log.observation || undefined}>
                        {log.observation || "-"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
