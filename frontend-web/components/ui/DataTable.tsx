"use client";

import React, { useState, useMemo } from "react";
import { ArticuloPublicView, ArticuloAdminView, UserRole } from "@/lib/types/domain";
import { useDataClient } from "@/lib/hooks/useDataClient";
import { Search, ChevronDown, AlertTriangle, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from "lucide-react";

export interface DataTableProps {
  articles: (ArticuloPublicView | ArticuloAdminView)[];
  currentRole: UserRole;
  isLoading?: boolean;
}

export function DataTable({ articles, currentRole, isLoading = false }: DataTableProps) {
  const emptyMessage = isLoading ? "Cargando artículos..." : "No se encontraron resultados.";
  const { users } = useDataClient();
  const [searchTerm, setSearchTerm] = useState("");
  const [familyFilter, setFamilyFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  const isAdmin = currentRole === UserRole.ADMINISTRADOR;
  const isSupervisor = currentRole === UserRole.SUPERVISOR;

  // Extract unique families
  const families = useMemo(() => {
    const set = new Set<string>();
    articles.forEach((a) => {
      if (a.des_familia) set.add(a.des_familia);
    });
    return Array.from(set);
  }, [articles]);

  const filteredArticles = useMemo(() => {
    const term = searchTerm.toLowerCase().trim();

    return articles.filter((art) => {
      const matchesSearch =
        !term ||
        art.id_articulo.toLowerCase().includes(term) ||
        art.des_articulo.toLowerCase().includes(term) ||
        (art.des_marca && art.des_marca.toLowerCase().includes(term)) ||
        Boolean(art.cod_barras?.some((cb) => cb.includes(term)));

      const matchesFamily = familyFilter === "all" || art.des_familia === familyFilter;
      
      const matchesStatus = 
        statusFilter === "all" || 
        (statusFilter === "audited" && art.fue_auditado) || 
        (statusFilter === "pending" && !art.fue_auditado);

      return matchesSearch && matchesFamily && matchesStatus;
    });
  }, [articles, searchTerm, familyFilter, statusFilter]);

  const totalPages = Math.ceil(filteredArticles.length / itemsPerPage);
  const paginatedArticles = filteredArticles.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  // Helper for deterministic mock auditor
  const getAuditorForArticle = (articleId: string) => {
    const auditors = users.filter(u => u.role === UserRole.AUDITOR || u.role === UserRole.SUPERVISOR);
    if (auditors.length === 0) return null;
    const index = articleId.split("").reduce((acc, char) => acc + char.charCodeAt(0), 0);
    return auditors[index % auditors.length];
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden flex flex-col">
      {/* Top Bar: Filters */}
      <div className="p-4 border-b border-slate-200 flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 w-full lg:flex-1">
          {/* Search Input */}
          <div className="relative w-full sm:flex-1">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => { setSearchTerm(e.target.value); setCurrentPage(1); }}
              placeholder="Buscar código de barras o nombre..."
              className="w-full pl-9 pr-3 py-2 text-sm bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:outline-none focus:border-[#1a56db] focus:ring-1 focus:ring-[#1a56db] transition"
            />
          </div>

          {/* Family Filter */}
          <div className="relative w-full sm:w-48">
            <select
              value={familyFilter}
              onChange={(e) => { setFamilyFilter(e.target.value); setCurrentPage(1); }}
              className="w-full appearance-none pl-3 pr-8 py-2 text-sm bg-white border border-slate-300 rounded-lg text-slate-700 focus:outline-none focus:border-[#1a56db] focus:ring-1 focus:ring-[#1a56db] transition cursor-pointer"
            >
              <option value="all">Todas las Familias</option>
              {families.map((f) => (
                <option key={f} value={f}>{f}</option>
              ))}
            </select>
            <ChevronDown className="w-4 h-4 absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          </div>

          {/* Status Filter */}
          <div className="relative w-full sm:w-40">
            <select
              value={statusFilter}
              onChange={(e) => { setStatusFilter(e.target.value); setCurrentPage(1); }}
              className="w-full appearance-none pl-3 pr-8 py-2 text-sm bg-white border border-slate-300 rounded-lg text-slate-700 focus:outline-none focus:border-[#1a56db] focus:ring-1 focus:ring-[#1a56db] transition cursor-pointer"
            >
              <option value="all">Todos los estados</option>
              <option value="pending">Pendiente</option>
              <option value="audited">Auditado</option>
            </select>
            <ChevronDown className="w-4 h-4 absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
          </div>
        </div>

        {/* Results count */}
        <div className="text-sm text-slate-500 font-medium whitespace-nowrap">
          {filteredArticles.length} resultados
        </div>
      </div>

      {/* Mobile Card List (Visible on < md) */}
      <div className="block md:hidden divide-y divide-slate-100">
        {paginatedArticles.length === 0 ? (
          <div className="p-8 text-center text-sm text-slate-500" aria-live="polite">
            {emptyMessage}
          </div>
        ) : (
          paginatedArticles.map((art) => {
            const isOutOfStock = art.stock_real === 0;
            const auditor = isSupervisor && art.fue_auditado ? getAuditorForArticle(art.id_articulo) : null;
            const auditorInitials = auditor
              ? auditor.name.split(" ").map((n) => n[0]).join("").substring(0, 2).toUpperCase()
              : "";

            return (
              <div key={art.id_articulo} className="p-4 space-y-3 bg-white hover:bg-slate-50/50 transition-colors">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <h3 className="font-semibold text-slate-900 text-sm leading-snug">
                      {art.des_articulo}
                    </h3>
                    <div className="font-mono text-xs text-slate-400 mt-0.5">
                      {art.cod_barras[0] || art.id_articulo}
                    </div>
                  </div>

                  <div>
                    {art.fue_auditado ? (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-bold tracking-wider uppercase">
                        Auditado
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-warning-50 border border-warning-200 text-warning-700 text-[10px] font-bold tracking-wider uppercase">
                        Pendiente
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2 text-xs">
                  {art.des_marca && (
                    <span className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 font-medium">
                      {art.des_marca}
                    </span>
                  )}
                  {art.des_familia && (
                    <span className="px-2 py-0.5 rounded-md bg-slate-50 border border-slate-200 text-slate-600 font-medium">
                      {art.des_familia}
                    </span>
                  )}
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs">
                  <div className="flex items-center gap-2">
                    <span className="text-slate-400 font-medium">Stock:</span>
                    {isOutOfStock ? (
                      <span className="inline-flex items-center gap-1 font-bold text-red-600">
                        <AlertTriangle className="w-3.5 h-3.5" />
                        0 unidades
                      </span>
                    ) : (
                      <span className="font-bold text-slate-900">
                        {art.stock_real} unidades
                      </span>
                    )}
                  </div>

                  {isAdmin && "pcio_com_siva" in art && art.pcio_com_siva !== undefined && (
                    <div className="font-mono font-semibold text-slate-700">
                      $ {art.pcio_com_siva.toLocaleString("es-AR", { minimumFractionDigits: 2 })}
                    </div>
                  )}

                  {isSupervisor && auditor && (
                    <div className="flex items-center gap-1.5 text-slate-600">
                      <div className="w-5 h-5 rounded-full bg-[#1a56db] text-white flex items-center justify-center text-[9px] font-bold">
                        {auditorInitials}
                      </div>
                      <span className="text-[11px] font-medium truncate max-w-[90px]">
                        {auditor.name}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Desktop Table Content (Visible on >= md) */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-600">
          <thead className="text-xs font-semibold text-slate-500 uppercase tracking-wider border-b border-slate-200 bg-white">
            <tr>
              <th className="px-6 py-4 font-semibold">CÓDIGO</th>
              <th className="px-6 py-4 font-semibold">DESCRIPCIÓN</th>
              <th className="px-6 py-4 font-semibold">MARCA</th>
              <th className="px-6 py-4 font-semibold">FAMILIA</th>
              <th className="px-6 py-4 font-semibold text-right">STOCK</th>
              {isAdmin && <th className="px-6 py-4 font-semibold text-right">COSTO</th>}
              <th className="px-6 py-4 font-semibold">ESTADO</th>
              {isSupervisor && <th className="px-6 py-4 font-semibold">AUDITADO POR</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {paginatedArticles.length === 0 ? (
              <tr>
                <td colSpan={isAdmin || isSupervisor ? 7 : 6} className="px-6 py-8 text-center text-slate-500">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              paginatedArticles.map((art) => {
                const isOutOfStock = art.stock_real === 0;
                
                return (
                  <tr key={art.id_articulo} className="hover:bg-slate-50/50 transition-colors bg-white">
                    {/* Barcode */}
                    <td className="px-6 py-4 font-mono text-slate-500 whitespace-nowrap">
                      {art.cod_barras[0] || art.id_articulo}
                    </td>

                    {/* Description */}
                    <td className="px-6 py-4">
                      <span className="font-medium text-slate-900">
                        {art.des_articulo}
                      </span>
                    </td>

                    {/* Brand / Group */}
                    <td className="px-6 py-4 text-slate-900">
                      {art.des_marca || art.des_grupo || "-"}
                    </td>

                    {/* Family */}
                    <td className="px-6 py-4">
                      {art.des_familia ? (
                        <span className="inline-flex items-center px-2 py-1 rounded-md bg-slate-50 border border-slate-200 text-xs font-medium text-slate-600">
                          {art.des_familia}
                        </span>
                      ) : (
                        "-"
                      )}
                    </td>

                    {/* Stock */}
                    <td className="px-6 py-4 text-right">
                      {isOutOfStock ? (
                        <div className="flex items-center justify-end gap-1.5 text-red-600 font-bold">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          <span>0</span>
                        </div>
                      ) : (
                        <span className="font-bold text-slate-900">{art.stock_real}</span>
                      )}
                    </td>

                    {/* Purchase Cost (Admin only, Right-aligned & Monospaced) */}
                    {isAdmin && (
                      <td className="px-6 py-4 text-right font-mono font-medium text-slate-700 whitespace-nowrap">
                        {"pcio_com_siva" in art && art.pcio_com_siva !== undefined
                          ? `$ ${art.pcio_com_siva.toLocaleString("es-AR", { minimumFractionDigits: 2 })}`
                          : "-"}
                      </td>
                    )}

                    {/* Status */}
                    <td className="px-6 py-4">
                      {art.fue_auditado ? (
                        <span className="inline-flex items-center px-2 py-1 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-bold tracking-widest uppercase">
                          AUDITADO
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2 py-1 rounded-full bg-warning-50 border-warning-200 text-warning-700 border text-[10px] font-bold tracking-widest uppercase">
                          PENDIENTE
                        </span>
                      )}
                    </td>

                    {/* Audited By (Supervisor only) */}
                    {isSupervisor && (
                      <td className="px-6 py-4">
                        {art.fue_auditado ? (
                          (() => {
                            const auditor = getAuditorForArticle(art.id_articulo);
                            if (!auditor) return <span className="text-slate-400">—</span>;
                            const initials = auditor.name.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();
                            return (
                              <div className="flex items-center gap-2">
                                <div className="w-7 h-7 rounded-full bg-[#1a56db] flex items-center justify-center text-[10px] font-bold text-white shrink-0">
                                  {initials}
                                </div>
                                <span className="text-slate-900 font-medium truncate max-w-[120px]" title={auditor.name}>
                                  {auditor.name}
                                </span>
                              </div>
                            );
                          })()
                        ) : (
                          <span className="text-slate-300">—</span>
                        )}
                      </td>
                    )}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      {totalPages > 0 && (
        <div className="p-4 border-t border-slate-200 flex flex-col sm:flex-row items-center justify-between gap-3 bg-white text-sm">
          <div className="text-slate-500 text-xs sm:text-sm">
            {Math.min((currentPage - 1) * itemsPerPage + 1, filteredArticles.length)}-{Math.min(currentPage * itemsPerPage, filteredArticles.length)} de {filteredArticles.length} ítems
          </div>
          <div className="flex items-center gap-1">
            <button
              disabled={currentPage === 1}
              onClick={() => setCurrentPage(1)}
              className="p-2 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 disabled:opacity-40 disabled:pointer-events-none active:scale-95 transition cursor-pointer"
              aria-label="Primera página"
            >
              <ChevronsLeft className="w-4 h-4" />
            </button>
            <button
              disabled={currentPage === 1}
              onClick={() => setCurrentPage((p) => p - 1)}
              className="p-2 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 disabled:opacity-40 disabled:pointer-events-none active:scale-95 transition cursor-pointer"
              aria-label="Página anterior"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            
            <div className="flex items-center gap-1 mx-1 sm:mx-2">
              {Array.from({ length: totalPages }).map((_, i) => {
                if (totalPages > 5 && i !== 0 && i !== totalPages - 1 && Math.abs(i + 1 - currentPage) > 1) {
                  if (i + 1 === currentPage - 2 || i + 1 === currentPage + 2) return <span key={i} className="text-slate-400 px-1">...</span>;
                  return null;
                }
                return (
                  <button
                    key={i}
                    onClick={() => setCurrentPage(i + 1)}
                    className={`w-8 h-8 rounded-lg flex items-center justify-center text-xs sm:text-sm font-semibold transition active:scale-95 cursor-pointer ${
                      currentPage === i + 1
                        ? "bg-[#1a56db] text-white shadow-xs"
                        : "text-slate-600 hover:bg-slate-100"
                    }`}
                  >
                    {i + 1}
                  </button>
                );
              })}
            </div>

            <button
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage((p) => p + 1)}
              className="p-2 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 disabled:opacity-40 disabled:pointer-events-none active:scale-95 transition cursor-pointer"
              aria-label="Página siguiente"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
            <button
              disabled={currentPage === totalPages}
              onClick={() => setCurrentPage(totalPages)}
              className="p-2 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 disabled:opacity-40 disabled:pointer-events-none active:scale-95 transition cursor-pointer"
              aria-label="Última página"
            >
              <ChevronsRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
