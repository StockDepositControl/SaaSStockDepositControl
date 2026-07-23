# 📑 Plan de Implementación Backend: Cobertura de User Stories (US 1 a US 6)

Este documento define el **análisis de requerimientos, diagnóstico de faltantes y la hoja de ruta en etapas para el Backend**, incorporando las confirmaciones de negocio de la plataforma **SaaSStockDepositControl**.

---

## 1. Análisis del Proyecto y Estado Actual

### 1.1 Estructura General del Repositorio
```
SaaSStockDepositControl/
├── backend/                  # API REST FastAPI + SQLAlchemy 2.0 Async + MySQL (Arquitectura Hexagonal)
├── frontend-web/             # Panel Web de Gestión (Next.js 14+ / React)
├── frontend-mobile/          # App Móvil de Auditoría de Campo (React Native / Expo)
├── docs/                     # Especificaciones funcionales y planes (SSoT)
└── .agents/                  # Reglas y habilidades de agentes AI
```

### 1.2 Estado Actual del Backend (`/backend`)
Actualmente, el backend cuenta con la **infraestructura base** y el diseño de **Arquitectura Hexagonal**:
* **`adapters/repositories/models.py`**: Modelos ORM de SQLAlchemy (`Usuario`, `Familia`, `Grupo`, `Marca`, `Articulo`, `StockPorDeposito`, `LotePorDeposito`, `AuditoriaRegistro`).
* **`app/`**: Dominio dividido en módulos (`articles`, `movements`, `users`, `ports`).
  * `articles/models.py` y `movements/models.py`: Schemas de Pydantic base.
  * `ports/database.py` y `ports/security.py`: Interfaces abstractas de conexión e identidad.
* **`api/`**: Servidor FastAPI.
  * `api/v1/auth.py`: Autenticación dummy/esqueleto JWT.
  * `api/v1/health.py`: Probe de salud del sistema.
* **Base de Datos**: Scripts de Alembic para migraciones iniciales (`migrations/`).

---

## 2. Definiciones de Negocio y Aclaraciones Confirmadas

A partir de las aclaraciones provistas para las User Stories:

1. **Valorización Financiera (US 6)**:
   * Confirma que **únicamente se utiliza el costo de compra (`pcio_com_siva`)**.
   * El precio de venta comercial no existe en los sistemas de origen ni se calcula.
   * El reporte de "Ganancias y Pérdidas" mide la **valorización financiera de Altas (entradas/sobrantes de inventario)** frente a las **Bajas (pérdidas/mermas de inventario)**.
2. **Código de Barras vs. Identificador (US 1 y US 2)**:
   * La relación exacta entre el código de barras escaneado y `id_articulo` queda **pendiente por definir/confirmar**.
   * El backend debe diseñarse de forma modular (capa de abstracción de búsqueda), utilizando de momento `id_articulo` como identificador clave, preparado para soportar una búsqueda directa por un campo de alias o tabla mapeadora si se requiere más adelante.
3. **Tasa de IVA Paramétrica**:
   * La tasa de IVA **no debe estar hardcodeada**. Debe recibirse como **parámetro configurable por transacción** (con un fallback predeterminado del 21% si no se especifica), ya que puede variar en el tiempo o por tipo de comprobante.
   * La familia "Medicamentos" se mantiene **siempre exenta (0% IVA)**.

---

## 3. Matriz de Faltantes en Backend por User Story

| User Story | Requerimiento Funcional | Estado Actual | Faltante en Backend |
| :--- | :--- | :--- | :--- |
| **US 1 & 2** | Escaneo de código de barras y registro manual de artículo. | Modelos ORM y Pydantic de `Articulo` definidos. | • Endpoint `GET /api/v1/articulos/scan/{code}` y `GET /api/v1/articulos/{id_articulo}`.<br>• Repositorio de consulta abstraído que devuelva los detalles del producto junto con su stock teórico y estado de auditoría en la sucursal/depósito activo. |
| **US 3 & 4** | Registrar cantidad en alta (sobrante) y en baja (faltante/pérdida). | Tabla `auditorias_registro` y `stock_por_deposito` en DB. | • Servicio de Dominio / Repositorio para procesar un registro de auditoría (`ALTA`, `BAJA`, `SIN_ACCION`).<br>• Cálculo de discrepancia ($\Delta = \text{Real} - \text{Teórico}$).<br>• **Motor Fiscal (`FiscalCalculator`)**: Cálculo de `monto_valorizado` a costo de compra (`pcio_com_siva`) aplicando IVA 0% a Medicamentos y la tasa de IVA parametrizada enviada en la transacción (o 21% por defecto).<br>• Endpoints `POST /api/v1/auditorias/registro` y `POST /api/v1/auditorias/sync` (batch offline). |
| **US 5** | Filtrar artículos (Nombre, Familia, Marca, Auditado S/N). | Modelos DB con relaciones entre `Articulo`, `Familia`, `Marca` y `StockPorDeposito`. | • Endpoint `GET /api/v1/articulos` con query params dinámicos: `q`, `id_familia`, `id_marca`, `fue_auditado` (boolean), `id_deposito` y paginación.<br>• Endpoints auxiliares: `GET /api/v1/familias` y `GET /api/v1/marcas`. |
| **US 6** | Consultar reportes estadísticos de ganancias y pérdidas. | Definición matemática en `docs/functional_specs.md`. | • Servicio de Analytics y Agregación Financiera.<br>• Endpoint `GET /api/v1/reportes/balance` que agregue totales de Altas ($), Bajas ($) y Balance Neto ($) valorizados estrictamente a costo de compra (`pcio_com_siva` + IVA parametrizado). |
| **Transversal** | Multi-Tenancy & Autenticación Real. | Multi-tenancy en modelos; auth dummy en `auth.py`. | • Repositorio y Servicio de Usuarios real conectando a tabla `usuarios`.<br>• Inyección automática de `tenant_id`, `id_sucursal` e `id_usuario` a través del token JWT en todas las consultas. |
| **Transversal** | Datos de Simulación (Seeding). | Sin script de carga masiva de prueba. | • Script `seed.py` para popular 500 artículos, depósitos, lotes con vencimiento y familias fiscales para validar las US y los protocolos de prueba. |

