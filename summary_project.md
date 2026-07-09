# Documento de Transferencia de Conocimiento: Sistema de Control de Stock y Auditoría de Inventario

Este documento funciona como una Única Fuente de Verdad (SSoT) técnica y metodológica para transferir todo el contexto del proyecto al modelo Claude, garantizando la continuidad perfecta del ciclo de desarrollo sin pérdida de alineación arquitectónica.

---

## 1. Resumen ejecutivo del proyecto

* 
**Objetivo principal**: Desarrollar una solución integral multiplataforma (móvil y web) de Auditoría e Inteligencia de Inventario que optimice el control de stock en tiempo real mediante escaneo rápido de códigos de barra. Busca visibilizar de forma inmediata las pérdidas financieras por bajas de mercadería y automatizar los balances de costos e ingresos operativos.


* 
**Problema que resuelve**: Elimina la ineficiencia, el descuadre de inventario y la falta de trazabilidad económica de las mermas en entornos de depósitos complejos con baja iluminación. Mitiga los fallos operativos por desconexiones de red en zonas muertas del almacén y prepara la base técnica para escalar de una empresa única a un modelo de franquicia/red sin reescribir software.


* 
**Estado actual del proyecto**: Se ha completado el diseño de la arquitectura global y la especificación de datos de la Fase 1. A través de las herramientas agénticas, el programador DBA (`dba-agent`) completó la inicialización del ecosistema asincrónico de migraciones con Alembic y generó los modelos relacionales físicos en la capa de infraestructura.


* **Funcionalidades implementadas**:
* Estructura base del monorepo inicializada.


* Configuración completa del entorno asincrónico de Alembic en Python utilizando la librería `aiomysql`.


* Modelado declarativo ORM de las 8 tablas de la base de datos core alineadas estrictamente a los requerimientos impositivos y operativos.


* Validación automatizada de dependencias cruzadas y compilación exitosa de metadatos relacionales.




* **Funcionalidades pendientes**:
* Desarrollo del script paramétrico de datos inteligentes (`seed.py`) utilizando la librería `Faker` para simular 500 artículos, lotes vencidos e inyecciones de topología multi-tenant.


* Programación del interceptor central de autenticación y middleware de paso de datos lógicos (`tenant_auth.py`) en FastAPI.


* Codificación en memoria de las reglas de negocio core (motor fiscal de IVA condicional y ordenamiento predictivo FEFO) en la capa de servicios puros del dominio.


* Construcción de la lógica de persistencia móvil *Offline-First* con colas de sincronización por lotes.


* Maquetación de las interfaces móviles de alto contraste y los componentes analíticos web (gráficos Tremor).





---

## 2. Arquitectura y tecnologías

### Tecnologías por Capa

* 
**Lenguajes utilizados**: Python 3.11/3.12+ para todo el ecosistema de backend , TypeScript para el desarrollo unificado del cliente móvil y el portal web.


* 
**Frameworks y librerías backend**: FastAPI como núcleo asincrónico de alta velocidad de respuesta , Uvicorn como servidor de aplicaciones ASGI de nivel de producción , Pydantic V2 para validación estricta y contratos de tipado , PyJWT para la gestión segura de tokens de acceso , y `python-dotenv` para la inyección dinámica de variables de entorno.


* 
**Acceso a datos y versionado**: SQLAlchemy 2.0 (Declarative Mapping) operando mediante wrappers de ejecución asincrónica nativa (`AsyncSession`) impulsados por el driver `AIOMySQL`. Control de versiones de base de datos gestionado mediante Alembic.


* 
**Base de datos central**: MariaDB, seleccionada para garantizar paridad absoluta con la infraestructura física del cliente corporativo final.


* 
**Capa cliente móvil (Operaciones de campo)**: React Native + Expo utilizando NativeWind (Tailwind CSS) para la rápida composición de UI ergonómicas de alto contraste. Almacenamiento local embebido estructurado mediante WatermelonDB / SQLite local para soportar tolerancia total a fallos de Wi-Fi.


* 
**Capa cliente web (Portal gerencial y operativo)**: Next.js (React) implementado con la arquitectura moderna de App Router. Interfaz estilizada mediante Tailwind CSS y componentes analíticos corporativos listos para usar de la librería Tremor.



