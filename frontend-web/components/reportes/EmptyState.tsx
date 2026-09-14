import React from "react";
import { Inbox, RefreshCcw } from "lucide-react";

export interface EmptyStateProps {
  title?: string;
  description?: string;
  onClearFilters?: () => void;
  icon?: React.ElementType;
}

export function EmptyState({
  title = "No se encontraron registros",
  description = "No hay datos disponibles para el rango de fechas o filtros seleccionados.",
  onClearFilters,
  icon: Icon = Inbox,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4 bg-white rounded-xl border border-slate-200 text-center shadow-sm">
      <div className="w-14 h-14 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-400 mb-4">
        <Icon className="w-7 h-7" />
      </div>
      <h3 className="text-base font-semibold text-slate-800 mb-1">{title}</h3>
      <p className="text-sm text-slate-500 max-w-sm mb-6">{description}</p>
      {onClearFilters && (
        <button
          type="button"
          onClick={onClearFilters}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 transition-colors border border-slate-200"
        >
          <RefreshCcw className="w-3.5 h-3.5" />
          <span>Restablecer Filtros</span>
        </button>
      )}
    </div>
  );
}