---

## 4. Hoja de Ruta por Etapas (Roadmap de Desarrollo Backend)

### Etapa 1: Autenticación Real, Contexto Multi-Tenant y Seeding
1. **UserRepository & AuthService**: Reemplazar la autenticación dummy en `api/v1/auth.py` conectando con la tabla `usuarios` (con hashing de contraseña seguro `passlib/bcrypt`).
2. **Dependencias de Contexto**: Extraer `tenant_id`, `id_usuario`, `rol` e `id_sucursal` del token JWT en todas las rutas.
3. **Script de Seeding (`scripts/seed.py`)**: Generación de 500 artículos, familias (incluyendo "Medicamentos"), marcas, depósitos, stock teórico/real y lotes con fechas de vencimiento según la sección 5 de `functional_specs.md`.

### Etapa 2: Módulo de Artículos, Búsqueda y Filtros (US 1, US 2 y US 5)
1. **ArticleRepository & ArticleService**:
   * Implementar `get_by_id_or_barcode(tenant_id, id_articulo, id_deposito)`.
   * Implementar `search_articles(tenant_id, id_deposito, query, id_familia, id_marca, fue_auditado, page, page_size)`.
2. **Endpoints REST de Artículos (`api/v1/articulos.py`)**:
   * `GET /api/v1/articulos/scan/{code}`: Respuesta optimizada para la app móvil en <1 segundo.
   * `GET /api/v1/articulos/{id_articulo}`: Consulta directa para registro manual.
   * `GET /api/v1/articulos`: Listado paginado con soporte de filtros dinámicos (US 5).
3. **Endpoints de Maestros (`api/v1/familias.py`, `api/v1/marcas.py`)**:
   * `GET /api/v1/familias` y `GET /api/v1/marcas` para poblar los selectores del frontend web/móvil.

### Etapa 3: Módulo de Movimientos, Registro de Auditoría y Motor Fiscal (US 3 y US 4)
1. **Motor Fiscal Parametrizado (`FiscalCalculator`)**:
   * Cálculo del costo unitario total a partir del costo de compra:
     $$\text{Total Unit Cost} = \begin{cases} \text{pcio\_com\_siva} & \text{si Familia = "Medicamentos"} \\ \text{pcio\_com\_siva} \times (1 + \text{Tasa\_IVA}) & \text{para otras familias} \end{cases}$$
   * `Tasa_IVA` es parametrizable por transacción (con fallback al 21% por defecto). Uso estricto de `decimal.Decimal`.
2. **AuditRepository & AuditService**:
   * Actualizar `StockPorDeposito` (`stock_real`, `fue_auditado = True`, `fecha_hora_auditacion`).
   * Registrar fila en `AuditoriaRegistro` (`tipo_accion`, `cantidad_afectada`, `monto_valorizado`).
3. **Endpoints de Movimientos (`api/v1/auditorias.py`)**:
   * `POST /api/v1/auditorias/registro`: Registro unitario en tiempo real.
   * `POST /api/v1/auditorias/sync`: Sincronización batch para cargas masivas/offline procesadas en la app móvil.

### Etapa 4: Módulo de Reportes Estadísticos y Analytics (US 6)
1. **Analytics Engine & ReportsRepository**:
   * Consulta agregada de `auditorias_registro` filtrado por `tenant_id`, `id_sucursal`, `id_deposito` y rango de fechas.
   * Cálculo de `total_inflow_cost` (Altas valorizadas), `total_loss_cost` (Bajas valorizadas) y `net_inventory_movement` ($).
   * Agregación por Familia, Marca y estado de auditoría (% auditado vs pendiente).
2. **Endpoints de Reportes (`api/v1/reportes.py`)**:
   * `GET /api/v1/reportes/balance`: Totales generales y balance financiero a costo de compra.
   * `GET /api/v1/reportes/discrepancias`: Detalle de artículos con mayores faltantes/sobrantes.
   * `GET /api/v1/reportes/vencimientos`: Reporte de alertas semafóricas FEFO (30, 60, 90 días).

---

## 5. Plan de Verificación y Pruebas de Calidad

* **Pruebas Automatizadas (`pytest`)**:
  * Test de motor fiscal parametrizado (verificando cálculo exacto con `decimal.Decimal` para Medicamentos al 0% e IVA configurable).
  * Test de aislamiento multi-tenant (Protocolo C).
  * Integration tests de endpoints REST con `httpx` async client.
* **Pruebas de Aceptación E2E**:
  * Ejecución de `scripts/seed.py` para cargar 500 artículos de prueba.
  * Verificación de reconciliación de balance financiero en reportes sin diferencias por redondeo flotante (Protocolo B).