### Patrones de Arquitectura Aplicados

El proyecto implementa de manera estricta el patrón de **Arquitectura Hexagonal (Ports & Adapters)** para aislar por completo el corazón del negocio de los protocolos de transporte, drivers y herramientas web.

La persistencia evoluciona de manera progresiva: en la **Fase 1 (Global Medica)** opera sobre una única instancia centralizada aislando los datos lógicamente mediante filtros por `tenant_id` / `id_sucursal`. En la **Fase 2 (Farmanor)** escalará de manera transparente hacia una estrategia **Database-per-Tenant** mediante un conmutador (*switch*) dinámico en la factoría de conexiones de SQLAlchemy inyectado por el middleware de autenticación.

### Diagrama Textual de la Arquitectura

```
                        [ FRONTEND CLIENTS ]
             React Native (Mobile)  | Next.js (Web Dashboard)
                                    |
                               HTTP / JSON
                                    v
     ======================= [ BACKEND SERVICE ] =======================
     |                                                                 |
     |  [ API LAYER / PRIMARY ADAPTERS ]                               |
     |    └── api/main.py (FastAPI Routing & Uvicorn Engine)          |
     |    └── api/middlewares/tenant_auth.py (JWT Decoder & Context)   |
     |                                                                 |
     |         v (Inyección de Contexto / Inmutable ContextVars)       |
     |                                                                 |
     |  [ CORE DOMAIN LAYER (Pure Python) ]                            |
     |    ├── app/[modulo]/ports.py (Abstract Interface Contracts)     |
     |    ├── app/[modulo]/models.py (Pydantic V2 Schemas)             |
     |    └── app/[modulo]/services.py (IVA/FEFO Rules & Math Logic)   |
     |                                                                 |
     |         ^ (Dependency Injection Pattern)                        |
     |                                                                 |
     |  [ INFRASTRUCTURE LAYER / SECONDARY ADAPTERS ]                  |
     |    └── adapters/repositories/ (SQLAlchemy 2.0 Async Session)   |
     |                                                                 |
     ===================================================================
                                    |
                             Asynchronous SQL
                                    v
                        [ PERSISTENCE LAYER Core ]
                                 MariaDB

```

---

## 3. Estructura del proyecto

El proyecto está organizado de forma estricta bajo una estructura de **Monorepo** centralizado para garantizar sincronización absoluta de tipos de datos y simplificar los pipelines de simulación locales.

```
├── .antigravity/                   # Configuraciones de la plataforma de agentes
│   └── agents/                     # Prontuarios estrictos de contexto de IA
│       ├── dba.agent               # Perfil especializado en MariaDB y Alembic
│       └── core_backend.agent      # Perfil de Jules (Lógica Hexagonal y FastAPI)
├── .agents/skills/                 # Catálogo local de habilidades cargadas On-Demand
│   └── check-hexagonal/            # Habilidad personalizada de auditoría arquitectónica
├── docs/                           # Documentación de requerimientos y planos base
│   ├── architecture.md             # SSoT global de la arquitectura del software
│   └── functional_specs.md         # Especificaciones de negocio del sistema
├── antigravity.yaml                # Archivo central de orquestación y límites físicos
├── backend/                        # Código fuente del servicio del Backend (Python)
│   ├── alembic.ini                 # Configuración local de control de migraciones
│   ├── requirements.txt            # Manifiesto estricto de librerías del entorno
│   ├── .env / .env.example         # Variables y credenciales de entorno aisladas
│   ├── api/                        # Adaptadores Primarios (Transporte HTTP)
│   │   ├── main.py                 # Punto de entrada de la aplicación FastAPI
│   │   ├── v1/                     # Enrutadores divididos por versiones de API
│   │   └── middlewares/            # Interceptores de seguridad (tenant_auth.py)
│   ├── app/                        # Capa de Dominio Pura (Lógica de Negocio Core)
│   │   ├── [modulo]/               # Módulos segregados (articles, movements, users)
│   │   │   ├── models.py           # Esquemas de validación de datos (Pydantic V2)
│   │   │   ├── services.py         # Motores matemáticos y de cálculo puros
│   │   │   └── ports.py            # Interfaces abstractas o protocolos de salida
│   ├── adapters/                   # Adaptadores Secundarios (Infraestructura)
│   │   └── repositories/           # Implementación concreta de persistencia ORM
│   │       └── models.py           # Modelos de tablas relacionales de SQLAlchemy
│   ├── migrations/                 # Archivos de control de versiones de Alembic
│   │   ├── env.py                  # Script de entorno de ejecución asincrónica
│   │   └── versions/               # Scripts de migraciones (upgrade/downgrade)
│   └── scripts/                    # Utilidades de inicialización de entorno
│       └── seed.py                 # Fábrica de datos falsos inteligentes con Faker
├── frontend-mobile/                # Aplicación móvil de campo (React Native / Expo)
└── frontend-web/                   # Portal web gerencial y operativo (Next.js)

```

