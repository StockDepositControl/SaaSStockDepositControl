# US-06: Smart Data Seeding for Multi-Tenant Security and Analytics Testing

## 1. Context & Objectives

Following the implementation of our security foundation (US-05), we need a robust, realistic data ecosystem to thoroughly validate tenant isolation, multi-tenancy boundaries (`id_sucursal`), and Role-Based Access Control (RBAC) rules.

Your task is to develop a smart data seeding script for "Global Medica (Phase 1)". This script will populate the database using the Faker library, generating realistic but fictitious operational data. The main objective is twofold:

- Allow the generation of valid JWT tokens for diverse user profiles to test security middleware isolation.
- Inject specific data anomalies (edge cases) that will stress-test downstream analytical reports and field-level restriction guards.

## 2. Technical Constraints & Standards

You must strictly adhere to the following guardrails during implementation:

- **Hexagonal Architecture Boundaries:** The seeding engine belongs strictly to the infrastructure layer (`backend/app/adapters/database/seeds/` or the designated database management CLI). It must interact with the system via application use cases or repository ports, ensuring that no infrastructure-specific generation logic bleeds into the pure domain layer.
- **Financial Precision (Decimal):** Absolutely no float types are allowed for monetary or financial representation. Any generated price, cost, or financial valuation (such as `pcio_com_siva`) must strictly utilize `decimal.Decimal` to ensure zero rounding errors.
- **Database Constraints:** This is a MariaDB project. The seeding script must use compatible SQLAlchemy constructs, raw SQL text optimized for MariaDB, or standard repository patterns. Do not write PostgreSQL-specific syntax, arrays, or JSONB operations.
- **Determinism and Reproducibility:** The seeding script must accept an optional seed parameter for the Faker generator so identical, predictable datasets can be reproduced across different testing cycles.

## 3. Explicit Acceptance Criteria to Implement

You are expected to build and verify the following components:

### A. Parameterized Seeding Engine Configuration

- Integrate the Faker library into a modular seeding script.
- Parameterize the execution to inject a default volume of 500 articles, ensuring they are logically and evenly distributed across multiple warehouses (depósitos) and branches (sucursales).

### B. Security & Tenant Mapping (Users, Roles & Branches)

- Create test user accounts mapping exactly to the three system roles defined in the domain Enum: administrador, supervisor, and auditor.
- Each generated user must be explicitly linked to a specific branch (`id_sucursal`).
- The data structure generated must provide all necessary fields (for example, hashed passwords, active status, claims) to seamlessly enable the TokenProvider to issue valid JWT tokens simulating the access of each specific profile.

### C. Analytical Edge Cases & Data Degradation Injection

To properly stress analytical reports, the script must programmatically inject the following realistic defective states:

- **Inventory Anomaly:** Inject a significant subset of articles featuring a positive theoretical stock but a real physical stock of exactly zero.
- **Batch Expiration Stress:** Generate a heavy, dense volume of expired inventory lots (lotes vencidos), distributed unevenly across warehouses to challenge date-filtering and risk-assessment analytics.
- **Sensitive Financial Fields:** Ensure all generated inventory items include sensitive pricing fields (for example, `pcio_com_siva`) modeled strictly as `decimal.Decimal` to validate the field-stripping mechanisms built for non-admin roles.

### D. Execution & CLI Hook

- Provide a clean CLI entry point (for example, `python manage.py db:seed --count 500`) allowing developers and automated CI/CD pipelines to run, reset, or scale the generated dataset easily.