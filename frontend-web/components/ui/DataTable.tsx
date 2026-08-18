"use client";

import React, { useState, useMemo } from "react";
import { ArticuloPublicView, ArticuloAdminView, UserRole } from "@/lib/types/domain";
import { StatusBadge } from "./StatusBadge";
import { Search, ArrowUpDown, ArrowUp, ArrowDown, Package, Layers } from "lucide-react";

export interface DataTableProps {
  articles: (ArticuloPublicView | ArticuloAdminView)[];
  currentRole: UserRole;
  onSelectArticle?: (article: ArticuloPublicView | ArticuloAdminView) => void;
  title?: string;
}

type SortField = "des_articulo" | "des_familia" | "stock_real" | "pcio_com_siva" | "fue_auditado" | "vencimiento";
type SortOrder = "asc" | "desc";

export function DataTable({
  articles,
  currentRole,
  onSelectArticle,
  title = "Artículos en Depósito",
}: DataTableProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [familyFilter, setFamilyFilter] = useState("all");
  const [sortField, setSortField] = useState<SortField>("des_articulo");
  const [sortOrder, setSortOrder] = useState<SortOrder>("asc");

  const isAdmin = currentRole === UserRole.ADMINISTRADOR;

  // Extract unique families for quick filter
  const families = useMemo(() => {
    const set = new Set<string>();
    articles.forEach((a) => {
      if (a.des_familia) set.add(a.des_familia);
    });
    return Array.from(set);
  }, [articles]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortOrder("asc");
    }
  };

  const filteredAndSortedArticles = useMemo(() => {
    const term = searchTerm.toLowerCase().trim();

    return articles
      .filter((art) => {
        const matchesSearch =
          !term ||
          art.id_articulo.toLowerCase().includes(term) ||
          art.des_articulo.toLowerCase().includes(term) ||
          (art.des_marca && art.des_marca.toLowerCase().includes(term)) ||
          art.cod_barras.some((cb) => cb.includes(term));

        const matchesFamily =
          familyFilter === "all" || art.des_familia === familyFilter;

        return matchesSearch && matchesFamily;
      })
      .sort((a, b) => {
        let valA: string | number | boolean = "";
        let valB: string | number | boolean = "";

        if (sortField === "des_articulo") {
          valA = a.des_articulo;
          valB = b.des_articulo;
        } else if (sortField === "des_familia") {
          valA = a.des_familia || "";
          valB = b.des_familia || "";
        } else if (sortField === "stock_real") {
          valA = a.stock_real;
          valB = b.stock_real;
        } else if (sortField === "fue_auditado") {
          valA = a.fue_auditado ? 1 : 0;
          valB = b.fue_auditado ? 1 : 0;
        } else if (sortField === "vencimiento") {
          valA = a.lotes[0]?.vencimiento || "9999-99-99";
          valB = b.lotes[0]?.vencimiento || "9999-99-99";
        } else if (sortField === "pcio_com_siva") {
          valA = "pcio_com_siva" in a ? (a as ArticuloAdminView).pcio_com_siva : 0;
          valB = "pcio_com_siva" in b ? (b as ArticuloAdminView).pcio_com_siva : 0;
        }

        if (typeof valA === "string" && typeof valB === "string") {
          return sortOrder === "asc"
            ? valA.localeCompare(valB)
            : valB.localeCompare(valA);
        }

        if (valA < valB) return sortOrder === "asc" ? -1 : 1;
        if (valA > valB) return sortOrder === "asc" ? 1 : -1;
        return 0;
      });
  }, [articles, searchTerm, familyFilter, sortField, sortOrder]);

  const renderSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <ArrowUpDown className="w-3.5 h-3.5 text-slate-500" />;
    }
    return sortOrder === "asc" ? (
      <ArrowUp className="w-3.5 h-3.5 text-indigo-400" />
    ) : (
      <ArrowDown className="w-3.5 h-3.5 text-indigo-400" />
    );
  };

  return (
    <div className="glass-panel rounded-2xl border border-slate-800/80 overflow-hidden shadow-2xl">
      {/* Table Header Controls */}
      <div className="p-5 border-b border-slate-800/80 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <Package className="w-5 h-5 text-indigo-400" />
            <span>{title}</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 font-mono">
              {filteredAndSortedArticles.length} ítems
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            {isAdmin
              ? "Vista Administrativa: Precios de compra s/IVA y valorizaciones habilitadas."
              : "Vista Operativa: Datos restringidos a stock y categorización."}
          </p>
        </div>

        {/* Filter and Search controls */}
        <div className="flex flex-col sm:flex-row items-center gap-3 w-full md:w-auto">
          {/* Family Filter Dropdown */}
          <div className="flex items-center gap-1.5 bg-slate-900/90 border border-slate-700/60 rounded-xl px-3 py-1.5 w-full sm:w-auto">
            <Layers className="w-4 h-4 text-slate-400" />
            <select
              value={familyFilter}
              onChange={(e) => setFamilyFilter(e.target.value)}
              className="bg-transparent text-xs text-slate-200 focus:outline-none cursor-pointer"
            >
              <option value="all" className="bg-slate-900 text-white">
                Todas las Familias
              </option>
              {families.map((f) => (
                <option key={f} value={f} className="bg-slate-900 text-white">
                  {f}
                </option>
              ))}
            </select>
          </div>

          {/* Search Input */}
          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Buscar por código, EAN o nombre..."
              className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-900/90 border border-slate-700/60 rounded-xl text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
            />
          </div>
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950/80 text-slate-400 font-semibold border-b border-slate-800/80 uppercase tracking-wider">
            <tr>
              <th
                onClick={() => handleSort("des_articulo")}
                className="p-3.5 cursor-pointer hover:text-white transition"
              >
                <div className="flex items-center gap-1.5">
                  <span>Artículo / EAN</span>
                  {renderSortIcon("des_articulo")}
                </div>
              </th>
              <th
                onClick={() => handleSort("des_familia")}
                className="p-3.5 cursor-pointer hover:text-white transition hidden sm:table-cell"
              >
                <div className="flex items-center gap-1.5">
                  <span>Familia / Marca</span>
                  {renderSortIcon("des_familia")}
                </div>
              </th>
              <th
                onClick={() => handleSort("stock_real")}
                className="p-3.5 text-right cursor-pointer hover:text-white transition"
              >
                <div className="flex items-center justify-end gap-1.5">
                  <span>Stock Teórico</span>
                  {renderSortIcon("stock_real")}
                </div>
              </th>
              <th
                onClick={() => handleSort("vencimiento")}
                className="p-3.5 cursor-pointer hover:text-white transition hidden md:table-cell"
              >
                <div className="flex items-center gap-1.5">
                  <span>FEFO Lote Próximo</span>
                  {renderSortIcon("vencimiento")}
                </div>
              </th>
              {isAdmin && (
                <th
                  onClick={() => handleSort("pcio_com_siva")}
                  className="p-3.5 text-right cursor-pointer hover:text-amber-400 text-amber-400/90 transition"
                >
                  <div className="flex items-center justify-end gap-1.5">
                    <span>Costo Unitario</span>
                    {renderSortIcon("pcio_com_siva")}
                  </div>
                </th>
              )}
              <th
                onClick={() => handleSort("fue_auditado")}
                className="p-3.5 text-center cursor-pointer hover:text-white transition"
              >
                <div className="flex items-center justify-center gap-1.5">
                  <span>Estado</span>
                  {renderSortIcon("fue_auditado")}
                </div>
              </th>
              {onSelectArticle && <th className="p-3.5 text-right">Acción</th>}
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-800/60">
            {filteredAndSortedArticles.length === 0 ? (
              <tr>
                <td
                  colSpan={isAdmin ? 7 : 6}
                  className="p-8 text-center text-slate-500 font-medium"
                >
                  No se encontraron artículos que coincidan con la búsqueda.
                </td>
              </tr>
            ) : (
              filteredAndSortedArticles.map((art) => {
                const nearestLot = art.lotes[0];
                const hasCost = "pcio_com_siva" in art;

                return (
                  <tr
                    key={art.id_articulo}
                    className={`hover:bg-slate-800/40 transition-colors ${
                      art.fue_auditado ? "bg-slate-900/20" : ""
                    }`}
                  >
                    {/* Description and Code */}
                    <td className="p-3.5">
                      <div className="font-semibold text-slate-100 max-w-[260px] truncate" title={art.des_articulo}>
                        {art.des_articulo}
                      </div>
                      <div className="flex items-center gap-2 mt-0.5 text-[11px] font-mono text-slate-400">
                        <span className="text-indigo-300 font-medium">{art.id_articulo}</span>
                        <span>•</span>
                        <span>{art.cod_barras[0] || "Sin EAN"}</span>
                      </div>
                    </td>

                    {/* Family / Brand */}
                    <td className="p-3.5 hidden sm:table-cell">
                      <div className="text-slate-300 font-medium">{art.des_familia || "-"}</div>
                      <div className="text-[11px] text-slate-500">{art.des_marca || "-"}</div>
                    </td>

                    {/* Theoretical Stock */}
                    <td className="p-3.5 text-right font-mono">
                      <span className="text-base font-bold text-white">
                        {art.stock_real}
                      </span>
                      <span className="text-[10px] text-slate-500 ml-1">un.</span>
                    </td>

                    {/* FEFO Lot Expiration */}
                    <td className="p-3.5 hidden md:table-cell">
                      {nearestLot?.vencimiento ? (
                        <div className="space-y-1">
                          <StatusBadge
                            type="fefo"
                            value={nearestLot.vencimiento}
                            size="sm"
                          />
                          <div className="text-[10px] font-mono text-slate-500">
                            Lote: {nearestLot.lote} ({nearestLot.stock_real} un.)
                          </div>
                        </div>
                      ) : (
                        <span className="text-slate-500 font-mono">Sin lotes</span>
                      )}
                    </td>

                    {/* Purchase Cost (Admin only) */}
                    {isAdmin && (
                      <td className="p-3.5 text-right font-mono text-amber-300 font-semibold">
                        {hasCost ? (
                          `$${(art as ArticuloAdminView).pcio_com_siva.toLocaleString(
                            "es-AR",
                            { minimumFractionDigits: 2 }
                          )}`
                        ) : (
                          <span className="text-slate-600 font-normal">N/A</span>
                        )}
                      </td>
                    )}

                    {/* Audit Status Badge */}
                    <td className="p-3.5 text-center">
                      <StatusBadge type="audit" value={art.fue_auditado} size="sm" />
                    </td>

                    {/* Action */}
                    {onSelectArticle && (
                      <td className="p-3.5 text-right">
                        <button
                          onClick={() => onSelectArticle(art)}
                          className="px-2.5 py-1 text-[11px] font-semibold bg-indigo-600/80 hover:bg-indigo-500 text-white rounded-lg transition shadow-sm"
                        >
                          Auditar
                        </button>
                      </td>
                    )}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