---

## 4. Modelo de datos

Para dar cumplimiento estricto a las directivas contables y ACID, todos los tipos financieros están tipados mediante formatos decimales fijos, eliminando imprecisiones de punto flotante en auditorías.

### 4.1 Catálogos y Datos Maestros

#### Tabla: `familias`

* 
*Propósito*: Define las agrupaciones de nivel superior de los productos, clave para evaluar de forma condicional la exención fiscal del IVA.


* *Campos*:
* 
`id_familia` (`INT`, Primary Key, Auto-Increment): Identificador único interno.


* 
`des_familia` (`VARCHAR(255)`, `NOT NULL`): Descripción o nombre comercial de la familia (ej. "Medicamentos").





#### Tabla: `grupos`

* 
*Propósito*: Subcategorías jerárquicas vinculadas aguas abajo con las familias.


* *Campos*:
* 
`id_familia` (`INT`, Primary Key, Foreign Key -> `familias.id_familia` con eliminación en `CASCADE`).


* 
`id_grupo` (`INT`, Primary Key): Identificador local del grupo bajo el alcance de la familia.


* 
`des_grupo` (`VARCHAR(255)`, `NOT NULL`): Descripción del grupo secundario.





#### Tabla: `marcas`

* 
*Propósito*: Catálogo maestro de laboratorios fabricantes.


* *Campos*:
* 
`id_marca` (`INT`, Primary Key, Auto-Increment).


* 
`des_marca` (`VARCHAR(255)`, `NOT NULL`): Nombre comercial del laboratorio.





#### Tabla: `articulos`

* *Propósito*: Maestro de productos. El identificador primario es alfanumérico para almacenar directamente la lectura directa de códigos de barra físicos.


* *Campos*:
* 
`id_articulo` (`VARCHAR(50)`, Primary Key): Código de barras (EAN-13, QR, etc.).


* 
`presentacion` (`VARCHAR(255)`, `NOT NULL`): Envase o empaque (ej. "Caja x 30 comprimidos").


* 
`des_articulo` (`VARCHAR(255)`, `NOT NULL`): Descripción del artículo.


* 
`id_marca` (`INT`, Foreign Key -> `marcas.id_marca` on delete `RESTRICT`).


* 
`id_familia` (`INT`, Foreign Key -> `familias.id_familia` on delete `RESTRICT`).


* 
`id_grupo` (`INT`, Foreign Key -> `grupos.id_grupo` on delete `RESTRICT`).


* 
`pcio_com_siva` (`DECIMAL(15, 4)`, `NOT NULL`): Costo base de adquisición sin impuestos.





#### Tabla: `usuarios`

* 
*Propósito*: Gestión de identidades y delimitación rígida de perfiles operativos mediante esquemas RBAC.


* *Campos*:
* 
`id_usuario` (`INT`, Primary Key, Auto-Increment).


* 
`nombre_completo` (`VARCHAR(255)`, `NOT NULL`).


* 
`email` (`VARCHAR(255)`, Unique, `NOT NULL`).


* 
`password_hash` (`VARCHAR(255)`, `NOT NULL`): Hash seguro (Argon2 / bcrypt).


* 
`rol` (`ENUM('administrador', 'supervisor', 'auditor')`, `NOT NULL`): Rol funcional del usuario.


