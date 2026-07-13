# 🔌 Capa de Interfaz y Adaptadores Primarios (`backend/api/`)

Esta capa representa los **Adaptadores Primarios (Driving Adapters)** de la aplicación. Su función principal es interactuar con los clientes externos, exponer los puntos de acceso HTTP (API REST) y gestionar el ciclo de vida de las solicitudes.

## 📁 Contenido de esta Capa

1. **Controladores y Enrutadores (`api/main.py`, `api/v1/`...)**: Rutas de FastAPI organizadas por recursos o módulos.
2. **Middlewares (`api/middlewares/`)**: Interceptores de peticiones, como la autenticación JWT multi-tenant (`tenant_auth.py`).
3. **Dependencias (`api/dependencies.py` u homólogos)**: Lógica de inyección de dependencias para proveer repositorios y servicios con sus respectivos scopes.
4. **Esquemas de Entrada/Salida (Pydantic)**: Modelos de serialización de peticiones y respuestas HTTP.

---

## 🛑 Prohibiciones Estrictas (Lo que NO debe ir aquí)

- **Lógica de Negocio / Reglas de Cálculo**: Los routers y controladores de la API deben actuar únicamente como coordinadores. No deben realizar cálculos de negocio (como el cálculo de IVA o filtros FEFO). Toda la lógica debe residir en `app/services.py`.
- **Consultas a Base de Datos (SQL / SQLAlchemy)**: Está estrictamente prohibido instanciar o usar sesiones de base de datos directamente para ejecutar consultas en los routers. Toda persistencia debe delegarse a los repositorios inyectados (`adapters/repositories/`).
- **Uso directo de Entidades de Base de Datos**: Los routers nunca deben retornar modelos declarativos de SQLAlchemy directamente al cliente. Todo objeto de respuesta debe ser serializado a través de esquemas de Pydantic V2 específicos.
- **Exposición de Datos Financieros Sensibles**: Bajo ninguna circunstancia se debe retornar el costo de compra (`pcio_com_siva`) a roles sin privilegios (`supervisor`, `auditor`). La API debe usar esquemas de salida separados estructuralmente según el rol del JWT.
