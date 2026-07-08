# 📑 Functional Specifications & Business Rules Document

This document defines the comprehensive behavioral models, edge-case conditions, and analytical math engines for the Inventory Audit & Stock Control Platform. All Antigravity AI Agents must reference this specification as the Single Source of Truth (SSoT) to validate logic boundaries and interface implementation.

---

## 1. Core Platform Architecture Overview
The platform acts as an intelligent data layer optimizing warehouse operations. It bridges physical reality (what is found on the warehouse floor) with enterprise ledger theories (what the database claims exists), calculates financial implications of discrepancies, and predicts shelf-life alerts.

* **Phase 1 Execution (Global Medica):** Logical database isolation on a unified infrastructure instance using filtering clauses.
* **Phase 2 Execution (Farmanor Network):** Asynchronous switching across physical databases per branch initiated by token-based tenants.

---

## 2. Module 1: Mobile Operations (Field Field Application)

### 2.1 Omnichannel Inventory Discovery Pipeline
* **Hardware Interface:** The application interface must bind directly to the camera module with automated autofocus cycles targeting standard symbologies: EAN-13, QR codes, and DataMatrix layers.
* **Response Threshold:** Hardware validation loops must successfully register codes in `<1 second` under erratic ambient warehouse lighting.
* **Exception Handlers:** If a barcode layer suffers physical deterioration preventing scanning, the interface must instantly provide an optimized alphanumeric keypad or a local matching predictive string search filtering by item descriptor tokens.

### 2.2 Blind/Semi-Blind Audit Mechanism
To minimize human conformation bias, the interface execution pattern is governed by the following workflow rules:
1.  **Item Scan Trigger:** The operator scans an item barcode or selects it manually.
2.  **Theoretical Contrast Isolation:** The backend pipeline fetches the underlying database state (`Theoretical Stock`), but this variable remains hidden from the user interface viewport or is restricted behind a privileged visibility toggle.
3.  **Physical Counting Mandate:** The operator is required to manually input the actual quantity observed physically present on the shelves (`Real Stock`).
4.  **Discrepancy Evaluation Matrix:** The system immediately compares the assertions:
    $$\Delta \text{ Stock} = \text{Real Stock} - \text{Theoretical Stock}$$

### 2.3 Structural Movement Ledger ("Novedades")
Upon confirming a discrepancy value, the operator selects massive interface targets corresponding to three architectural state changes:
* **Alta (Stock Surplus):** Triggered when $\Delta \text{ Stock} > 0$. The system registers an infrastructure addition voucher tracking items found that were not accounted for in records.
* **Baja (Stock Deficit/Loss):** Triggered when $\Delta \text{ Stock} < 0$. The system flags a financial loss voucher indicating shrinkage, item breakage, or unaccounted consumption.
* **Sin Acción (Pristine Match):** Triggered when $\Delta \text{ Stock} = 0$. Structural records match reality; a confirmation heartbeat timestamp updates the specific table allocation row.

### 2.4 Offline-First Resiliency & Data Sync Pipeline
* **Local Storage Allocation:** When executing operations inside zero-signal environments or wireless dead-zones, state changes cannot abort. Payloads must immediately persist within an embedded, transaction-safe local engine (**SQLite / WatermelonDB**).
* **Queue Management:** State adjustments are stacked sequentially inside an outbound local sync queue table.
* **Asynchronous Reconnection Handshake:** A background background synchronization worker continually tracks web api availability. Once a reliable HTTP network connection is re-established, the background worker initiates a batch payload transmission, flushing local records into the remote MariaDB cluster securely.

---

## 3. Module 2: Core Calculation & Expiration Engines (Backend)

### 3.1 Conditional Fiscal Calculation Engine (VAT / IVA)
Financially modeling shrinkage or inventory adjustments requires tracking tax exemptions defined by catalog classifications:
* **Tax Classification Lookup:** The service engine parses individual records checking foreign relation metadata associations: `id_familia` or `id_grupo`.
* **Exemption Condition Logic:** * If the parent classification maps to the **"Medicamentos" (Medicines)** family, the fiscal calculator flags the element as untaxed. The gross monetary estimation evaluates purely on cost-price variables (`pcio_com_siva`).
    * If the item maps to any alternative classification (such as perfumery, cosmetics, or auxiliary accessories), the engine applies the standard corporate value-added modifier (Standard VAT / IVA) directly over the base price before compiling structural balances.