* 
`id_sucursal` (`INT`, Foreign Key, `NULL`): Sucursal corporativa asignada. Nota: Para perfiles de administración global, este campo se define como `NULL` para permitir la conmutación cruzada entre tiendas.





### 4.2 Tablas Operativas y de Movimientos

#### Tabla: `stock_por_deposito`

* 
*Propósito*: Estado de inventario físico actual modificado continuamente por las acciones de auditoría en campo.


* *Campos*:
* 
`id_sucursal` (`INT`, Primary Key): Mapeo de la sucursal (clave multi-tenant lógica de Fase 1).


* 
`id_deposito` (`INT`, Primary Key): Identificador del sector de depósito.


* 
`id_articulo` (`VARCHAR(50)`, Primary Key, Foreign Key -> `articulos.id_articulo` on delete `RESTRICT`).


* 
`stock_real` (`INT`, `NOT NULL`, `DEFAULT 0`): Conteo físico real confirmado.


* 
`fue_auditado` (`BOOLEAN`, `NOT NULL`, `DEFAULT FALSE`): Flag de control de estado del turno.


* 
`fecha_hora_auditación` (`DATETIME`, `NULL`): Timestamp exacto de la última captura en estantería.





#### Tabla: `lotes_por_deposito`

* *Propósito*: Motor de trazabilidad de fechas de vencimiento de producción. Alimentación directa para el algoritmo FEFO.


* *Campos*:
* 
`id_deposito` (`INT`, Primary Key).


* 
`id_articulo` (`VARCHAR(50)`, Primary Key, Foreign Key -> `articulos.id_articulo` on delete `RESTRICT`).


* 
`lote` (`VARCHAR(50)`, Primary Key): Código alfanumérico de lote otorgado por el fabricante.


* 
`vencimiento` (`DATE`, `NOT NULL`): Fecha de caducidad (Campo indexado).


* 
`stock_real` (`INT`, `NOT NULL`, `DEFAULT 0`): Unidades físicas remanentes de este lote en particular.





#### Tabla: `auditorias_registro`

* 
*Propósito*: Libro de transacciones históricas e inmutables de auditoría (*Audit Trail*) para la confección de balances y reportes analíticos gerenciales.


* *Campos*:
* 
`id_auditoria` (`BIGINT`, Primary Key, Auto-Increment).


* 
`id_sucursal` (`INT`, `NOT NULL`, Index): Mapeo de aislamiento de sucursal.


* 
`id_deposito` (`INT`, `NOT NULL`).


* 
`id_articulo` (`VARCHAR(50)`, `NOT NULL`, Foreign Key -> `articulos.id_articulo` on delete `RESTRICT`).


* 
`tipo_accion` (`ENUM('ALTA', 'BAJA', 'SIN_ACCION')`, `NOT NULL`): Dirección exacta del ajuste físico.


* 
`cantidad_afectada` (`INT`, `NOT NULL`): Volumen neto de unidades alteradas.


* 
`monto_valorizado` (`DECIMAL(15, 4)`, `NOT NULL`): Consecuencia financiera calculada en memoria por el backend aplicando las reglas de exención del IVA.


* 
`id_usuario` (`INT`, Foreign Key -> `usuarios.id_usuario` on delete `RESTRICT`): Operario responsable del movimiento.


* 
`fecha_hora` (`DATETIME`, `DEFAULT CURRENT_TIMESTAMP`, Index).





---

## 5. Endpoints y contratos de API

Los contratos se procesan de forma asincrónica nativa. A nivel de seguridad global, todos los endpoints no públicos interceptan el token obligatoriamente para inyectar las claves del aislamiento multi-tenant.

### 5.1 GET `/health`

* 
**Propósito**: Verificación de estado operativa de la infraestructura (Healthcheck).


* 
**Método HTTP**: `GET` 


* 
**Autenticación**: Pública.


* **Response Ejemplo (200 OK)**:
```json
{
  "status": "healthy",
  "timestamp": "2026-07-09T13:30:00Z",
  "version": "1.0.0"
}

```



### 5.2 POST `/api/v1/auth/login`

* 
**Propósito**: Autenticación centralizada de usuarios emitiendo un token sin estado conteniendo los ganchos de control RBAC y Multi-tenant.


