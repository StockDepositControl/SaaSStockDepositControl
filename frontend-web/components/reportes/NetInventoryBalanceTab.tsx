"use client";

import React, { useState } from "react";
import { ArticuloAdminView, ArticuloPublicView, AuditResult, TipoAccion } from "@/lib/types/domain";
import { SummaryKPICard } from "./SummaryKPICard";
import { BarChart3, TrendingUp, TrendingDown, Layers, ArrowUpRight, ArrowDownRight } from "lucide-react";

export interface NetInventoryBalanceTabProps {
  articles: (ArticuloPublicView | ArticuloAdminView)[];
  auditLogs: AuditResult[];
  startDate?: string;
  endDate?: string;
  onClearFilters?: () => void;
}

export function NetInventoryBalanceTab({
  articles,
  auditLogs,
}: NetInventoryBalanceTabProps) {
  const [chartView, setChartView] = useState<"daily" | "family">("daily");

  // Calculate Total Stock & Stock Valuation (for admin)
  const totalUnitsInStock = articles.reduce((acc, art) => acc + art.stock_real, 0);

  const totalStockValuation = articles.reduce((acc, art) => {
    const cost = "pcio_com_siva" in art ? (art as ArticuloAdminView).pcio_com_siva : 0;
    return acc + cost * art.stock_real;
  }, 0);

  // Net variation from audit logs
  const totalAltas = auditLogs
    .filter((l) => l.tipo_accion === TipoAccion.ALTA)
    .reduce((acc, l) => acc + l.monto_valorizado, 0);

  const totalBajas = auditLogs
    .filter((l) => l.tipo_accion === TipoAccion.BAJA)
    .reduce((acc, l) => acc + l.monto_valorizado, 0);

  const netVariation = totalAltas - totalBajas;
  const isNegativeVariation = netVariation < 0;

  // Aggregate data by family
  const familyBreakdown = React.useMemo(() => {
    const map = new Map<
      string,
      { family: string; units: number; valuation: number; itemsCount: number }
    >();

    articles.forEach((art) => {
      const familyName = art.des_familia || "Sin Familia";
      const cost = "pcio_com_siva" in art ? (art as ArticuloAdminView).pcio_com_siva : 0;
      const current = map.get(familyName) || {
        family: familyName,
        units: 0,
        valuation: 0,
        itemsCount: 0,
      };

      current.units += art.stock_real;
      current.valuation += cost * art.stock_real;
      current.itemsCount += 1;
      map.set(familyName, current);
    });

    return Array.from(map.values()).sort((a, b) => b.valuation - a.valuation);
  }, [articles]);

  // Mock daily historical trend (7 days sequence)
  const dailyTrends = React.useMemo(() => {
    const days = ["12/08", "13/08", "14/08", "15/08", "16/08", "17/08", "18/08"];
    const baseValuation = totalStockValuation > 0 ? totalStockValuation : 320000;

    return days.map((day, idx) => {
      // Simulate minor fluctuation around total stock
      const dayFactor = 0.96 + idx * 0.008;
      const valuation = Math.round(baseValuation * dayFactor);
      const altas = idx % 2 === 0 ? 3750 : 1200;
      const bajas = idx % 3 === 0 ? 4450 : 900;
      return {
        day,
        valuation,
        altas,
        bajas,
        net: altas - bajas,
      };
    });
  }, [totalStockValuation]);

  const maxDailyValuation = Math.max(...dailyTrends.map((d) => d.valuation), 1);
  const minDailyValuation = Math.min(...dailyTrends.map((d) => d.valuation), 0) * 0.9;

  return (
    <div className="space-y-6">
      {/* KPI Cards Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <SummaryKPICard
          title="Stock Total Valorizado"
          amount={totalStockValuation}
          quantity={totalUnitsInStock}
          quantityLabel="unidades totales"
          subtitle="Valor actualizado del inventario en depósito"
          icon={BarChart3}
        />
        <SummaryKPICard
          title="Variación Neta del Período"
          amount={Math.abs(netVariation)}
          isLoss={isNegativeVariation}
          subtitle={
            isNegativeVariation
              ? `Pérdida neta de -$${Math.abs(netVariation).toLocaleString("es-AR")}`
              : `Ganancia / Incremento neto de +$${netVariation.toLocaleString("es-AR")}`
          }
          icon={isNegativeVariation ? TrendingDown : TrendingUp}
        />
        <SummaryKPICard
          title="Artículos Monitoreados"
          amount={articles.length}
          quantityLabel="familias"
          quantity={familyBreakdown.length}
          subtitle="Líneas de productos con control de lote"
          icon={Layers}
        />
      </div>

      {/* Interactive Chart Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 sm:p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <h2 className="text-sm font-bold text-slate-800 tracking-tight">
              Evolución y Balance Neto Diario
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Valuación histórica del stock e impacto diario de auditorías
            </p>
          </div>
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg">
            <button
              type="button"
              onClick={() => setChartView("daily")}
              className={`px-3 py-1 rounded-md text-xs font-semibold transition-all cursor-pointer ${
                chartView === "daily"
                  ? "bg-white text-[#0F2C59] shadow-xs"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              Evolución Diaria
            </button>
            <button
              type="button"
              onClick={() => setChartView("family")}
              className={`px-3 py-1 rounded-md text-xs font-semibold transition-all cursor-pointer ${
                chartView === "family"
                  ? "bg-white text-[#0F2C59] shadow-xs"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              Distribución por Familia
            </button>
          </div>
        </div>

        {chartView === "daily" ? (
          <div className="mt-6">
            {/* SVG Interactive Chart */}
            <div className="h-64 w-full flex items-end gap-3 sm:gap-6 pt-8 pb-2 px-2">
              {dailyTrends.map((item, idx) => {
                const heightPercent = Math.max(
                  15,
                  Math.round(
                    ((item.valuation - minDailyValuation) /
                      (maxDailyValuation - minDailyValuation || 1)) *
                      100
                  )
                );

                return (
                  <div
                    key={item.day}
                    className="flex-1 flex flex-col items-center h-full justify-end group relative"
                  >
                    {/* Tooltip on hover */}
                    <div className="absolute -top-12 left-1/2 -translate-x-1/2 hidden group-hover:flex flex-col items-center bg-slate-900 text-white text-[11px] px-2.5 py-1.5 rounded-md shadow-lg z-30 pointer-events-none whitespace-nowrap">
                      <span className="font-mono font-bold">
                        ${item.valuation.toLocaleString("es-AR")}
                      </span>
                      <span className="text-[9px] text-slate-300">
                        Neto: {item.net >= 0 ? `+$${item.net}` : `-$${Math.abs(item.net)}`}
                      </span>
                    </div>

                    {/* Bar representation */}
                    <div className="w-full max-w-[48px] bg-slate-100 rounded-t-lg overflow-hidden flex flex-col justify-end h-full">
                      <div
                        style={{ height: `${heightPercent}%` }}
                        className="w-full bg-[#0F2C59] hover:bg-[#1565C0] transition-all rounded-t-md relative flex items-center justify-center group-hover:brightness-110"
                      >
                        {item.net !== 0 && (
                          <span
                            className={`hidden sm:inline-block absolute -top-5 text-[10px] font-mono font-bold ${
                              item.net > 0 ? "text-emerald-600" : "text-red-500"
                            }`}
                          >
                            {item.net > 0 ? "+" : "-"}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Day label */}
                    <span className="text-[11px] font-mono font-medium text-slate-500 mt-2">
                      {item.day}
                    </span>
                  </div>
                );
              })}
            </div>

            <div className="flex items-center justify-center gap-6 mt-4 text-xs text-slate-500 border-t border-slate-100 pt-3">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded bg-[#0F2C59]"></div>
                <span>Valuación Stock Diario ($)</span>
              </div>
              <div className="flex items-center gap-2">
                <ArrowUpRight className="w-3.5 h-3.5 text-emerald-600" />
                <span>Ingreso Neto</span>
              </div>
              <div className="flex items-center gap-2">
                <ArrowDownRight className="w-3.5 h-3.5 text-red-500" />
                <span>Merma Neta</span>
              </div>
            </div>
          </div>
        ) : (
          /* Family Distribution Breakdown Chart */
          <div className="mt-6 space-y-4">
            {familyBreakdown.map((fam) => {
              const sharePercent =
                totalStockValuation > 0
                  ? Math.round((fam.valuation / totalStockValuation) * 100)
                  : 0;

              return (
                <div key={fam.family} className="space-y-1.5">
                  <div className="flex justify-between text-xs font-semibold">
                    <span className="text-slate-700">{fam.family}</span>
                    <span className="font-mono text-slate-900">
                      ${fam.valuation.toLocaleString("es-AR", { minimumFractionDigits: 2 })} ({sharePercent}%)
                    </span>
                  </div>
                  <div className="h-2.5 w-full bg-slate-100 rounded-full overflow-hidden">
                    <div
                      style={{ width: `${Math.max(sharePercent, 4)}%` }}
                      className="h-full bg-[#0F2C59] rounded-full transition-all"
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Breakdown Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="p-4 sm:p-5 border-b border-slate-100 flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-800 tracking-tight">
            Consolidado de Existencias por Familia
          </h2>
          <span className="text-xs font-semibold text-slate-500 bg-slate-100 px-2.5 py-1 rounded-full">
            {familyBreakdown.length} familias
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs sm:text-sm text-slate-600">
            <thead className="text-[11px] font-bold text-slate-400 uppercase tracking-wider border-b border-slate-200 bg-slate-50/70">
              <tr>
                <th className="px-5 py-3.5">Familia de Productos</th>
                <th className="px-5 py-3.5 text-right whitespace-nowrap">Líneas de Artículos</th>
                <th className="px-5 py-3.5 text-right whitespace-nowrap">Unidades en Depósito</th>
                <th className="px-5 py-3.5 text-right whitespace-nowrap">Valuación Total</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {familyBreakdown.map((fam) => (
                <tr key={fam.family} className="hover:bg-slate-50/60 transition-colors">
                  <td className="px-5 py-4 font-semibold text-slate-900">{fam.family}</td>
                  <td className="px-5 py-4 text-right font-mono text-slate-600">
                    {fam.itemsCount}
                  </td>
                  <td className="px-5 py-4 text-right font-mono font-bold text-slate-800">
                    {fam.units.toLocaleString("es-AR")}
                  </td>
                  <td className="px-5 py-4 text-right font-mono font-bold text-slate-900 bg-slate-50/40">
                    $
                    {fam.valuation.toLocaleString("es-AR", {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </td>
                </tr>
              ))}
            </tbody>
            <tfoot className="border-t-2 border-slate-200 bg-slate-50/80 text-slate-900 font-bold">
              <tr>
                <td className="px-5 py-3.5 text-xs uppercase tracking-wider">Total General</td>
                <td className="px-5 py-3.5 text-right font-mono">{articles.length}</td>
                <td className="px-5 py-3.5 text-right font-mono">
                  {totalUnitsInStock.toLocaleString("es-AR")}
                </td>
                <td className="px-5 py-3.5 text-right font-mono text-sm bg-slate-100/60">
                  $
                  {totalStockValuation.toLocaleString("es-AR", {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  })}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>
    </div>
  );
}