### 3.2 FEFO (First Expired, First Out) Scheduling Engine
Warehouse inventory management requires prioritizing items with closer shelf-life limits to limit fiscal deterioration. The engine executes under these strict constraints:
* **Batch Tracking Constraints:** Items with multiple production lifecycles must be broken down by unique identifier lots mapped under `Lots_per_Deposit`.
* **Sorting Sorting Rule:** All queries returning target item batches must evaluate the explicit `fecha_vencimiento` date field, ordering records sequentially from closest expiration target to furthest.
* **Semaphoric Alert Stratification:** The system calculates real-time day intervals remaining until expiration dates, appending warning tokens to the analytical payload structure:
    * 🔴 **Critical Tier (Immediate Action Required):** $\le 30 \text{ days}$ remaining.
    * 🟡 **Warning Tier (Medium Risk Allocation):** $> 30 \text{ days}$ and $\le 60 \text{ days}$ remaining.
    * 🔵 **Attention Tier (Routine Monitor Matrix):** $> 60 \text{ days}$ and $\le 90 \text{ days}$ remaining.

---

## 4. Module 3: Management Analytical Dashboard (Web Panel)

### 4.1 Daily Ledger Synchronization & Profitability Metrics
The management analytical interface renders corporate operational efficiency values updated in real-time by database ledger operations.
* **Core Balance Formula:** The main component updates a financial metric derived as follows:
    $$\text{Day Net Balance} = \sum (\text{Financial Gains from Altas}) - \sum (\text{Financial Losses from Bajas})$$
* **Value Multiplier:** Financial Loss/Gain is derived by evaluating the delta changes against item purchase costs (`pcio_com_siva`) combined with its conditional fiscal VAT factor.

### 4.2 Expiration Risk Overview Matrix
The web dashboard renders interactive graphical distributions highlighting forthcoming product expiration vulnerabilities across the five system deposits. This grid prioritizes sorting lots inside the Critical Tier (30 days) to coordinate quick inventory adjustments or liquidations.

---

## 5. Simulation Data Requirements (Seeding Blueprint)

To test system thresholds safely without modifying live client infrastructures, the database agent (`dba-agent`) must construct a parametric script (`seed.py`) reflecting complex real-world conditions.

### 5.1 Volume Configuration Parameters
* **Scale Metrics:** Default configuration generates **500 distinct items** mapped cleanly across **5 virtual warehouses/deposits**.
* **Relational Integrity Constraints:** Generated objects must feature valid structural records cross-linked to appropriate attributes for `Families`, `Groups`, `Brands` (Laboratories), and valid contextual barcode strings.

### 5.2 Failure Modes Injection Matrix
The seed generator must programmatically pollute the database with three intentional real-world inventory operational anomalies:
* **Anomalous State A (The Ghost Item):** Items featuring a positive `Theoretical Stock` metric (>0) within the database tables, but whose `Physical Stock` values are written as zero. This forces mobile clients to evaluate shrinkage workflows.
* **Anomalous State B (Expired Lot Clusters):** Programmatically allocate at least 25% of total lot rows with `fecha_vencimiento` stamps preset to previous calendar months. This guarantees that the FEFO scheduler returns critical alerts during testing.
* **Anomalous State C (Fiscal Mix Testing Vector):** Construct a precise distribution split among catalog items: 50% must fall within the tax-exempt "Medicamentos" category, while the alternative 50% must match taxable items to test tax evaluation workflows.

---

## 6. Acceptance Testing Criteria (Functional Validation Protocols)

All created routes, data structures, and client components must satisfy these functional constraints during local automation suites:

### 6.1 Protocol A: Offline Resiliency Verification
* **Execution Vector:** Set a mobile test client to Airplane Mode while an active audit run is in progress. Execute 10 distinct inventory delta movements (including Altas and Bajas). Shut down the mobile runtime memory context entirely.
* **Evaluation Threshold:** Upon rebooting the mobile application and reconnecting the wireless interface, the network queue must broadcast payloads via batch transmission without record omission, updating target server MariaDB tables accurately.

### 6.2 Protocol B: Decimal Reconciliation Precision Check
* **Execution Vector:** Process a test dataset containing exactly 5 items flagged within the "Medicamentos" category and 5 taxable items through the audit pipeline. Inject matching stock deficits into all of them.
* **Evaluation Threshold:** The analytical dashboard's reported financial loss must reconcile down to the exact decimal point against a pre-calculated reference sheet. Any floating-point approximations or rounding anomalies will result in an immediate test failure.

### 6.3 Protocol C: Cross-Tenant Isolation Safeguard ("The Phantom Tenant")
* **Execution Vector:** Establish concurrent client test connections: User X authenticated under `Tenant ID: GlobalMedica_01` and User Y authenticated under `Tenant ID: Farmanor_Branch_02`. Trigger simultaneous stock modification queries targeting the exact same generic product barcode string.
* **Evaluation Threshold:** Changes committed by User X must restrict state impact exclusively to records flagged under tenant context 01. User Y must remain completely isolated from these updates, and zero database table reads or mutations may cross isolated tenant boundaries.