* 
**Método HTTP**: `POST` 


* **Request Body**:
```json
{
  "email": "auditor.central@globalmedica.com.ar",
  "password": "secure_password_string"
}

```


* **Response Ejemplo (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}

```


* **Estructura interna obligatoria del Payload descifrado (JWT)**:
```json
{
  "user_id": 142,
  "nombre": "Esteban Quito",
  "email": "auditor.central@globalmedica.com.ar",
  "role": "auditor",
  "tenant_id": 1,
  "id_sucursal": 10,
  "exp": 1783632000
}

```


* **Códigos de error relevantes**:
* `401 Unauthorized`: Credenciales de acceso incorrectas o expiradas.
* `422 Unprocessable Entity`: Errores de formato interceptados por los esquemas de validación de Pydantic V2.



---

## 6. Lógica de negocio clave

Claude debe comprender que estas tres reglas impositivas y de ordenamiento matemático constituyen el core del sistema y se calculan exclusivamente en memoria dentro de la capa `app/[modulo]/services.py`.

### 6.1 Motor Fiscal de IVA Condicional

Al procesar un movimiento de inventario, el servicio evalúa el artículo basándose en su metadata categórica de `id_familia` o `id_grupo`.

* 
**Regla**: Si el producto pertenece a la familia indexada como `"Medicamentos"`, su costo salta por completo la aplicación de tasas fiscales (Exento de IVA). Para cualquier otro tipo de producto (ej. perfumería, cosmética o accesorios), el motor aplica dinámicamente el multiplicador impositivo estandarizado de IVA sobre el precio base de costo (`pcio_com_siva`) antes de compilar el impacto en el histórico financiero.


* 
**Precisión**: Toda operación aritmética se ejecuta mediante la librería nativa de Python `decimal.Decimal`. **PROHIBIDO** el uso de tipos `float` para evitar pérdidas centesimales acumuladas.



### 6.2 Algoritmo de Priorización Expirativa FEFO

La lógica de visualización operativa y emisión de alertas del sistema no lee el stock de forma plana; implementa de forma estricta el principio **FEFO (First Expired, First Out)**.

* El servicio backend interroga la tabla `lotes_por_deposito`, ordenando de forma ascendente por el campo `vencimiento`.


* Los datos se segregan dinámicamente y se exponen en componentes semafóricos categorizados en ventanas temporales críticas e inquebrantables de **30 días** (Rojo / Crítico), **60 días** (Amarillo / Alerta media) y **90 días** (Verde / Advertencia preventiva).



### 6.3 Matriz Funcional de Restricción RBAC

El sistema opera bajo una estricta separación de responsabilidades a nivel de API y UI basada en el token JWT del usuario:

| Perfil / Rol | Alcance de Interfaz | Permisos Críticos de API | Restricciones Estrictas |
| --- | --- | --- | --- |
| <br>`administrador` 

 | Acceso ilimitado a todo el ecosistema (Web).

 | Gestión total, altas de usuarios, reportes financieros de ganancias y pérdidas.

 | Ninguna.

 |
| <br>`supervisor` 

 | Tablero Analítico Operativo y Módulos de Ajuste Web.

 | Monitoreo físico de conteos, visualización de alertas FEFO y resolución de discrepancias relacionales.

 | <br>**PROHIBIDO** leer campos financieros de costos (`pcio_com_siva`), dashboards de P&L o balances monetarios de pérdida.

 |
| <br>`auditor` 

 | Interfaz simplificada de Carga Rápida (Quick Web Audit / App Móvil).

 | Ejecución exclusiva de lecturas de código de barra y registro físico de conteos de unidades.

 | Bloqueado por completo de paneles analíticos, reportes gerenciales, datos monetarios o configuraciones de sistema.

 |

---

## 7. Problemas encontrados y soluciones

A lo largo de las sesiones de arquitectura previas con Antigravity CLI, se detectaron desviaciones críticas del comportamiento automatizado por defecto. Claude debe conocer estos errores históricos para no reintroducirlos:

* 
**Error de Stack en Base de Datos (PostgreSQL vs MariaDB)**: El generador automático inicial configuró al agente bajo el chip genérico de PostgreSQL e intentó forzar configuraciones de políticas nativas de seguridad RLS (Row-Level Security).


* 
*Causa Raíz*: Pérdida transitoria de contexto en el modelo fundacional al procesar prompts genéricos.


* 
*Solución Aplicada*: Se reescribió el prontuario del agente delimitando de forma milimétrica el stack tecnológico (MariaDB) e indicando que el multi-tenancy se resuelve mediante lógica de filtrado de queries por repositorio (`id_sucursal`) en la Fase 1 y mediante bases de datos físicas independientes en la Fase 2.




* 
**Formato de Migraciones Incorrecto (SQL Crudo vs Alembic)**: El sistema solicitaba inicialmente scripts UP/DOWN en sintaxis SQL nativa.


* 
*Causa Raíz*: Restricción de salida mal planteada en las directivas de formato del prompt.


* 
*Solución Aplicada*: Se forzó al agente a emitir únicamente archivos Python estructurados compatibles con Alembic conteniendo las funciones explícitas `upgrade()` y `downgrade()`.




* 
**Enclaustramiento de Directorios de Operación**: El agente DBA tenía prohibido escribir código fuera de `backend/migrations/`, bloqueándolo de generar el script de simulación `seed.py` el cual debe vivir en `backend/scripts/`.


* 
*Causa Raíz*: Restricciones de seguridad excesivamente restrictivas (*Over-sandboxing*).


* 
*Solución Aplicada*: Se expandieron las fronteras operativas explícitas de los archivos `.agent` permitiendo al DBA operar en `scripts/` y a Jules operar sobre `backend/adapters/repositories/`.




* 
**Contaminación de la Raíz del Repositorio (`alembic.ini`)**: El archivo de configuración de Alembic fue creado suelto en la raíz del monorepo.


* *Causa Raíz*: Inicialización por defecto de la CLI de Alembic sin especificar rutas relativas.
* 
*Solución Aplicada*: Se reubicó de inmediato adentro de `backend/`, ajustando el archivo `env.py` para mapear de forma relativa y coherente la inyección dinámica del archivo `.env` local de esa misma carpeta.





---

## 8. Configuración y despliegue

### Esquema de Variables de Entorno Obligatorio (`backend/.env`)

```bash
# Servidor y Entorno General
ENVIRONMENT=staging
DEBUG=True
SECRET_KEY=c3VwZXJfc2VjcmV0X2tleV9mb3Jfand0X2VuY3J5cHRpb25fMjAyNg==

