import React from "react";

export function ReportSkeleton() {
  return (
    <div className="space-y-6 animate-pulse" aria-label="Cargando reporte...">
      {/* Top Filter Skeleton */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 flex flex-col sm:flex-row justify-between gap-4">
        <div className="flex gap-4">
          <div className="h-10 w-36 bg-slate-200 rounded-lg"></div>
          <div className="h-10 w-36 bg-slate-200 rounded-lg"></div>
        </div>
        <div className="h-10 w-32 bg-slate-200 rounded-lg"></div>
      </div>

      {/* KPI Cards Skeleton */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-xl border border-slate-200 h-32 flex flex-col justify-between">
          <div className="h-4 w-24 bg-slate-200 rounded"></div>
          <div className="h-8 w-36 bg-slate-200 rounded"></div>
          <div className="h-3 w-48 bg-slate-100 rounded"></div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 h-32 flex flex-col justify-between">
          <div className="h-4 w-24 bg-slate-200 rounded"></div>
          <div className="h-8 w-36 bg-slate-200 rounded"></div>
          <div className="h-3 w-48 bg-slate-100 rounded"></div>
        </div>
        <div className="bg-white p-6 rounded-xl border border-slate-200 h-32 flex flex-col justify-between">
          <div className="h-4 w-24 bg-slate-200 rounded"></div>
          <div className="h-8 w-36 bg-slate-200 rounded"></div>
          <div className="h-3 w-48 bg-slate-100 rounded"></div>
        </div>
      </div>

      {/* Table / Content Skeleton */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 space-y-4">
        <div className="h-6 w-48 bg-slate-200 rounded mb-6"></div>
        <div className="space-y-3">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-10 bg-slate-100 rounded-lg w-full"></div>
          ))}
        </div>
      </div>
    </div>
  );
}
