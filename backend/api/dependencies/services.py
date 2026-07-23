"""
Service Dependency Injection — Multi-DB Repository Wiring

This module is the central point where concrete repositories are instantiated
with their respective database session factories and injected into domain
Service constructors.

Architecture contract (from docs/ARCHITECTURE.md §4.3):
  - article_repository  → main_db    → ArticleRepositoryPort
  - movement_repository → main_db    → StockRepositoryPort
  - user_repository     → users_db   → UserRepositoryPort
  - report_repository   → reports_db → AuditLedgerRepositoryPort

Each provider function below will follow this pattern:
  1. Obtain the correct async_sessionmaker from connection.py (main/users/reports)
  2. Instantiate the concrete repository with that session factory
  3. Instantiate the domain Service with the repository (typed against the Port)
  4. Return the Service for FastAPI Depends() injection

Implementation is deferred until concrete repositories and domain services exist.
"""
