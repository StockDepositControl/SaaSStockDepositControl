# 🌌 Capa de Dominio y Aplicación (`backend/app/`)

Este directorio contiene el núcleo del negocio (Core Domain) y la lógica de aplicación del sistema. Está diseñado siguiendo los principios de la **Arquitectura Hexagonal (Ports & Adapters)**.

## 🛑 Regla de Oro: Aislamiento Puro del Dominio

**Está estrictamente prohibido importar frameworks, ORMs o herramientas de infraestructura** dentro de esta carpeta. 

Esto incluye, pero no se limita a:
- **FastAPI / Starlette / HTTP Utilities**: La lógica de negocio no debe saber cómo se expone (HTTP, gRPC, CLI, etc.).
- **SQLAlchemy / Alembic / Drivers de Base de Datos**: El dominio maneja datos en memoria y abstracciones, no persistencia física ni transacciones de base de datos.
- **Bibliotecas de Terceros de Infraestructura**: Todo lo relacionado con el mundo exterior debe interactuar a través de interfaces (**Ports**).

El dominio debe depender únicamente de la biblioteca estándar de Python y de **Pydantic V2** para la definición y validación de tipos de datos puros.

---

## 📁 Estructura Interna de Módulos

Cada módulo funcional dentro de `app/` (por ejemplo, `users`, `movements`, `articles`) debe organizarse de la siguiente manera:

```text
backend/app/[modulo]/
├── __init__.py
├── models.py       # Modelos de Dominio y Schemas de Validación (Pydantic V2)
├── ports.py        # Interfaces y Contratos Abstractos (Ports)
└── services.py     # Servicios puros con la lógica de negocio y casos de uso
```

### 1. Modelos de Dominio (`models.py`)
Contiene los modelos de datos puros utilizando **Pydantic V2**. Aquí se definen los esquemas de validación de datos que entran y salen del dominio.
- **Tipos comunes**:
  - `[Entity]Base`: Atributos comunes de la entidad.
  - `[Entity]Create`: Esquema para la creación.
  - `[Entity]Update`: Esquema para actualizaciones parciales.
  - `[Entity]`: Modelo completo representando la entidad del dominio, configurado con `ConfigDict(from_attributes=True)` para permitir la conversión desde objetos ORM en los adaptadores.
- **Regla**: No deben contener decoradores de base de datos ni metadatos de persistencia.

### 2. Puertos (`ports.py`)
Define las interfaces abstractas (contratos) utilizando `abc.ABC` and `abc.abstractmethod`. 
- **Propósito**: Declarar qué operaciones de persistencia o comunicación externa necesita el dominio sin especificar cómo se implementan.
- **Ejemplo**:
  ```python
  from abc import ABC, abstractmethod
  from typing import List, Optional
  from app.users.models import User, UserCreate

  class UserRepositoryPort(ABC):
      @abstractmethod
      async def get_by_id(self, id_usuario: int) -> Optional[User]:
          pass

      @abstractmethod
      async def get_by_email(self, email: str) -> Optional[User]:
          pass

      @abstractmethod
      async def create(self, user: UserCreate) -> User:
          pass
  ```

### 3. Servicios de Aplicación (`services.py`)
Contiene la lógica de negocio pura, cálculos y casos de uso que orquestan el flujo de datos.
- **Regla**: Dependen exclusivamente de las abstracciones definidas en `ports.py` y de los modelos en `models.py`.
- **Inyección de Dependencias**: Los servicios deben recibir sus dependencias (como repositorios) a través del constructor utilizando los puertos como anotaciones de tipo.
- **Ejemplos de Lógica**: Cálculo fiscal condicional de IVA, ordenamiento FEFO de lotes, validación de reglas de negocio para auditorías.
