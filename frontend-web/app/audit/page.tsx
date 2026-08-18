"use client";

import React, { useState, useEffect } from "react";
import { useDataClient } from "@/lib/hooks/useDataClient";
import { DemoShell } from "@/components/layout/DemoShell";
import { ArticuloPublicView, ArticuloAdminView } from "@/lib/types/domain";
import { Search, Check, AlertCircle, CheckCircle2 } from "lucide-react";

export default function AuditPage() {
  const { client } = useDataClient();
  const [barcodeQuery, setBarcodeQuery] = useState("");
  const [selectedArticle, setSelectedArticle] = useState<ArticuloPublicView | ArticuloAdminView | null>(null);
  
  // Form State
  const [actionType, setActionType] = useState<"surplus" | "shortage" | "none" | null>(null);
  const [physicalCount, setPhysicalCount] = useState<number | "">("");
  const [reason, setReason] = useState("");
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

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

  const increment = () => setPhysicalCount(prev => (prev === "" ? 1 : prev + 1));
  const decrement = () => setPhysicalCount(prev => (prev === "" || prev <= 0 ? 0 : prev - 1));

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setFeedback(null);
    if (!barcodeQuery.trim()) return;

    try {
      const result = await client.getArticuloByBarcode(barcodeQuery);
      if (result) {
        setSelectedArticle(result);
        setPhysicalCount("");
        setActionType(null);
        setReason("");
      } else {
        setSelectedArticle(null);
        setFeedback({ type: "error", message: "Artículo no encontrado." });
      }
    } catch (err: unknown) {
      setFeedback({ type: "error", message: "Error en la búsqueda del artículo." });
    }
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
        message: `Auditoría registrada correctamente.`,
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
        <h1 className="text-3xl font-bold text-slate-900 mb-6">Auditoría de Stock</h1>

        {/* Search Bar */}
        <form onSubmit={handleSearch} className="flex items-center gap-3 mb-10">
          <div className="flex-1 bg-white border border-slate-200 rounded-xl flex items-center px-4 py-3 shadow-sm focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500 transition-all">
            <input
              type="text"
              value={barcodeQuery}
              onChange={(e) => setBarcodeQuery(e.target.value)}
              placeholder="Ingrese código de barras o nombre del artículo..."
              className="w-full text-slate-900 placeholder-slate-400 focus:outline-none text-base"
              autoFocus
            />
          </div>
          <button
            type="submit"
            className="px-8 py-3.5 bg-[#1a56db] hover:bg-blue-700 text-white font-medium rounded-xl shadow-sm transition-colors"
          >
            Buscar
          </button>
        </form>

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
                <h2 className="text-xl font-bold text-slate-900">{selectedArticle.des_articulo}</h2>
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
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-1">MARCA</div>
                  <div className="text-sm font-medium text-slate-900">{selectedArticle.des_marca || "-"}</div>
                </div>
                <div>
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-1">FAMILIA</div>
                  <div className="text-sm font-medium text-slate-900">{selectedArticle.des_familia || "-"}</div>
                </div>
                <div>
                  <div className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mb-1">CÓDIGO</div>
                  <div className="text-sm font-medium text-slate-900 font-mono">{selectedArticle.cod_barras[0] || selectedArticle.id_articulo}</div>
                </div>
              </div>
              
              <hr className="border-slate-100 mb-5" />
              
              <div className="flex items-baseline gap-2">
                <div className="text-[11px] font-bold text-slate-400 uppercase tracking-widest">STOCK ACTUAL</div>
                <div className="text-2xl font-bold text-slate-900 ml-2">{selectedArticle.stock_real}</div>
                <div className="text-sm font-medium text-slate-500">unidades</div>
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
                  <label className="block text-sm font-medium text-slate-500 mb-3">Acción</label>
                  <div className="grid grid-cols-3 gap-3">
                    <button
                      type="button"
                      onClick={() => handleActionClick("surplus")}
                      className={`py-2.5 rounded-lg text-sm font-medium border transition-colors ${
                        actionType === "surplus" 
                          ? "bg-slate-50 border-slate-400 text-slate-900" 
                          : "bg-white border-slate-200 text-slate-500 hover:bg-slate-50"
                      }`}
                    >
                      Sobrante
                    </button>
                    <button
                      type="button"
                      onClick={() => handleActionClick("shortage")}
                      className={`py-2.5 rounded-lg text-sm font-medium border transition-colors ${
                        actionType === "shortage" 
                          ? "bg-slate-50 border-slate-400 text-slate-900" 
                          : "bg-white border-slate-200 text-slate-500 hover:bg-slate-50"
                      }`}
                    >
                      Faltante
                    </button>
                    <button
                      type="button"
                      onClick={() => handleActionClick("none")}
                      className={`py-2.5 rounded-lg text-sm font-medium border transition-colors ${
                        actionType === "none" 
                          ? "bg-slate-50 border-slate-400 text-slate-900" 
                          : "bg-white border-slate-200 text-slate-500 hover:bg-slate-50"
                      }`}
                    >
                      Sin Acción
                    </button>
                  </div>
                </div>

                {/* Audited Quantity */}
                <div>
                  <label className="block text-sm font-medium text-slate-500 mb-3">Cantidad Auditada</label>
                  <div className="flex items-center border border-slate-200 rounded-lg h-12 overflow-hidden w-48">
                    <button
                      type="button"
                      onClick={decrement}
                      className="w-12 h-full flex items-center justify-center text-slate-500 hover:bg-slate-50 border-r border-slate-200 transition-colors"
                    >
                      -
                    </button>
                    <input
                      type="number"
                      min="0"
                      required
                      value={physicalCount}
                      onChange={(e) => setPhysicalCount(e.target.value === "" ? "" : Number(e.target.value))}
                      className="flex-1 h-full text-center font-bold text-lg text-slate-900 focus:outline-none focus:bg-slate-50 transition-colors"
                    />
                    <button
                      type="button"
                      onClick={increment}
                      className="w-12 h-full flex items-center justify-center text-slate-500 hover:bg-slate-50 border-l border-slate-200 transition-colors"
                    >
                      +
                    </button>
                  </div>
                </div>

                {/* Reason Dropdown */}
                <div>
                  <label className="block text-sm font-medium text-slate-500 mb-3">Motivo</label>
                  <select
                    value={reason}
                    onChange={(e) => setReason(e.target.value)}
                    className="w-full h-12 px-4 bg-white border border-slate-200 rounded-lg text-sm text-slate-700 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all appearance-none"
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
                  className="w-full h-12 mt-4 bg-[#0e9f6e] hover:bg-[#057a55] text-white font-bold rounded-lg flex items-center justify-center gap-2 transition-colors shadow-sm"
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
            <p className="text-slate-500 text-sm">Busque un artículo para comenzar a auditar</p>
          </div>
        )}
      </div>
    </DemoShell>
  );
}
