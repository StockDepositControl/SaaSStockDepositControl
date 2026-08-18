"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useDataClient } from "@/lib/hooks/useDataClient";
import { ClipboardCheck, Eye, EyeOff, AlertCircle } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { login } = useDataClient();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Error de autenticación");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 p-6 relative">
      <div className="w-full max-w-[440px] z-10">
        <div className="bg-white rounded-2xl shadow-lg border border-slate-100 overflow-hidden relative">
          {/* Top Blue Border */}
          <div className="absolute top-0 left-0 w-full h-1.5 bg-[#1a56db]" />

          <div className="p-8 sm:p-10 pb-8">
            {/* Logo / Brand Header */}
            <div className="flex flex-col items-center mb-8">
              <div className="w-14 h-14 rounded-full border-2 border-[#1a56db] flex items-center justify-center mb-5 text-[#1a56db]">
                <ClipboardCheck className="w-6 h-6" strokeWidth={2} />
              </div>
              <div className="text-center">
                <h1 className="text-2xl font-bold text-slate-900 mb-2">
                  Audit Global
                </h1>
                <p className="text-slate-500 text-sm">
                  Sistema de Control y Auditoría de Inventario
                </p>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              {error && (
                <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-600 text-sm flex items-start gap-2.5">
                  <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                  <span>{error}</span>
                </div>
              )}

              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="block text-sm font-medium text-slate-900">
                    Correo electrónico
                  </label>
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="tu@globalmedica.com"
                    className="w-full bg-white border border-slate-200 rounded-lg px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-[#1a56db] focus:ring-1 focus:ring-[#1a56db] transition-all"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="block text-sm font-medium text-slate-900">
                    Contraseña
                  </label>
                  <div className="relative">
                    <input
                      type={showPassword ? "text" : "password"}
                      required
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full bg-white border border-slate-200 rounded-lg pl-4 pr-10 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-[#1a56db] focus:ring-1 focus:ring-[#1a56db] transition-all tracking-widest placeholder:tracking-widest"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                    >
                      {showPassword ? (
                        <EyeOff className="w-5 h-5" />
                      ) : (
                        <Eye className="w-5 h-5" />
                      )}
                    </button>
                  </div>
                </div>
              </div>

              <button
                type="submit"
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-[#1a56db] hover:bg-blue-700 active:scale-[0.98] transition-all text-white font-medium text-sm disabled:opacity-70 disabled:cursor-not-allowed mt-2"
              >
                {isLoading ? (
                  <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <span>Iniciar Sesión</span>
                )}
              </button>
            </form>
          </div>

          {/* Footer Area */}
          <div className="bg-slate-50 border-t border-slate-100 p-6 text-center">
            <p className="text-sm text-slate-500">
              El acceso está restringido por rol. Contacte a su administrador si no puede iniciar sesión.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

