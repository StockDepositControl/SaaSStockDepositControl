# 🌌 Domain and Application Layer (`backend/app/`)

This folder contains the core business logic and application layer for the platform. It follows the Hexagonal Architecture pattern and keeps the domain isolated from HTTP and SQL infrastructure concerns.

## Golden rule: pure domain isolation

The domain layer must avoid importing infrastructure libraries such as:

- FastAPI / Starlette
- SQLAlchemy / Alembic
- database drivers
- external HTTP clients

The domain should depend only on the Python standard library and Pydantic V2 models.

---

## Internal module structure

Functional modules under `app/` are organized around the following pattern:

```text
backend/app/[module]/
├── __init__.py
├── models.py
├── ports.py
├── services.py
```

### 1. Domain models (`models.py`)

This file contains the pure validation and business data models.

- `[Entity]Base`: common fields
- `[Entity]Create`: creation schema
- `[Entity]Update`: update schema
- `[Entity]`: complete domain model

These models are intentionally framework-independent and use `ConfigDict(from_attributes=True)` where necessary for adaptation from ORM objects.

### 2. Ports (`ports.py`)

This file defines the abstract contracts used by the domain layer.

Example pattern:

```python
from abc import ABC, abstractmethod
from typing import Optional

class UserRepositoryPort(ABC):
    @abstractmethod
    async def get_by_email(self, email: str, tenant_id: Optional[int] = None):
        pass
```

The purpose is to declare required persistence or dependency behavior without coupling the domain to a concrete implementation.

### 3. Services (`services.py`)

This file implements business logic for each domain module.

Examples from the current codebase include:

- VAT classification and financial loss calculation
- stock delta logic
- audit session lifecycle behavior
- reporting aggregations and summaries

These services receive their dependencies through constructor injection using the port abstractions.

---

## Current modules in the domain layer

- `articles/`
- `branches/`
- `enterprises/`
- `movements/`
- `reports/`
- `users/`
- `work_sessions/`
- `ports/`

This structure matches the actual backend implementation and is the basis for the API and repository wiring.
