"""Pure helpers for Alembic's env.py, kept import-safe (no Alembic context needed)."""

from backend.adapters.database.connection import (
    build_ssl_connect_args,
    resolve_database_url,
)
from sqlalchemy.engine import make_url


def resolve_alembic_url(target: str) -> str:
    """Same URL precedence as the application connection provider."""
    return resolve_database_url(target)


def escape_for_configparser(url: str) -> str:
    """Alembic stores options in a ConfigParser, where a bare '%' starts an interpolation."""
    return url.replace("%", "%%")


def alembic_engine_kwargs(url: str) -> dict:
    """Extra ``async_engine_from_config`` kwargs: TLS args for MySQL drivers only."""
    if make_url(url).get_backend_name() == "sqlite":
        return {}
    connect_args = build_ssl_connect_args()
    return {"connect_args": connect_args} if connect_args else {}
