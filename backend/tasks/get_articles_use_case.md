# Especificación Técnica: Estado de Auditoría por Artículo

**Proyecto:** SAASSTOCKDEPOSITCONTROL (Global Medica / Farmanor)
**Fase:** Phase 1 — Single-tenant
**Arquitectura:** Hexagonal (Ports & Adapters)
**Agentes involucrados:** `core-backend-agent` (Jules) — owner principal · `dba-agent` — soporte en modelos/migraciones

---

## 1. Contexto de negocio

El sistema opera sobre **tres bases de datos físicamente independientes**:

| Base de datos | Propietario | Acceso | Contenido |
|---|---|---|---|
| `db_articulos` | Cliente (externa) | **Solo lectura** | Catálogo de artículos por depósito |
| `db_usuarios` | Sistema | Lectura/Escritura | Usuarios y roles (Administrador, Supervisor, Auditor) |
| `db_auditorias` | Sistema | Lectura/Escritura | Registros de auditorías realizadas por artículo (código de barra) |

**Regla de negocio a implementar:** al listar artículos de `db_articulos`, cada fila debe incluir una columna derivada `auditado` con valor `"Si"` o `"No"`, calculada verificando si existe al menos un registro en `db_auditorias` cuyo `codigo_barra` coincida con el del artículo.

**Restricción crítica:** `db_articulos` es propiedad del cliente y de solo lectura. Ningún adapter puede asumir que ambas bases comparten motor, servidor o transacción. **Está prohibido resolver esto con un JOIN cruzado entre bases de datos.**

---

## 2. Principio arquitectónico rector

> La composición de datos que provienen de **puertos distintos** ocurre **exclusivamente en la capa de aplicación** (use case / application service), nunca dentro de un repositorio, nunca dentro de un endpoint, nunca vía SQL cruzado.

Cada repositorio conoce **una sola base de datos**. El use case es el único componente autorizado a invocar más de un repositorio y fusionar sus resultados.

```
┌─────────────────────────────────────────────────────────┐
│                    Application Layer                     │
│         ListarArticulosConEstadoAuditoriaUseCase          │
│                                                            │
│   1. Pide artículos → ArticuloRepositoryPort               │
│   2. Extrae codigos_barra de esos artículos                │
│   3. Pide estado auditado → AuditoriaRepositoryPort         │
│   4. Fusiona en memoria → ArticuloConEstadoDTO[]            │
└───────────────┬─────────────────────────┬─────────────────┘
                │                         │
     ┌──────────▼──────────┐   ┌──────────▼──────────┐
     │ ArticuloRepository   │   │ AuditoriaRepository   │
     │ (adapter: db_articulos)│   │ (adapter: db_auditorias)│
     │ SOLO LECTURA           │   │ LECTURA/ESCRITURA       │
     └───────────────────────┘   └────────────────────────┘
```

---

## 3. Contratos de puertos (interfaces)

### 3.1 `ArticuloRepositoryPort` (ya existente — no se modifica su contrato de lectura)

```python
class ArticuloRepositoryPort(Protocol):
    async def get_articulos(
        self, filtros: ArticuloFiltros, page: int, page_size: int
    ) -> list[Articulo]:
        """Devuelve artículos paginados desde db_articulos. Solo lectura."""
```

No debe ganar ningún método relacionado a auditorías. Este repositorio **no sabe que las auditorías existen**.

### 3.2 `AuditoriaRepositoryPort` (método nuevo a agregar)

```python
class AuditoriaRepositoryPort(Protocol):
    async def get_codigos_auditados(self, codigos_barra: list[str]) -> set[str]:
        """
        Dado un lote de códigos de barra, devuelve el subconjunto que
        POSEE al menos un registro de auditoría en db_auditorias.
        Debe resolverse con UNA sola consulta (SELECT ... WHERE codigo_barra IN (...)),
        nunca con una consulta por artículo (evitar N+1).
        """
```

Este repositorio **no sabe qué es un artículo del catálogo**, solo conoce `codigo_barra` como valor de dato.

---

## 4. Caso de uso (application layer)

**Ubicación:** `backend/app/application/use_cases/listar_articulos_con_estado_auditoria.py`

**Responsabilidad exclusiva de esta capa:**
1. Recibe filtros + paginación.
2. Llama a `ArticuloRepositoryPort.get_articulos(...)`.
3. Extrae la lista de `codigo_barra` de los artículos obtenidos (solo del lote/página actual, no de todo el catálogo).
4. Llama a `AuditoriaRepositoryPort.get_codigos_auditados(codigos_barra)`.
5. Construye el DTO de salida fusionando ambos resultados en memoria (no en SQL).
6. Devuelve `list[ArticuloConEstadoDTO]`.

```python
class ListarArticulosConEstadoAuditoriaUseCase:
    def __init__(
        self,
        articulo_repo: ArticuloRepositoryPort,
        auditoria_repo: AuditoriaRepositoryPort,
    ):
        self._articulo_repo = articulo_repo
        self._auditoria_repo = auditoria_repo

    async def ejecutar(
        self, filtros: ArticuloFiltros, page: int, page_size: int
    ) -> list[ArticuloConEstadoDTO]:
        articulos = await self._articulo_repo.get_articulos(filtros, page, page_size)

        codigos_barra = [a.codigo_barra for a in articulos]
        codigos_auditados = await self._auditoria_repo.get_codigos_auditados(
            codigos_barra
        )

        return [
            ArticuloConEstadoDTO(
                **articulo.model_dump(),
                auditado="Si" if articulo.codigo_barra in codigos_auditados else "No",
            )
            for articulo in articulos
        ]
```

