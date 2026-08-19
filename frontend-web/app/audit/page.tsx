"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { useDataClient } from "@/lib/hooks/useDataClient";
import { DemoShell } from "@/components/layout/DemoShell";
import { ArticuloPublicView, ArticuloAdminView } from "@/lib/types/domain";
import {
  Search,
  Check,
  AlertCircle,
  CheckCircle2,
  Plus,
  Minus,
  Package,
  X,
} from "lucide-react";

export default function AuditPage() {
  const { client } = useDataClient();
  const [barcodeQuery, setBarcodeQuery] = useState("");
  const [selectedArticle, setSelectedArticle] = useState<
    ArticuloPublicView | ArticuloAdminView | null
  >(null);

  // Autocomplete / Search State
  const [suggestions, setSuggestions] = useState<
    (ArticuloPublicView | ArticuloAdminView)[]
  >([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const searchContainerRef = useRef<HTMLDivElement>(null);

  // Form State
  const [actionType, setActionType] = useState<
    "surplus" | "shortage" | "none" | null
  >(null);
  const [physicalCount, setPhysicalCount] = useState<number | "">("");
  const [reason, setReason] = useState("");
  const [feedback, setFeedback] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  // Debounced search for autocomplete suggestions
  useEffect(() => {
    const trimmed = barcodeQuery.trim();
    if (!trimmed) {
      setSuggestions([]);
      setShowDropdown(false);
      return;
    }

    const timer = setTimeout(async () => {
      try {
        setIsSearching(true);
        const results = await client.searchArticulos(trimmed);
        setSuggestions(results);
        setShowDropdown(true);
      } catch (err) {
        console.error("Search error:", err);
      } finally {
        setIsSearching(false);
      }
    }, 180);

    return () => clearTimeout(timer);
  }, [barcodeQuery, client]);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        searchContainerRef.current &&
        !searchContainerRef.current.contains(event.target as Node)
      ) {
        setShowDropdown(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Sync actionType and physicalCount
  useEffect(() => {
    if (selectedArticle && physicalCount !== "") {
      const count = Number(physicalCount);
      if (count === selectedArticle.stock_real) {
        setActionType("none");
      } else if (count > selectedArticle.stock_real) {
        setActionType("surplus");
      } else {
        setActionType("shortage");
      }
    } else if (physicalCount === "") {
      setActionType(null);
    }
  }, [physicalCount, selectedArticle]);

  const selectArticle = useCallback(
    (article: ArticuloPublicView | ArticuloAdminView) => {
      setSelectedArticle(article);
      setBarcodeQuery(article.des_articulo);
      setShowDropdown(false);
      setSuggestions([]);
      setPhysicalCount("");
      setActionType(null);
      setReason("");
      setFeedback(null);
    },
    []
  );

  const handleActionClick = (type: "surplus" | "shortage" | "none") => {
    setActionType(type);
    if (selectedArticle) {
      if (type === "none") {
        setPhysicalCount(selectedArticle.stock_real);
      } else if (type === "surplus") {
        setPhysicalCount(selectedArticle.stock_real + 1);
      } else if (type === "shortage") {
        setPhysicalCount(Math.max(0, selectedArticle.stock_real - 1));
      }
    }
  };

  const increment = () =>
    setPhysicalCount((prev) => (prev === "" ? 1 : Number(prev) + 1));
  const decrement = () =>
    setPhysicalCount((prev) =>
      prev === "" || Number(prev) <= 0 ? 0 : Number(prev) - 1
    );

  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFeedback(null);
    setShowDropdown(false);
    const query = barcodeQuery.trim();
    if (!query) return;

    try {
      // 1. Try exact barcode or ID match
      const exactResult = await client.getArticuloByBarcode(query);
      if (exactResult) {
        selectArticle(exactResult);
        return;
      }

      // 2. Try search matches
      const searchResults = await client.searchArticulos(query);
      if (searchResults.length > 0) {
        selectArticle(searchResults[0]);
      } else {
        setSelectedArticle(null);
        setFeedback({
          type: "error",
          message: "Artículo no encontrado por código o nombre.",
        });
      }
    } catch (err: unknown) {
      setFeedback({
        type: "error",
        message: "Error en la búsqueda del artículo.",
      });
    }
  };

  const handleClearSearch = () => {
    setBarcodeQuery("");
    setSuggestions([]);
    setShowDropdown(false);
  };

  const handleAuditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedArticle || physicalCount === "") return;

    try {
      await client.registerAudit({
        id_articulo: selectedArticle.id_articulo,
        stock_fisico_contado: Number(physicalCount),
        observation: reason || undefined,
      });

      setFeedback({
        type: "success",
        message: `Auditoría de "${selectedArticle.des_articulo}" registrada correctamente.`,
      });
      setSelectedArticle(null);
      setBarcodeQuery("");
      setPhysicalCount("");
      setReason("");
      setActionType(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setFeedback({ type: "error", message: `Error al registrar: ${msg}` });
    }
  };

  return (
    <DemoShell>
      <div className="max-w-3xl mx-auto py-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-6">
          Auditoría de Stock
        </h1>

        {/* Search Bar with Autocomplete Dropdown */}
        <div ref={searchContainerRef} className="relative mb-10">
          <form
            onSubmit={handleSearchSubmit}
            className="flex items-center gap-3"
          >
            <div className="flex-1 bg-white border border-slate-200 rounded-xl flex items-center px-4 py-3 shadow-sm focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500 transition-all">
              <Search className="w-5 h-5 text-slate-400 mr-3 shrink-0" />
              <input
                type="text"
                value={barcodeQuery}
                onChange={(e) => setBarcodeQuery(e.target.value)}
                onFocus={() => {
                  if (suggestions.length > 0) setShowDropdown(true);
                }}
                onKeyDown={(e) => {
                  if (e.key === "Escape") {
                    setShowDropdown(false);
                  }
                }}
                placeholder="Buscar por nombre, código de barras o ID..."
                className="w-full text-slate-900 placeholder-slate-400 focus:outline-none text-base"
                autoFocus
              />
              {barcodeQuery && (
                <button
                  type="button"
                  onClick={handleClearSearch}
                  className="p-1 text-slate-400 hover:text-slate-600 rounded-full transition-colors"
                  aria-label="Limpiar búsqueda"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>
            <button
              type="submit"
              className="px-8 py-3.5 bg-[#1a56db] hover:bg-blue-700 text-white font-medium rounded-xl shadow-sm transition-colors cursor-pointer"
            >
              Buscar
            </button>
          </form>

          {/* Autocomplete Dropdown List */}
          {showDropdown && barcodeQuery.trim().length > 0 && (
            <div className="absolute left-0 right-0 top-full mt-2 bg-white border border-slate-200 rounded-xl shadow-xl z-50 max-h-80 overflow-y-auto divide-y divide-slate-100">
              {suggestions.length > 0 ? (
                suggestions.map((article) => (
                  <button
                    key={article.id_articulo}
                    type="button"
                    onClick={() => selectArticle(article)}
                    className="w-full px-4 py-3 text-left hover:bg-blue-50/70 transition-colors flex items-center justify-between gap-3 group cursor-pointer"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center shrink-0 group-hover:bg-blue-100 transition-colors">
                        <Package className="w-4 h-4 text-slate-600 group-hover:text-blue-600" />
                      </div>
                      <div className="truncate">
                        <div className="text-sm font-semibold text-slate-900 group-hover:text-blue-700 truncate">
                          {article.des_articulo}
                        </div>
                        <div className="text-xs text-slate-500 flex items-center gap-2">
                          <span className="font-mono text-slate-400">
                            {article.cod_barras[0] || article.id_articulo}
                          </span>
                          {article.des_marca && (
                            <>
                              <span>•</span>
                              <span>{article.des_marca}</span>
                            </>
                          )}
                          {article.des_familia && (
                            <>
                              <span>•</span>
                              <span>{article.des_familia}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <div className="text-right">
                        <div className="text-xs font-semibold text-slate-700">
                          Stock: {article.stock_real}
                        </div>
                      </div>
                      {article.fue_auditado ? (
                        <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 text-[10px] font-bold uppercase tracking-wider">
                          Auditado
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 rounded-full bg-amber-50 text-amber-600 border border-amber-200 text-[10px] font-bold uppercase tracking-wider">
                          Pendiente
                        </span>
                      )}
                    </div>
                  </button>
                ))
              ) : (
                <div className="px-4 py-6 text-center text-sm text-slate-500">
                  {isSearching
                    ? "Buscando coincidencias..."
                    : `No se encontraron artículos que coincidan con "${barcodeQuery}"`}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Feedback Messages */}
        {feedback && feedback.type === "error" && (
          <div className="mb-6 p-4 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm flex items-start gap-3">
            <AlertCircle className="w-5 h-5 shrink-0" />
            <span>{feedback.message}</span>
          </div>
        )}

        {feedback && feedback.type === "success" && (
          <div className="mb-6 p-4 rounded-xl bg-emerald-50 border border-emerald-100 text-emerald-700 text-sm flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 shrink-0" />
            <span>{feedback.message}</span>
          </div>
        )}

        {/* Main Content Area */}
        {selectedArticle ? (
          <div className="space-y-6">
            {/* Item Card */}
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
              <div className="flex items-center justify-between mb-5">
                <h2 className="text-xl font-bold text-slate-900">
                  {selectedArticle.des_articulo}
                </h2>
                {selectedArticle.fue_auditado ? (
                  <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold uppercase tracking-wider">
                    AUDITADO
                  </span>
                ) : (
                  <span className="px-3 py-1 rounded-full bg-amber-50 text-amber-600 border border-amber-200 text-xs font-bold uppercase tracking-wider">
                    PENDIENTE
                  </span>
                )}
              </div>

              <hr className="border-slate-100 mb-5" />

              <div className="grid grid-cols-3 gap-6 mb-5">
                <div>
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-1">
                    MARCA
                  </div>
                  <div className="text-sm font-medium text-slate-900">
                    {selectedArticle.des_marca || "-"}
                  </div>
                </div>
                <div>
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-1">
                    FAMILIA
                  </div>
                  <div className="text-sm font-medium text-slate-900">
                    {selectedArticle.des_familia || "-"}
                  </div>
                </div>
                <div>
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-1">
                    CÓDIGO
                  </div>
                  <div className="text-sm font-medium text-slate-900 font-mono">
                    {selectedArticle.cod_barras[0] ||
                      selectedArticle.id_articulo}
                  </div>
                </div>
              </div>

              <hr className="border-slate-100 mb-5" />

              <div className="flex items-baseline gap-2">
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">
                  STOCK ACTUAL
                </div>
                <div className="text-2xl font-bold text-slate-900 ml-2">
                  {selectedArticle.stock_real}
                </div>
                <div className="text-sm font-medium text-slate-500">
                  unidades
                </div>
              </div>
            </div>

            {/* Audit Form Card */}
            <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
              <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-6">
                REGISTRAR DISCREPANCIA
              </h3>

              <form onSubmit={handleAuditSubmit} className="space-y-6">
                {/* Action Buttons */}
                <div>
                  <label className="block text-sm font-medium text-slate-500 mb-3">
                    Acción
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    <button
                      type="button"
                      onClick={() => handleActionClick("surplus")}
                      className={`py-2.5 rounded-lg text-sm font-medium border transition-colors cursor-pointer ${
                        actionType === "surplus"
                          ? "bg-slate-50 border-slate-400 text-slate-900 font-semibold"
                          : "bg-white border-slate-200 text-slate-500 hover:bg-slate-50"
                      }`}
                    >
                      Sobrante
                    </button>
                    <button
                      type="button"
                      onClick={() => handleActionClick("shortage")}
                      className={`py-2.5 rounded-lg text-sm font-medium border transition-colors cursor-pointer ${
                        actionType === "shortage"
                          ? "bg-slate-50 border-slate-400 text-slate-900 font-semibold"
                          : "bg-white border-slate-200 text-slate-500 hover:bg-slate-50"
                      }`}
                    >
                      Faltante
                    </button>
                    <button
                      type="button"
                      onClick={() => handleActionClick("none")}
                      className={`py-2.5 rounded-lg text-sm font-medium border transition-colors cursor-pointer ${
                        actionType === "none"
                          ? "bg-slate-50 border-slate-400 text-slate-900 font-semibold"
                          : "bg-white border-slate-200 text-slate-500 hover:bg-slate-50"
                      }`}
                    >
                      Sin Acción
                    </button>
                  </div>
                </div>

                {/* Audited Quantity Stepper */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-medium text-slate-500">
                      Cantidad Auditada
                    </label>
                    {selectedArticle && (
                      <button
                        type="button"
                        onClick={() => setPhysicalCount(selectedArticle.stock_real)}
                        className="text-xs font-semibold text-blue-600 hover:text-blue-700 hover:underline cursor-pointer"
                      >
                        Copiar Stock Actual ({selectedArticle.stock_real})
                      </button>
                    )}
                  </div>

                  <div className="flex flex-wrap items-center gap-3">
                    {/* Stepper Input Container */}
                    <div className="flex items-center bg-slate-50 border border-slate-200 rounded-xl p-1.5 w-52 shadow-sm focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20 transition-all">
                      {/* Minus Button */}
                      <button
                        type="button"
                        onClick={decrement}
                        disabled={physicalCount !== "" && Number(physicalCount) <= 0}
                        aria-label="Disminuir cantidad"
                        className="w-10 h-10 rounded-lg bg-white border border-slate-200 text-slate-700 hover:bg-slate-100 hover:text-slate-900 active:scale-95 transition-all flex items-center justify-center shadow-xs shrink-0 cursor-pointer disabled:opacity-40 disabled:hover:bg-white disabled:hover:text-slate-700 disabled:cursor-not-allowed disabled:active:scale-100"
                        title="Restar 1"
                      >
                        <Minus className="w-4 h-4 stroke-[3]" />
                      </button>

                      {/* Number Input Field */}
                      <input
                        type="number"
                        min="0"
                        required
                        value={physicalCount}
                        placeholder="0"
                        onChange={(e) =>
                          setPhysicalCount(
                            e.target.value === "" ? "" : Number(e.target.value)
                          )
                        }
                        className="w-0 flex-1 min-w-0 h-10 text-center font-extrabold text-xl text-slate-900 bg-transparent focus:outline-none placeholder:text-slate-300 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                      />

                      {/* Plus Button */}
                      <button
                        type="button"
                        onClick={increment}
                        aria-label="Aumentar cantidad"
                        className="w-10 h-10 rounded-lg bg-[#1a56db] text-white hover:bg-blue-700 active:scale-95 transition-all flex items-center justify-center shadow-xs shrink-0 cursor-pointer"
                        title="Sumar 1"
                      >
                        <Plus className="w-4 h-4 stroke-[3]" />
                      </button>
                    </div>

                    {/* Quick Adjustment Chips */}
                    <div className="flex items-center gap-1.5">
                      {[1, 5, 10].map((step) => (
                        <button
                          key={step}
                          type="button"
                          onClick={() =>
                            setPhysicalCount((prev) =>
                              prev === "" ? step : Number(prev) + step
                            )
                          }
                          className="px-2.5 py-1.5 rounded-lg bg-slate-100 hover:bg-blue-50 hover:text-blue-700 hover:border-blue-200 border border-slate-200/80 text-xs font-semibold text-slate-600 transition-all cursor-pointer active:scale-95"
                          title={`Sumar ${step}`}
                        >
                          +{step}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Reason Dropdown */}
                <div>
                  <label className="block text-sm font-medium text-slate-500 mb-3">
                    Motivo
                  </label>
                  <select
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    className="w-full h-12 px-4 bg-white border border-slate-200 rounded-lg text-sm text-slate-700 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all appearance-none cursor-pointer"
                  >
                    <option value="">Seleccione un motivo...</option>
                    <option value="Conteo regular">Conteo regular</option>
                    <option value="Mercadería dañada">Mercadería dañada</option>
                    <option value="Vencimiento">Vencimiento</option>
                    <option value="Pérdida desconocida">Pérdida desconocida</option>
                    <option value="Error de sistema">Error de sistema</option>
                  </select>
                </div>

                {/* Submit Button */}
                <button
                  type="submit"
                  className="w-full h-12 mt-4 bg-[#0e9f6e] hover:bg-[#057a55] text-white font-bold rounded-lg flex items-center justify-center gap-2 transition-colors shadow-sm cursor-pointer"
                >
                  <Check className="w-5 h-5" />
                  <span>Registrar Auditoría</span>
                </button>
              </form>
            </div>
          </div>
        ) : (
          /* Empty State */
          <div className="flex flex-col items-center justify-center py-20">
            <Search className="w-12 h-12 text-slate-200 stroke-1 mb-4" />
            <p className="text-slate-500 text-sm">
              Busque un artículo para comenzar a auditar
            </p>
          </div>
        )}
      </div>
    </DemoShell>
  );
}

