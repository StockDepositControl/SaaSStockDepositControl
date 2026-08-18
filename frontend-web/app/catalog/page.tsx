"use client";

import React from "react";
import { useDataClient } from "@/lib/hooks/useDataClient";
import { DemoShell } from "@/components/layout/DemoShell";
import { DataTable } from "@/components/ui/DataTable";
import { PackageSearch, Calendar } from "lucide-react";

export default function CatalogPage() {
  const { articles, currentRole } = useDataClient();

  return (
    <DemoShell>
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
              <PackageSearch className="w-8 h-8 text-indigo-400" />
              <span>Catálogo de Artículos</span>
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Consulta el maestro de artículos, stock teórico y matrices de vencimiento FEFO.
            </p>
          </div>
          <div className="px-3 py-1.5 rounded-full bg-slate-900 border border-slate-800 text-xs text-slate-400 flex items-center gap-2 shadow-inner">
            <Calendar className="w-3.5 h-3.5" />
            <span>Actualizado en tiempo real</span>
          </div>
        </div>

        {/* Main Data Table */}
        <div className="bg-slate-900/40 rounded-2xl p-1 border border-slate-800 shadow-2xl">
          <DataTable
            articles={articles}
            currentRole={currentRole!}
            title="Maestro de Artículos (Depósito 01)"
          />
        </div>
      </div>
    </DemoShell>
  );
}