**Prohibido en esta capa:** acceder directamente a `session`/engine de SQLAlchemy. Solo debe hablar con los puertos (interfaces), nunca con los adapters concretos.

---

## 5. DTO de salida

**Ubicación:** `backend/app/application/dtos/articulo_con_estado_dto.py`

```python
class ArticuloConEstadoDTO(BaseModel):
    codigo_barra: str
    descripcion: str
    # ...resto de campos existentes del Articulo...
    auditado: Literal["Si", "No"]
```

**Nota RBAC:** si en el futuro el estado de auditoría se enriquece con detalle (fecha, usuario auditor), ese detalle debe respetar el mismo patrón de **schema por rol** ya establecido para `pcio_com_siva` — no exponer campos sensibles vía condicionales, sino vía un DTO separado para roles autorizados.

---

## 6. Adapter de auditorías — implementación concreta

**Ubicación:** `backend/app/infrastructure/repositories/auditoria_repository.py`
**Owner:** `core-backend-agent` (Jules) — implementación del repositorio de aplicación
**Owner del modelo/migración:** `dba-agent` — `models.py` y migración de la tabla `auditorias`

```python
class SQLAlchemyAuditoriaRepository(AuditoriaRepositoryPort):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_codigos_auditados(self, codigos_barra: list[str]) -> set[str]:
        if not codigos_barra:
            return set()

        stmt = (
            select(AuditoriaModel.codigo_barra)
            .where(AuditoriaModel.codigo_barra.in_(codigos_barra))
            .distinct()
        )
        result = await self._session.execute(stmt)
        return {row[0] for row in result.all()}
```

---

## 7. Requisitos de modelo/migración (a cargo de `dba-agent`)

- Tabla `auditorias` debe tener **índice** sobre `codigo_barra` (es el campo de búsqueda de este flujo y probablemente de otros).
- `codigo_barra`: mismo tipo/longitud que en `db_articulos` para evitar mismatches de comparación.
- `dba-agent` debe entregar el comando manual de migración (Alembic) — no ejecuta nada directamente, según su restricción de "no execution capability".
- Este trabajo **no debe bloquearse** por la decisión pendiente de si "Auditado" es tabla propia o campos embebidos en Stock-per-deposit — el contrato `get_codigos_auditados(codigos_barra) -> set[str]` es independiente de esa decisión interna del modelo; solo cambia el `SELECT` interno del adapter si se resuelve distinto.

---

## 8. Endpoint (interface layer)

**Ubicación:** `backend/app/interfaces/api/articulos_router.py`

Responsabilidad: recibir el request HTTP, resolver dependencias (inyección de ambos repos vía DI), invocar el use case, devolver el DTO. **No contiene lógica de negocio ni de merge.**

```python
@router.get("/articulos", response_model=list[ArticuloConEstadoDTO])
async def listar_articulos(
    filtros: ArticuloFiltros = Depends(),
    page: int = 1,
    page_size: int = 50,
    use_case: ListarArticulosConEstadoAuditoriaUseCase = Depends(
        get_listar_articulos_use_case
    ),
):
    return await use_case.ejecutar(filtros, page, page_size)
```

---

## 9. Reglas no negociables (checklist de validación)

- [ ] **Ningún JOIN cruzado entre bases.** La fusión ocurre solo en el use case, en memoria.
- [ ] `ArticuloRepositoryPort` permanece **de solo lectura** y sin conocimiento de auditorías.
- [ ] `get_codigos_auditados` resuelve con **una sola query `IN`** — no N+1 (una consulta por artículo está prohibido).
- [ ] El use case no importa `sqlalchemy` ni ningún símbolo de infraestructura — solo los ports (interfaces).
- [ ] El campo `auditado` es `Literal["Si", "No"]`, nunca booleano libre ni string arbitrario.
- [ ] Ningún campo sensible tipo `pcio_com_siva` se filtra a través de este flujo — el DTO de salida se valida contra el schema del rol correspondiente.
- [ ] `dba-agent` entrega migración manual (no la ejecuta), con índice en `codigo_barra`.
- [ ] Gate final: correr skill `check-hexagonal` antes de dar la tarea por finalizada (Jules y DBA).

---

## 10. Fuera de alcance (release actual)

- Almacenamiento y consulta de **reportes** de auditoría (queda para otro release, según lo ya definido).
- Detalle expandido de la auditoría (fecha, usuario, resultado) en el listado de artículos — solo el flag `auditado`.
- Cualquier filtrado por `tenant_id` — Phase 1 es single-tenant; los hooks de Phase 2 permanecen comentados/sin activar.

---

## 11. Resumen de responsabilidades por archivo

| Archivo | Capa | Owner |
|---|---|---|
| `application/ports/articulo_repository_port.py` | Puerto | Jules |
| `application/ports/auditoria_repository_port.py` | Puerto | Jules |
| `application/use_cases/listar_articulos_con_estado_auditoria.py` | Aplicación | Jules |
| `application/dtos/articulo_con_estado_dto.py` | Aplicación | Jules |
| `infrastructure/repositories/articulo_repository.py` | Adapter (solo lectura) | Jules |
| `infrastructure/repositories/auditoria_repository.py` | Adapter | Jules |
| `infrastructure/models.py` (tabla `auditorias`, índice) | Modelo/Migración | dba-agent |
| `interfaces/api/articulos_router.py` | Endpoint | Jules |