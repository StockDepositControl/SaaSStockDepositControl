"use client";

import React, { useState } from "react";
import { useDataClient } from "@/lib/hooks/useDataClient";
import { DemoShell } from "@/components/layout/DemoShell";
import { ArticuloPublicView, ArticuloAdminView } from "@/lib/types/domain";
import { ClipboardCheck, ScanBarcode, CheckCircle2, AlertCircle, ArrowRight } from "lucide-react";

export default function AuditPage() {
  const { client, articles } = useDataClient();
  const [barcodeQuery, setBarcodeQuery] = useState("");
  const [selectedArticle, setSelectedArticle] = useState<ArticuloPublicView | ArticuloAdminView | null>(null);
  const [physicalCount, setPhysicalCount] = useState<number | "">("");
  const [lot, setLot] = useState("");
  const [notes, setNotes] = useState("");
  const [feedback, setFeedback] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setFeedback(null);
    if (!barcodeQuery.trim()) return;

    try {
      const result = await client.getArticuloByBarcode(barcodeQuery);
      if (result) {
        setSelectedArticle(result);
        setPhysicalCount("");
        setLot("");
      } else {
        setSelectedArticle(null);
        setFeedback({ type: "error", message: "Artículo no encontrado." });
      }
    } catch (err: unknown) {
      setFeedback({ type: "error", message: "Error en búsqueda de artículo." });
    }
  };

  const handleAuditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedArticle || physicalCount === "") return;

    try {
      const auditResult = await client.registerAudit({
        id_articulo: selectedArticle.id_articulo,
        stock_fisico_contado: Number(physicalCount),
        lote: lot || undefined,
        observation: notes || undefined,
      });

      setFeedback({
        type: "success",
        message: `Auditoría registrada: ${auditResult.des_articulo}. Discrepancia: ${auditResult.delta_stock}`,
      });
      setSelectedArticle(null);
      setBarcodeQuery("");
      setPhysicalCount("");
      setLot("");
      setNotes("");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      setFeedback({ type: "error", message: `Error al registrar: ${msg}` });
    }
  };

  return (
    <DemoShell>
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
              <ClipboardCheck className="w-8 h-8 text-indigo-400" />
              <span>Auditoría de Stock Operativo</span>
            </h1>
            <p className="text-sm text-slate-400 mt-1">
              Escanea el código de barras o EAN y registra el conteo físico de la góndola.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Scanner / Search Area */}
          <div className="glass-panel rounded-3xl p-6 border border-slate-800 space-y-6">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <ScanBarcode className="w-5 h-5 text-indigo-400" />
              <span>Escáner de Artículo</span>
            </h2>

            <form onSubmit={handleSearch} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-2">
                  EAN / Código Interno
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={barcodeQuery}
                    onChange={(e) => setBarcodeQuery(e.target.value)}
                    placeholder="Escanear o tipear código..."
                    className="flex-1 bg-slate-900/80 border border-slate-700/80 rounded-xl px-4 py-3 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all font-mono"
                    autoFocus
                  />
                  <button
                    type="submit"
                    className="px-5 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold transition shadow-md"
                  >
                    Buscar
                  </button>
                </div>
              </div>
            </form>

            {feedback && feedback.type === "error" && (
              <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-sm flex items-start gap-2.5">
                <AlertCircle className="w-5 h-5 shrink-0" />
                <span>{feedback.message}</span>
              </div>
            )}
            
            {feedback && feedback.type === "success" && (
              <div className="p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-sm flex items-start gap-2.5">
                <CheckCircle2 className="w-5 h-5 shrink-0" />
                <span>{feedback.message}</span>
              </div>
            )}
          </div>

          {/* Audit Action Area */}
          <div className={`glass-panel rounded-3xl p-6 border transition-all duration-300 ${selectedArticle ? 'border-indigo-500/50 shadow-[0_0_30px_-5px_rgba(99,102,241,0.2)]' : 'border-slate-800 opacity-50'}`}>
            <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-6">
              <span>Registro de Conteo</span>
            </h2>

            {selectedArticle ? (
              <form onSubmit={handleAuditSubmit} className="space-y-4">
                <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-700/60 mb-4">
                  <div className="text-sm font-semibold text-white mb-1 truncate" title={selectedArticle.des_articulo}>
                    {selectedArticle.des_articulo}
                  </div>
                  <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
                    <span className="text-indigo-400">{selectedArticle.id_articulo}</span>
                    <span>•</span>
                    <span>{selectedArticle.cod_barras[0]}</span>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-2">
                    Cantidad Física (Real)
                  </label>
                  <input
                    type="number"
                    min="0"
                    required
                    value={physicalCount}
                    onChange={(e) => setPhysicalCount(e.target.value === "" ? "" : Number(e.target.value))}
                    className="w-full bg-slate-900/80 border border-slate-700/80 rounded-xl px-4 py-3 text-lg font-bold text-white focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all font-mono"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-2">Lote</label>
                    <input
                      type="text"
                      value={lot}
                      onChange={(e) => setLot(e.target.value)}
                      placeholder="Opcional"
                      className="w-full bg-slate-900/80 border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500 transition-all font-mono"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-300 mb-2">Notas</label>
                    <input
                      type="text"
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      placeholder="Opcional"
                      className="w-full bg-slate-900/80 border border-slate-700/80 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-indigo-500 transition-all"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  className="w-full mt-4 flex items-center justify-center gap-2 py-3.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 active:scale-[0.98] transition-all text-white font-bold shadow-lg shadow-indigo-600/20"
                >
                  <span>Confirmar Auditoría</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              </form>
            ) : (
              <div className="flex flex-col items-center justify-center h-48 text-center text-slate-500 space-y-3">
                <ScanBarcode className="w-10 h-10 opacity-20" />
                <p className="text-sm max-w-xs">Escanea un artículo para habilitar el registro de conteo.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </DemoShell>
  );
}
