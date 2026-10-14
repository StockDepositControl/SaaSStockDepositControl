import { describe, it, expect } from "vitest";
import {
  mapArticleByRole,
  mapToArticuloPublicView,
  mapToArticuloAdminView,
  mapToDomainAuditResult,
} from "./mappers";
import { UserRole, TipoAccion } from "../types/domain";
import { ApiArticuloAdminOut, ApiAuditEntryResult } from "../types/api";

describe("mappers - RBAC Field Stripping & Conversions", () => {
  const rawAdminArticle: ApiArticuloAdminOut = {
    id_articulo: "ART-101",
    des_articulo: "Amoxicilina 500mg",
    presentacion: "Caja x 20 comp",
    id_marca: 1,
    des_marca: "Laboratorio Roemmers",
    id_familia: "FAM-MED",
    des_familia: "Medicamentos",
    id_grupo: "GRP-ANT",
    des_grupo: "Antibióticos",
    stock_real: 150,
    fue_auditado: true,
    pcio_com_siva: "4500.50",
  };

  it("should structurally exclude pcio_com_siva for AUDITOR role", () => {
    const result = mapArticleByRole(rawAdminArticle, UserRole.AUDITOR);
    expect("pcio_com_siva" in result).toBe(false);
    expect(result.id_articulo).toBe("ART-101");
    expect(result.stock_real).toBe(150);
  });

  it("should structurally exclude pcio_com_siva for SUPERVISOR role", () => {
    const result = mapArticleByRole(rawAdminArticle, UserRole.SUPERVISOR);
    expect("pcio_com_siva" in result).toBe(false);
  });

  it("should include numeric pcio_com_siva for ADMINISTRADOR role", () => {
    const result = mapArticleByRole(rawAdminArticle, UserRole.ADMINISTRADOR);
    expect("pcio_com_siva" in result).toBe(true);
    if ("pcio_com_siva" in result) {
      expect(result.pcio_com_siva).toBe(4500.5);
    }
  });

  it("mapToArticuloPublicView never outputs pcio_com_siva even if present in input", () => {
    const publicView = mapToArticuloPublicView(rawAdminArticle);
    expect("pcio_com_siva" in publicView).toBe(false);
    expect(Object.keys(publicView)).not.toContain("pcio_com_siva");
  });

  it("maps ApiAuditEntryResult correctly to domain AuditResult", () => {
    const apiAudit: ApiAuditEntryResult = {
      client_uuid: "uuid-1234",
      id_articulo: "ART-101",
      stock_real: 150,
      stock_fisico_contado: 140,
      delta_stock: -10,
      tipo_accion: TipoAccion.BAJA,
      cantidad_afectada: 10,
      audit_quantity: 140,
      monto_valorizado: "45005.00",
      audit_id: 42,
    };

    const domainAudit = mapToDomainAuditResult(apiAudit, "Amoxicilina 500mg", "Falta física");
    expect(domainAudit.client_uuid).toBe("uuid-1234");
    expect(domainAudit.audit_id).toBe(42);
    expect(domainAudit.delta_stock).toBe(-10);
    expect(domainAudit.monto_valorizado).toBe(45005);
    expect(domainAudit.tipo_accion).toBe(TipoAccion.BAJA);
    expect(domainAudit.observation).toBe("Falta física");
  });
});
