# Backend Schema, Repository, and API Inconsistencies & Refined Solution Proposals

## Executive Summary
This document outlines the refined architectural problems and exact technical solutions for `@backend/`. Following project rules and domain decisions, domain entities are aligned directly with physical database ORM models (using English names matching the ORM schema where specified), domain models are cleaned of non-existent columns, multi-tenant isolation is enforced, and user-facing endpoints/roles are strictly standardized in Spanish.

---

## Section 1: Data Models (ORM vs. Domain Models)

### 1.1 `Familia` & `Grupo` Primary Key Data Types
* **Problem**: 
  * In the ORM layer ([articles.py (ORM)](file:///home/fede/Proyectos/SaaSStockDepositControl/backend/adapters/repositories/models/articles.py#L23-L33)), `id_familia` and `id_grupo` represent string codes (`VARCHAR(11)` / `String`).
  * In domain Pydantic models ([articles.py (Domain)](file:///home/fede/Proyectos/SaaSStockDepositControl/backend/app/articles/models.py#L15-L22)), `Familia.id_familia`, `GrupoBase.id_familia`, and `GrupoBase.id_grupo` are incorrectly declared as integers (`int`).
* **Refined Solution**:
  * Update `Familia`, `GrupoBase`, and `Grupo` in `backend/app/articles/models.py` to use `str` for `id_familia` and `id_grupo` (`VARCHAR(11)` compatible), preserving zero-padded codes without integer truncation.

### 1.2 `Articulo` Schema `tenant_id` Removal
* **Problem**:
  * `ArticuloBase` in `backend/app/articles/models.py` currently contains `tenant_id: Optional[str] = None`.
  * The physical `articulos` table belongs to the client's database (`db_articles`) and does NOT contain a `tenant_id` column.
* **Refined Solution**:
  * Remove `tenant_id` completely from `ArticuloBase`, `Articulo`, and all article domain DTOs in `backend/app/articles/models.py`.

### 1.3 `User` Domain Model Alignment with `UserORM`
* **Problem**:
  * Domain model `User` in `backend/app/users/models.py` uses `id_usuario`, `nombre_completo`, and a single `rol` string, whereas `UserORM` in `backend/adapters/repositories/models/users.py` uses `user_id` (`int`), `tenant_id` (`int`), `first_name` (`str`), `last_name` (`str`), `email` (`str`), `password_hash` (`str`), `branch_id` (`Optional[int]`), `is_active` (`bool`), and a `roles` relationship.
* **Refined Solution**:
  * Align the domain `User` model in `backend/app/users/models.py` directly with `UserORM` structure:
    * Replace `id_usuario` with `user_id: int`.
    * Use `tenant_id: int`.
    * Replace `nombre_completo` with `first_name: str` and `last_name: str`.
    * Include `is_active: bool`, `branch_id: Optional[int]`, and `roles: List[Role]`.

### 1.4 Primary Keys & Attribute Cleanup in `StockPorDeposito` & `LotePorDeposito`
* **Problem**:
  * `StockPorDepositoBase` in `backend/app/movements/models.py` includes non-existent columns `fue_auditado` and `fecha_hora_auditacion`, and omits `id_empresa` which is part of the table's composite primary key.
  * `LotePorDepositoBase` omits `id_empresa` and `id_sucursal` (which form the primary key alongside `id_deposito`, `id_articulo`, and `lote`) and parses `vencimiento` as `date` instead of `Optional[str]` (`VARCHAR(11)`).
* **Refined Solution**:
  * **`StockPorDeposito`**: Delete `fue_auditado` and `fecha_hora_auditacion` from the domain model. Add `id_empresa: int` to `StockPorDepositoBase` so the primary key `(id_empresa, id_sucursal, id_deposito, id_articulo)` matches the ORM model.
  * **`LotePorDeposito`**: Include `id_empresa: int` and `id_sucursal: int` in `LotePorDepositoBase`. Set `vencimiento: Optional[str]` (`VARCHAR(11)`), matching `LotePorDeposito` ORM.

### 1.5 Domain `AuditoriaRegistro` Renaming & Exact Alignment to `AuditRecord`
* **Problem**:
  * Domain model `AuditoriaRegistro` uses Spanish field names (`id_auditoria`, `id_sucursal`, `id_deposito`, `id_articulo`, `id_usuario`, `tipo_accion`, `fecha_hora`) and missing/extra fields (`audit_action_type`), whereas ORM uses `AuditRecord` with English column names (`audit_id`, `tenant_id`, `branch_id`, `warehouse_id`, `article_code`, `user_id`, `action_type`, `affected_amount`, `audit_quantity`, `applied_unit_cost`, `applied_vat_rate`, `valorized_amount`, `scan_timestamp`, `client_uuid`, `observation`).
* **Refined Solution**:
  * Rename the domain model `AuditoriaRegistro` to `AuditRecord` in `backend/app/movements/models.py`.
  * Align domain fields 1:1 with `AuditRecordORM` using exact English field names (`audit_id`, `tenant_id`, `branch_id`, `warehouse_id`, `article_code`, `user_id`, `action_type`, `affected_amount`, `audit_quantity`, `applied_unit_cost`, `applied_vat_rate`, `valorized_amount`, `scan_timestamp`, `client_uuid`, `observation`).

---

## Section 2: Repositories (Data Access Layer)

### 2.1 Unification of `audit_action_type` into `action_type` & English Column Alignment
* **Problem**:
  * `SQLAlchemyAuditRepository` ([audit_repository.py:L58](file:///home/fede/Proyectos/SaaSStockDepositControl/backend/adapters/repositories/audit_repository.py#L58)) attempts to pass `audit_action_type` to `AuditRecordORM`, which causes runtime crashes because `audit_action_type` is not an ORM column.
  * Line 132 sets `audit_action_type=orm_record.observation`, corrupting action types with observation notes.
* **Refined Solution**:
  * Treat `action_type` as the single canonical attribute (matching `AuditRecordORM`). Remove all references to `audit_action_type`.
  * Ensure `SQLAlchemyAuditRepository` works exclusively with English attribute names matching `AuditRecordORM`.

### 2.2 Correct Financial Unit Cost Mapping in `create_audit_record()`
* **Problem**:
  * In [audit_repository.py:L52-L54](file:///home/fede/Proyectos/SaaSStockDepositControl/backend/adapters/repositories/audit_repository.py#L52-L54), `applied_unit_cost` is assigned `record.monto_valorizado` (the total valorized cost), rather than the unit cost.
* **Refined Solution**:
  * Pass the purchase unit cost (`pcio_com_siva`) into `applied_unit_cost` (and default VAT rate into `applied_vat_rate`), while storing total valorized amount in `valorized_amount`.

### 2.3 Strict Multi-Tenant Filtering in `SQLAlchemyUserRepository`
* **Problem**:
  * `get_by_email()` and `get_by_id()` in `SQLAlchemyUserRepository` omit `tenant_id` filtering from their SQL `.where()` clauses.
* **Refined Solution**:
  * Include `UserORM.tenant_id == active_tenant` in the `.where()` clause of `get_by_id()` and `get_by_email()` to enforce database-level tenant isolation.

### 2.4 Composite Primary Key Scope in `SQLAlchemyStockRepository`
* **Problem**:
  * `get_stock_position()` filters `StockPorDepositoORM` only by `(id_sucursal, id_deposito, id_articulo)`, omitting `id_empresa`.
* **Refined Solution**:
  * Include `id_empresa` in the SQL `.where()` filter matching the 4-column primary key `(id_empresa, id_sucursal, id_deposito, id_articulo)`.

---

## Section 3: API Endpoints & Request Processing

### 3.1 Strict Spanish Action Types for Endpoints (`"Alta"`, `"Baja"`, `"Sin Acción"`)
* **Problem**:
  * Backend service logic was accepting mixed English/Spanish action strings (`"ADDITION"`, `"REMOVAL"`).
* **Refined Solution**:
  * Enforce strictly Spanish action strings (`"Alta"`, `"Baja"`, `"Sin Acción"`) across API request payloads (`AuditEntryRequest`), `TipoAccion` enum, and endpoint processing. Disallow English action strings in the API layer. Map Spanish actions to ORM `action_type` values in the repository layer.

### 3.2 Strict Spanish Role Enforcement
* **Problem**:
  * Database seed script inserted English role names (`"ADMINISTRATOR"`), causing mismatches with Spanish `UserRole` enum (`"administrador"`).
* **Refined Solution**:
  * Enforce strictly Spanish role names across the application, database seed scripts (`seed.py`), and `UserRole` enum (`"administrador"`, `"supervisor"`, `"auditor"`). Remove all references to English role names.
