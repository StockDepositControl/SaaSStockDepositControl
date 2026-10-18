"use client";

import React from "react";
import { useDataClient } from "@/lib/hooks/useDataClient";
import { UserRole } from "@/lib/types/domain";
import { DemoShell } from "@/components/layout/DemoShell";
import { DataTable } from "@/components/ui/DataTable";
import { Lock } from "lucide-react";

export default function CatalogPage() {
  const { articles, currentRole } = useDataClient();
  const isAdmin = currentRole === UserRole.ADMINISTRADOR;
  const isSupervisor = currentRole === UserRole.SUPERVISOR;

  const subtitle = isAdmin
    ? `${articles.length} artículos · Precios visibles (Vista de administrador)`
    : isSupervisor
    ? `${articles.length} artículos · Stock, estado de auditoría y trazabilidad del auditor`
    : `${articles.length} artículos · Stock y estado de auditoría`;

  return (
    <DemoShell>
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
              Catálogo de Artículos
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-1">
              {subtitle}
            </p>
          </div>
          
          {isAdmin && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-[#eff6ff] border border-[#dbeafe] text-[#1e429f] text-sm font-medium">
              <Lock className="w-4 h-4" />
              <span>Columna de costo — restringido</span>
            </div>
          )}
        </div>

        {/* Main Data Table */}
        <div className="w-full">
          <DataTable
            articles={articles}
            currentRole={currentRole || UserRole.AUDITOR}
          />
        </div>
      </div>
    </DemoShell>
  );
}
