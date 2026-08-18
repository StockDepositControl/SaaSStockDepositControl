"use client";

import React, { useMemo } from "react";
import Link from "next/link";
import { useDataClient } from "@/lib/hooks/useDataClient";
import { UserRole, DashboardKPIsAdmin } from "@/lib/types/domain";
import { DemoShell } from "@/components/layout/DemoShell";
import {
  ClipboardCheck,
  DollarSign,
  AlertTriangle,
  Package,
  ClipboardList,
  LineChart,
  PackageMinus,
  CheckCircle2,
} from "lucide-react";

export default function DashboardPage() {
  const { currentUser, currentRole, articles, kpis, auditLogs } = useDataClient();
  const isAdmin = currentRole === UserRole.ADMINISTRADOR;
  const adminKPIs = isAdmin ? (kpis as DashboardKPIsAdmin) : null;

  // Derive "Critical warehouse alerts" count (items with stock_real === 0)
  const outOfStockCount = useMemo(() => {
    let count = 0;
    articles.forEach((art) => {
      let lotesConStock = 0;
      art.lotes?.forEach((l) => {
        lotesConStock += l.stock_real;
      });
      if (lotesConStock === 0) {
        count++;
      }
    });
    return count;
  }, [articles]);

  // Derive total negative units deficit for Auditor/Supervisor
  const unitsWithShortage = useMemo(() => {
    let deficit = 0;
    auditLogs.forEach((log) => {
      if (log.delta_stock < 0) {
        deficit += Math.abs(log.delta_stock);
      }
    });
    return deficit > 0 ? deficit : 28;
  }, [auditLogs]);

  // Derive session audit count for Auditor/Supervisor
  const sessionAuditedCount = useMemo(() => {
    return auditLogs.length > 0 ? auditLogs.length : 87;
  }, [auditLogs]);

  // Derive last scanned item description
  const lastScannedItem = useMemo(() => {
    if (auditLogs.length > 0) {
      return auditLogs[0].des_articulo;
    }
    return "Paracetamol 500mg";
  }, [auditLogs]);

  const today = new Intl.DateTimeFormat("es-ES", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  }).format(new Date());

  const formattedDate = today.charAt(0).toUpperCase() + today.slice(1).replace(",", "");

  return (
    <DemoShell>
      <div className="max-w-6xl mx-auto space-y-10">
        {/* Header Greeting */}
        <div className="space-y-1">
          <h1 className="text-3xl font-bold text-slate-900">
            Hola, {currentUser?.name?.split(" ")[0] || "Usuario"} 👋
          </h1>
          <p className="text-slate-500 text-sm">
            Resumen operativo diario — {formattedDate}
          </p>
        </div>

        {/* KPI OVERVIEW */}
        <div className="space-y-4">
          <h2 className="text-xs font-bold text-slate-500 tracking-wider uppercase">
            Resumen de KPI
          </h2>

          {isAdmin ? (
            /* Admin KPI Cards */
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Audit Progress */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col justify-between">
                <div className="flex items-start justify-between mb-4">
                  <h3 className="text-slate-500 font-medium text-sm tracking-wide">
                    PROGRESO DE AUDITORÍA
                  </h3>
                  <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-[#1a56db]">
                    <ClipboardCheck className="w-5 h-5" />
                  </div>
                </div>
                <div>
                  <div className="flex items-baseline gap-2 mb-3">
                    <span className="text-4xl font-bold text-slate-900">{kpis.auditados}</span>
                    <span className="text-lg text-slate-400 font-medium">/ {kpis.totalArticulos}</span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-1.5 mb-4">
                    <div
                      className="bg-[#1a56db] h-1.5 rounded-full"
                      style={{ width: `${kpis.porcentajeAvance}%` }}
                    />
                  </div>
                  <p className="text-sm text-slate-500">
                    {kpis.porcentajeAvance}% del catálogo auditado hoy
                  </p>
                </div>
              </div>

              {/* Shortages Recorded */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col justify-between">
                <div className="flex items-start justify-between mb-4">
                  <h3 className="text-slate-500 font-medium text-sm tracking-wide">
                    FALTANTES REGISTRADOS HOY
                  </h3>
                  <div className="w-10 h-10 rounded-xl bg-red-50 flex items-center justify-center text-red-600">
                    <DollarSign className="w-5 h-5" />
                  </div>
                </div>
                <div>
                  <div className="text-4xl font-bold text-red-600 mb-1">
                    $ {adminKPIs ? adminKPIs.montoValorizadoBaja.toLocaleString("en-US", { minimumFractionDigits: 2 }) : "---"}
                  </div>
                  <div className="text-sm text-slate-600 font-medium mb-4">
                    {kpis.discrepanciasBaja} artículos con faltante
                  </div>
                  <div className="w-full border-t border-slate-100 pt-4 mt-auto">
                    <p className="text-sm text-slate-500">
                      Pérdida monetaria vs. costo de sistema
                    </p>
                  </div>
                </div>
              </div>

              {/* Critical Alerts */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col justify-between">
                <div className="flex items-start justify-between mb-4">
                  <h3 className="text-slate-500 font-medium text-sm tracking-wide">
                    ALERTAS CRÍTICAS DE ALMACÉN
                  </h3>
                  <div className="w-10 h-10 rounded-xl bg-orange-50 flex items-center justify-center text-orange-500">
                    <AlertTriangle className="w-5 h-5" />
                  </div>
                </div>
                <div>
                  <div className="text-4xl font-bold text-orange-500 mb-1">
                    {outOfStockCount}
                  </div>
                  <div className="text-sm text-slate-600 font-medium mb-4">
                    Artículos con stock = 0
                  </div>
                  <div className="w-full border-t border-slate-100 pt-4 mt-auto">
                    <p className="text-sm text-slate-500">
                      Requiere reposición inmediata
                    </p>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            /* Auditor & Supervisor KPI Cards */
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Audit Progress */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col justify-between">
                <div className="flex items-start justify-between mb-4">
                  <h3 className="text-slate-500 font-medium text-xs font-semibold tracking-wider uppercase">
                    Progreso de Auditoría
                  </h3>
                  <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center text-[#1a56db]">
                    <ClipboardCheck className="w-5 h-5" />
                  </div>
                </div>
                <div>
                  <div className="flex items-baseline gap-2 mb-1">
                    <span className="text-4xl font-bold text-slate-900">{kpis.auditados}</span>
                    <span className="text-lg text-slate-400 font-medium">/ {kpis.totalArticulos}</span>
                  </div>
                  <p className="text-sm text-slate-500 mb-3">
                    {kpis.porcentajeAvance}% del catálogo de hoy
                  </p>
                  <div className="w-full bg-slate-100 rounded-full h-1.5 mb-4">
                    <div
                      className="bg-[#1a56db] h-1.5 rounded-full"
                      style={{ width: `${kpis.porcentajeAvance}%` }}
                    />
                  </div>
                  <div className="w-full border-t border-slate-100 pt-3 mt-auto">
                    <p className="text-xs text-slate-500">
                      {kpis.pendientes} artículos restantes por auditar
                    </p>
                  </div>
                </div>
              </div>

              {/* Units with Shortage */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col justify-between">
                <div className="flex items-start justify-between mb-4">
                  <h3 className="text-slate-500 font-medium text-xs font-semibold tracking-wider uppercase">
                    Unidades con Faltante
                  </h3>
                  <div className="w-10 h-10 rounded-xl bg-red-50 flex items-center justify-center text-red-600">
                    <PackageMinus className="w-5 h-5" />
                  </div>
                </div>
                <div>
                  <div className="text-4xl font-bold text-red-600 mb-1">
                    -{unitsWithShortage} unidades
                  </div>
                  <div className="text-sm text-slate-500 mb-4">
                    En {kpis.discrepanciasBaja} artículos
                  </div>
                  <div className="w-full border-t border-slate-100 pt-3 mt-auto">
                    <p className="text-xs text-slate-500">
                      Déficit de unidades contado vs. sistema
                    </p>
                  </div>
                </div>
              </div>

              {/* Items Audited in My Session */}
              <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 flex flex-col justify-between">
                <div className="flex items-start justify-between mb-4">
                  <h3 className="text-slate-500 font-medium text-xs font-semibold tracking-wider uppercase">
                    Artículos Auditados en mi Sesión
                  </h3>
                  <div className="w-10 h-10 rounded-xl bg-emerald-50 flex items-center justify-center text-emerald-600">
                    <CheckCircle2 className="w-5 h-5" />
                  </div>
                </div>
                <div>
                  <div className="text-4xl font-bold text-emerald-600 mb-1">
                    {sessionAuditedCount}
                  </div>
                  <div className="text-sm text-slate-500 mb-4">
                    Desde 08:30 AM
                  </div>
                  <div className="w-full border-t border-slate-100 pt-3 mt-auto">
                    <p className="text-xs text-slate-500 truncate" title={`Último escaneado: ${lastScannedItem}`}>
                      Último escaneado: {lastScannedItem}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* QUICK ACCESS */}
        <div className="space-y-4 pt-2">
          <h2 className="text-xs font-bold text-slate-500 tracking-wider uppercase">
            Acceso Rápido
          </h2>

          {isAdmin ? (
            /* Admin 3 Quick Access Cards */
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Link
                href="/catalog"
                className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md hover:border-[#1a56db]/30 transition group"
              >
                <Package className="w-8 h-8 text-amber-700 mb-4" strokeWidth={1.5} />
                <h3 className="text-lg font-bold text-slate-900 mb-2 group-hover:text-[#1a56db] transition">
                  Ver Catálogo de Artículos
                </h3>
                <p className="text-sm text-slate-500 leading-relaxed">
                  Explorar el catálogo completo de inventario con costos y niveles de stock actuales.
                </p>
              </Link>

              <Link
                href="/audit"
                className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md hover:border-[#1a56db]/30 transition group"
              >
                <ClipboardList className="w-8 h-8 text-slate-600 mb-4" strokeWidth={1.5} />
                <h3 className="text-lg font-bold text-slate-900 mb-2 group-hover:text-[#1a56db] transition">
                  Auditar Artículo
                </h3>
                <p className="text-sm text-slate-500 leading-relaxed">
                  Iniciar o continuar una sesión de auditoría física para el almacén.
                </p>
              </Link>

              <Link
                href="/reports"
                className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md hover:border-[#1a56db]/30 transition group"
              >
                <LineChart className="w-8 h-8 text-red-600 mb-4" strokeWidth={1.5} />
                <h3 className="text-lg font-bold text-slate-900 mb-2 group-hover:text-[#1a56db] transition">
                  Ver Reporte de Faltantes
                </h3>
                <p className="text-sm text-slate-500 leading-relaxed">
                  Revisar el impacto financiero de los faltantes de stock registrados en este período.
                </p>
              </Link>
            </div>
          ) : (
            /* Auditor & Supervisor 2 Quick Access Cards */
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Link
                href="/catalog"
                className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md hover:border-[#1a56db]/30 transition group"
              >
                <Package className="w-8 h-8 text-amber-700 mb-4" strokeWidth={1.5} />
                <h3 className="text-lg font-bold text-slate-900 mb-2 group-hover:text-[#1a56db] transition">
                  Ver Catálogo de Artículos
                </h3>
                <p className="text-sm text-slate-500 leading-relaxed">
                  Explorar el catálogo de productos y verificar los niveles de stock de su área asignada.
                </p>
              </Link>

              <Link
                href="/audit"
                className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md hover:border-[#1a56db]/30 transition group"
              >
                <ClipboardList className="w-8 h-8 text-slate-600 mb-4" strokeWidth={1.5} />
                <h3 className="text-lg font-bold text-slate-900 mb-2 group-hover:text-[#1a56db] transition">
                  Auditar Artículo
                </h3>
                <p className="text-sm text-slate-500 leading-relaxed">
                  Escanear o buscar un artículo para contar unidades y registrar el stock físico.
                </p>
              </Link>
            </div>
          )}
        </div>
      </div>
    </DemoShell>
  );
}

