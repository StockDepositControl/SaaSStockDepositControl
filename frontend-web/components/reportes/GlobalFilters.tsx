"use client";

import React from "react";
import { Download, Calendar } from "lucide-react";

export interface GlobalFiltersProps {
  startDate: string;
  endDate: string;
  onStartDateChange: (date: string) => void;
  onEndDateChange: (date: string) => void;
  onExport: () => void;
  isExporting?: boolean;
}

export function GlobalFilters({
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
  onExport,
  isExporting = false,
}: GlobalFiltersProps) {
  return (
    <div className="sticky top-0 z-20 bg-white/95 backdrop-blur-md rounded-xl border border-slate-200 shadow-sm p-4 sm:p-5 transition-all">
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        {/* Left Side: Date Range Selectors */}
        <div className="flex flex-wrap items-center gap-3 sm:gap-6">
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-slate-400 shrink-0" />
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Período:</span>
          </div>

          <div className="flex items-center gap-2">
            <label htmlFor="filter-start-date" className="text-xs text-slate-500 font-medium">
              Desde:
            </label>
            <input
              id="filter-start-date"
              type="date"
              value={startDate}
              onChange={(e) => onStartDateChange(e.target.value)}
              className="border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs sm:text-sm text-slate-700 bg-white hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-[#0F2C59]/20 focus:border-[#0F2C59] transition-all font-mono"
            />
          </div>

          <div className="flex items-center gap-2">
            <label htmlFor="filter-end-date" className="text-xs text-slate-500 font-medium">
              Hasta:
            </label>
            <input
              id="filter-end-date"
              type="date"
              value={endDate}
              onChange={(e) => onEndDateChange(e.target.value)}
              className="border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs sm:text-sm text-slate-700 bg-white hover:border-slate-300 focus:outline-none focus:ring-2 focus:ring-[#0F2C59]/20 focus:border-[#0F2C59] transition-all font-mono"
            />
          </div>
        </div>

        {/* Right Side: Export Action */}
        <div className="flex items-center justify-end gap-2">
          <button
            type="button"
            onClick={onExport}
            disabled={isExporting}
            className="inline-flex items-center justify-center gap-2 border border-slate-300 bg-white hover:bg-slate-50 active:bg-slate-100 text-slate-700 font-semibold px-4 py-2 rounded-lg text-xs sm:text-sm transition-all shadow-sm disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            <Download className="w-4 h-4 text-slate-600" />
            <span>{isExporting ? "Exportando..." : "Exportar Excel"}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
