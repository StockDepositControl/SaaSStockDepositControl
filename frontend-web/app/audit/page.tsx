"use client";

import React, { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { useDataClient } from "@/lib/hooks/useDataClient";
import { DemoShell } from "@/components/layout/DemoShell";
import { ArticuloPublicView, ArticuloAdminView } from "@/lib/types/domain";
import { BarcodeScannerModal } from "@/components/scanner/BarcodeScannerModal";
import {
  Search,
  Check,
  AlertCircle,
  CheckCircle2,
  Plus,
  Minus,
  Package,
  X,
  ScanBarcode,
} from "lucide-react";

export default function AuditPage() {
  const { client } = useDataClient();
  const [barcodeQuery, setBarcodeQuery] = useState("");
  const [selectedArticle, setSelectedArticle] = useState<
    ArticuloPublicView | ArticuloAdminView | null
  >(null);

  // Scanner modal state
  const [isScannerOpen, setIsScannerOpen] = useState(false);

  // Autocomplete / Search State
  const [suggestions, setSuggestions] = useState<
    (ArticuloPublicView | ArticuloAdminView)[]
  >([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const searchContainerRef = useRef<HTMLDivElement>(null);

  // Form State
  const [physicalCount, setPhysicalCount] = useState<number | "">("");
  const [reason, setReason] = useState("");
  const [feedback, setFeedback] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  // React 19 State-in-Effect compliant: derive actionType during render
  const actionType = useMemo<"surplus" | "shortage" | "none" | null>(() => {
    if (!selectedArticle || physicalCount === "") return null;
    const count = Number(physicalCount);
    if (count === selectedArticle.stock_real) return "none";
    return count > selectedArticle.stock_real ? "surplus" : "shortage";
  }, [physicalCount, selectedArticle]);

  // Debounced search for autocomplete suggestions (no sync setState inside effect)
  useEffect(() => {
    const trimmed = barcodeQuery.trim();
    if (!trimmed) {
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

  const selectArticle = useCallback(
    (article: ArticuloPublicView | ArticuloAdminView) => {
      setSelectedArticle(article);
      setBarcodeQuery(article.des_articulo);
      setShowDropdown(false);
      setSuggestions([]);
      setPhysicalCount("");
      setReason("");
      setFeedback(null);
    },
    []
  );

  const handleActionClick = (type: "surplus" | "shortage" | "none") => {
    if (!selectedArticle) return;
    if (type === "none") {
      setPhysicalCount(selectedArticle.stock_real);
    } else if (type === "surplus") {
      setPhysicalCount(selectedArticle.stock_real + 1);
    } else if (type === "shortage") {
      setPhysicalCount(Math.max(0, selectedArticle.stock_real - 1));
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
    } catch {
      setFeedback({
        type: "error",
        message: "Error en la búsqueda del artículo.",
      });
    }
  };

  // Fast-path lookup for camera scanned barcode
  const handleBarcodeScanned = async (code: string) => {
    setFeedback(null);
    const trimmed = code.trim();
    if (!trimmed) return;

    try {
      // 1. Exact match via port
      const exactResult = await client.getArticuloByBarcode(trimmed);
      if (exactResult) {
        selectArticle(exactResult);
        setFeedback({
          type: "success",
          message: `Artículo "${exactResult.des_articulo}" identificado por código de barras.`,
        });
        return;
      }

      // 2. Search fallback
      const searchResults = await client.searchArticulos(trimmed);
      if (searchResults.length > 0) {
        selectArticle(searchResults[0]);
        setFeedback({
          type: "success",
          message: `Artículo "${searchResults[0].des_articulo}" encontrado.`,
        });
      } else {
        setFeedback({
          type: "error",
          message: `Código "${trimmed}" no encontrado en el catálogo.`,
        });
      }
    } catch {
      setFeedback({
        type: "error",
        message: "Error al consultar el artículo escaneado.",
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
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setFeedback({ type: "error", message: `Error al registrar: ${msg}` });
    }
  };

  return (
    <DemoShell>
      <div className="max-w-3xl mx-auto py-4 sm:py-8 space-y-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            Auditoría de Stock
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Escanee códigos con la cámara del dispositivo o busque manualmente.
          </p>
        </div>

        {/* Search Bar with Camera Trigger and Autocomplete Dropdown */}
        <div ref={searchContainerRef} className="relative">
          <form
            onSubmit={handleSearchSubmit}
            className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 sm:gap-3"
          >
            <div className="flex-1 bg-white border border-slate-200 rounded-xl flex items-center px-3 sm:px-4 py-2 sm:py-3 shadow-sm focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500 transition-all">
              <Search className="w-5 h-5 text-slate-400 mr-2 sm:mr-3 shrink-0" />
              <input
                type="text"
                value={barcodeQuery}
                onChange={(e) => {
                  const val = e.target.value;
                  setBarcodeQuery(val);
                  if (!val.trim()) {
                    setSuggestions([]);
                    setShowDropdown(false);
                  }
                }}
                onFocus={() => {
                  if (suggestions.length > 0) setShowDropdown(true);
                }}
                onKeyDown={(e) => {
                  if (e.key === "Escape") {
                    setShowDropdown(false);
                  }
                }}
                placeholder="Buscar por código de barras o nombre..."
                className="w-full text-slate-900 placeholder-slate-400 focus:outline-none text-sm sm:text-base"
                autoFocus
              />

              {/* Clear search button */}
              {barcodeQuery && (
                <button
                  type="button"
                  onClick={handleClearSearch}
                  className="p-1.5 text-slate-400 hover:text-slate-600 rounded-full transition-colors mr-1 cursor-pointer"
                  aria-label="Limpiar búsqueda"
                >
                  <X className="w-4 h-4" />
                </button>
              )}

              {/* Prominent Camera Barcode Scanner Button */}
              <button
                type="button"
                onClick={() => setIsScannerOpen(true)}
                aria-label="Escanear con cámara"
                className="w-11 h-11 rounded-lg flex items-center justify-center text-slate-500 hover:text-blue-600 hover:bg-blue-50 active:scale-95 transition-all shrink-0 cursor-pointer"
                title="Escanear con cámara"
              >
                <ScanBarcode className="w-5 h-5" />
              </button>
            </div>

            <button
              type="submit"
              className="h-12 px-6 sm:px-8 bg-[#1a56db] hover:bg-blue-700 active:scale-95 text-white font-medium text-sm sm:text-base rounded-xl shadow-sm transition-all cursor-pointer flex items-center justify-center"
            >
              Buscar
            </button>
          </form>

          {/* Autocomplete Dropdown List */}
          {showDropdown && barcodeQuery.trim().length > 0 && (
            <div className="absolute left-0 right-0 top-full mt-2 bg-white border border-slate-200 rounded-xl shadow-xl z-30 max-h-80 overflow-y-auto divide-y divide-slate-100">
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
          <div className="p-4 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm flex items-start gap-3">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <span>{feedback.message}</span>
          </div>
        )}

        {feedback && feedback.type === "success" && (
          <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-100 text-emerald-700 text-sm flex items-start gap-3">
            <CheckCircle2 className="w-5 h-5 shrink-0 mt-0.5" />
            <span>{feedback.message}</span>
          </div>
        )}

        {/* Main Content Area */}
        {selectedArticle ? (
          <div className="space-y-6">
            {/* Item Card */}
            <div className="bg-white rounded-2xl border border-slate-200 p-5 sm:p-6 shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
                <h2 className="text-lg sm:text-xl font-bold text-slate-900 leading-snug">
                  {selectedArticle.des_articulo}
                </h2>
                <div>
                  {selectedArticle.fue_auditado ? (
                    <span className="inline-flex px-3 py-1 rounded-full bg-emerald-100 text-emerald-700 text-xs font-bold uppercase tracking-wider">
                      AUDITADO
                    </span>
                  ) : (
                    <span className="inline-flex px-3 py-1 rounded-full bg-amber-50 text-amber-600 border border-amber-200 text-xs font-bold uppercase tracking-wider">
                      PENDIENTE
                    </span>
                  )}
                </div>
              </div>

              <hr className="border-slate-100 mb-5" />

              <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 sm:gap-6 mb-5">
                <div>
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-1">
                    MARCA
                  </div>
                  <div className="text-xs sm:text-sm font-medium text-slate-900">
                    {selectedArticle.des_marca || "-"}
                  </div>
                </div>
                <div>
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-1">
                    FAMILIA
                  </div>
                  <div className="text-xs sm:text-sm font-medium text-slate-900">
                    {selectedArticle.des_familia || "-"}
                  </div>
                </div>
                <div className="col-span-2 sm:col-span-1">
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-1">
                    CÓDIGO
                  </div>
                  <div className="text-xs sm:text-sm font-medium text-slate-900 font-mono">
                    {selectedArticle.cod_barras[0] || selectedArticle.id_articulo}
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
            <div className="bg-white rounded-2xl border border-slate-200 p-5 sm:p-6 shadow-sm">
              <h3 className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-5">
                REGISTRAR CONTEO FÍSICO
              </h3>

              <form onSubmit={handleAuditSubmit} className="space-y-6">
                {/* Action Type Selector */}
                <div>
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2.5">
                    Acción Rápida
                  </label>
                  <div className="grid grid-cols-3 gap-2.5">
                    <button
                      type="button"
                      onClick={() => handleActionClick("surplus")}
                      className={`h-12 rounded-xl text-xs sm:text-sm font-medium border transition-all cursor-pointer active:scale-95 ${
                        actionType === "surplus"
                          ? "bg-blue-50 border-blue-400 text-blue-900 font-bold shadow-xs"
                          : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
                      }`}
                    >
                      Sobrante
                    </button>
                    <button
                      type="button"
                      onClick={() => handleActionClick("shortage")}
                      className={`h-12 rounded-xl text-xs sm:text-sm font-medium border transition-all cursor-pointer active:scale-95 ${
                        actionType === "shortage"
                          ? "bg-red-50 border-red-300 text-red-900 font-bold shadow-xs"
                          : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
                      }`}
                    >
                      Faltante
                    </button>
                    <button
                      type="button"
                      onClick={() => handleActionClick("none")}
                      className={`h-12 rounded-xl text-xs sm:text-sm font-medium border transition-all cursor-pointer active:scale-95 ${
                        actionType === "none"
                          ? "bg-emerald-50 border-emerald-400 text-emerald-900 font-bold shadow-xs"
                          : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
                      }`}
                    >
                      Exacto
                    </button>
                  </div>
                </div>

                {/* Audited Quantity Stepper */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider">
                      Cantidad Contada
                    </label>
                    <button
                      type="button"
                      onClick={() => setPhysicalCount(selectedArticle.stock_real)}
                      className="text-xs font-semibold text-blue-600 hover:text-blue-700 hover:underline cursor-pointer"
                    >
                      Copiar Stock ({selectedArticle.stock_real})
                    </button>
                  </div>

                  <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                    {/* Stepper with 48x48px targets */}
                    <div className="flex items-center bg-slate-50 border border-slate-200 rounded-xl p-1 w-full sm:w-60 shadow-sm focus-within:border-blue-500 focus-within:ring-2 focus-within:ring-blue-500/20 transition-all">
                      {/* Minus Button */}
                      <button
                        type="button"
                        onClick={decrement}
                        disabled={physicalCount !== "" && Number(physicalCount) <= 0}
                        aria-label="Disminuir cantidad"
                        className="w-12 h-12 rounded-lg bg-white border border-slate-200 text-slate-700 hover:bg-slate-100 hover:text-slate-900 active:scale-95 transition-all flex items-center justify-center shadow-xs shrink-0 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                        title="Restar 1"
                      >
                        <Minus className="w-5 h-5 stroke-[2.5]" />
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
                        className="w-0 flex-1 min-w-0 h-12 text-center font-extrabold text-2xl text-slate-900 bg-transparent focus:outline-none placeholder:text-slate-300 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                      />

                      {/* Plus Button */}
                      <button
                        type="button"
                        onClick={increment}
                        aria-label="Aumentar cantidad"
                        className="w-12 h-12 rounded-lg bg-[#1a56db] text-white hover:bg-blue-700 active:scale-95 transition-all flex items-center justify-center shadow-xs shrink-0 cursor-pointer"
                        title="Sumar 1"
                      >
                        <Plus className="w-5 h-5 stroke-[2.5]" />
                      </button>
                    </div>

                    {/* Quick Adjustment Chips */}
                    <div className="flex items-center gap-2">
                      {[1, 5, 10].map((step) => (
                        <button
                          key={step}
                          type="button"
                          onClick={() =>
                            setPhysicalCount((prev) =>
                              prev === "" ? step : Number(prev) + step
                            )
                          }
                          className="flex-1 sm:flex-none h-12 px-4 rounded-xl bg-slate-100 hover:bg-blue-50 hover:text-blue-700 hover:border-blue-200 border border-slate-200 text-xs sm:text-sm font-bold text-slate-700 transition-all cursor-pointer active:scale-95 flex items-center justify-center"
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
                  <label className="block text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                    Motivo / Observación
                  </label>
                  <select
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    className="w-full h-12 px-4 bg-white border border-slate-200 rounded-xl text-sm text-slate-700 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all cursor-pointer"
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
                  className="w-full h-14 bg-[#0e9f6e] hover:bg-[#057a55] active:scale-[0.99] text-white font-bold rounded-xl flex items-center justify-center gap-2.5 transition-all shadow-md cursor-pointer text-base pb-safe"
                >
                  <Check className="w-5 h-5 stroke-[2.5]" />
                  <span>Registrar Auditoría</span>
                </button>
              </form>
            </div>
          </div>
        ) : (
          /* Empty State */
          <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
            <div className="w-16 h-16 rounded-2xl bg-slate-100 flex items-center justify-center text-slate-400 mb-4 shadow-xs">
              <ScanBarcode className="w-8 h-8" />
            </div>
            <h2 className="text-base font-bold text-slate-800 mb-1">
              Comenzar conteo de stock
            </h2>
            <p className="text-slate-500 text-xs sm:text-sm max-w-sm">
              Presione el ícono de cámara en la barra para escanear un código de barras o escriba el nombre del artículo.
            </p>
          </div>
        )}

        {/* Barcode Scanner Modal */}
        <BarcodeScannerModal
          isOpen={isScannerOpen}
          onClose={() => setIsScannerOpen(false)}
          onDetected={handleBarcodeScanned}
        />
      </div>
    </DemoShell>
  );
}