# Conexión Asincrónica Core a MariaDB Local (Fase 1 - Global Medica)
DATABASE_URL=mysql+aiomysql://db_user:db_password@localhost:3306/global_medica_sim

```

### Arquitectura de Producción y Disponibilidad 24/7

Para dar cumplimiento estricto a las métricas de rendimiento y asegurar que el sistema sobreviva a picos concurrentes al cierre de cada turno de depósito, queda estrictamente prohibido exponer el servidor de aplicaciones Uvicorn directamente a Internet.

1. 
**Nginx**: Actúa como proxy inverso de entrada y escudo de seguridad frontal. Maneja el cifrado SSL (HTTPS) y mitiga ataques de red.


2. 
**Gunicorn**: Administra el ciclo de vida del proceso en el servidor Linux corporativo. Orquesta múltiples workers asincrónicos corriendo por debajo instancias optimizadas de Uvicorn. Si un hilo se cuelga ante una consulta masiva, Gunicorn lo destruye y levanta otro en milisegundos sin interrumpir los escaneos de las terminales móviles de campo.



---

## 9. Decisiones técnicas importantes

* 
**Elección de un Monorepo centralizado**: Se descartó la estrategia Polyrepo (separar backend, web y móvil en 3 repositorios diferentes). El monorepo garantiza que los equipos junior compartan tipados, prueben de forma local con un solo clon de Git y suban cambios atómicos del backend y de los clientes en un único Pull Request.


* 
**Uso obligatorio de FastAPI + SQLAlchemy Asincrónico**: Garantiza que el servidor mantenga tiempos de respuesta mínimos (meta de escaneo < 1 segundo), liberando el bucle de eventos mediante procesos asincrónicos reales con `aiomysql` para no bloquear hilos al consultar grandes catálogos relacionales.


* 
**Adopción del modelo SaaS / Licenciamiento por Sucursal para Fase 2**: Evaluado frente a la venta tradicional de código llave en mano. Esta decisión retiene la propiedad intelectual del software en manos del equipo de ingeniería, cobrando un monto fijo de configuración inicial ($1,500 USD) para financiar la automatización del pipeline Multi-tenant y una suscripción mensual recurrente digerible por sucursal ($40 - $60 USD/mes), logrando ingresos pasivos escalables a largo plazo.



---

## 10. Próximos pasos recomendados

Para avanzar de forma fluida con el backlog del proyecto, Claude debe tomar las siguientes tareas respetando el orden secuencial de dependencias de código:

1. 
**Generación de la Fábrica de Datos (`seed.py`) - [Prioridad ALTA]**: Invocar las librerías de `Faker` desde `backend/scripts/` para poblar el esquema MariaDB local recién creado. Debe inyectar de forma balanceada 500 artículos simulando topologías de sucursales distintas, incluyendo de forma intencional un alto porcentaje de lotes ya vencidos y discrepancias físicas de stock para estresar los reportes de prueba.


2. 
**Implementación del Middleware de Autenticación (`tenant_auth.py`) - [Prioridad ALTA]**: Programar el interceptor central en FastAPI que decodifique las firmas de los tokens JWT mediante `pyjwt`. Debe verificar los roles RBAC e inyectar el identificador del inquilino de forma inmutable en el contexto de ejecución de la consulta asincrónica de base de datos.


3. 
**Codificación de Reglas del Negocio Core en el Dominio - [Prioridad MEDIA]**: Escribir los servicios puros en Python dentro de `app/` encargados de la discriminación contable condicional del IVA (exención de medicamentos) y el cálculo matemático de las mermas financieras operativas.


4. 
**Inicialización de los Proyectos Frontend - [Prioridad BAJA]**: Desplegar los boilerplate base estructurados en TypeScript para `frontend-mobile/` (Expo con soporte nativo de cámara para lectura ultrarrápida de barras) y `frontend-web/` (Next.js con las plantillas analíticas de Tremor).



---

## Resumen crítico para continuar el proyecto

> **¡ATENCIÓN CLAUDE! Lea estas directivas obligatorias antes de responder tu primer mensaje o generar cualquier línea de código en este repositorio:**
> 1. **Stack Técnico Inquebrantable**: El backend corre en **Python con FastAPI e instancias asincrónicas de SQLAlchemy 2.0 + AIOMySQL**. El motor de base de datos es **MariaDB**. Queda terminantemente prohibido reintroducir código de PostgreSQL o triggers SQL nativos.
> 2. **Límites de la Arquitectura Hexagonal**: La lógica de negocio (`backend/app/`) debe mantenerse 100% pura y abstracta. Ningún archivo del dominio puede importar paquetes de bases de datos (SQLAlchemy/Alembic) ni utilidades HTTP de FastAPI. Toda comunicación con el exterior se define mediante contratos abstractos de interfaces (**Ports**) en el dominio e implementaciones concretas en la capa de **Adapters**.
> 3. **Formato de Migraciones**: Cualquier ajuste estructural al modelo relacional de datos debe traducirse exclusivamente en **scripts de migración de Python controlados por Alembic**. Cada script generado debe contar obligatoriamente con una función de reversión funcional `downgrade()` para permitir rollbacks limpios en entornos locales de desarrollo.
> 4. **Precisión Financiera**: Está rotundamente prohibido usar el tipo de dato nativo `float` para precios, mermas o cálculos impositivos de IVA. Toda la matemática del negocio debe implementarse utilizando la librería estándar **`decimal.Decimal`** para garantizar precisión contable absoluta al centavo.
> 5. **Protocolo de Seguridad RBAC**: No expongas datos financieros planos de costos (`pcio_com_siva`) de forma pública en la API. Los endpoints analíticos monetarios deben validar en el backend que el rol descifrado del JWT sea estrictamente `'administrador'`, rechazando de inmediato las peticiones si el token pertenece a perfiles de `'supervisor'` o `'auditor'`.
> 
>