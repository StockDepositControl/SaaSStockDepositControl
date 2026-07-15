# 💾 Capa de Adaptadores Secundarios (`backend/adapters/`)

Esta capa representa los **Adaptadores Secundarios (Driven Adapters)** de la aplicación, encargados de la comunicación con el exterior (bases de datos, clientes HTTP para APIs externas, colas de mensajes, etc.).

## 📁 Contenido de esta Capa

1. **Repositorios (`adapters/repositories/`)**: Implementaciones concretas de los puertos (interfaces) declarados en el dominio (`app/[modulo]/ports.py`). Utilizan SQLAlchemy 2.0 Async para interactuar con MariaDB.
2. **Modelos de Base de Datos (`adapters/repositories/models.py`)**: Definiciones de tablas y mapeos declarativos ORM de SQLAlchemy.
3. **Configuración de Conexiones**: Lógica para resolver dinámicamente las conexiones por inquilino (Multi-Tenancy) y gestionar las sesiones (`AsyncSession`).

---

## 🛑 Reglas y Prohibiciones Estrictas

- **Alineación con Puertos**: Cada repositorio concreto debe implementar estrictamente el contrato (Port) definido en el dominio. No debe exponer métodos públicos adicionales que no formen parte de la interfaz abstracta del puerto.
- **Sin Lógica de Negocio**: Los repositorios solo leen, persisten y estructuran datos. No validan reglas de negocio (ej. excepciones de IVA o semáforos de vencimiento).
- **Límites de Propiedad (Ownership)**:
  - **Jules (Core Backend)**: Desarrolla y edita los repositorios concretos (`*_repository.py`).
  - **DBA Specialist**: Posee y gestiona el archivo `models.py` y las migraciones de Alembic. **Jules no debe modificar `models.py` directamente**.
- **Aislamiento Multi-Inquilino (Multi-Tenancy)**: Todos los repositorios deben appendear automáticamente el filtro de `tenant_id` y `id_sucursal` en las consultas de lectura y mutación para evitar fuga de datos entre inquilinos.
