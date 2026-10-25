import asyncio
import os
import sys
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Ensure the root of the project is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

# Load env variables
load_dotenv()

# Import models metadata
from backend.adapters.repositories.models import BaseArticles, BaseUsers, BaseAnalytics
from backend.migrations.url_config import (
    alembic_engine_kwargs,
    escape_for_configparser,
    resolve_alembic_url,
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Determine the target database to migrate
db_target = os.getenv("DB_TARGET")
if not db_target:
    if config.config_file_name and "analytics" in config.config_file_name:
        db_target = "analytics"
    elif config.config_file_name and "users" in config.config_file_name:
        db_target = "users"
    else:
        db_target = "articles"

if db_target == "users":
    target_metadata = BaseUsers.metadata
elif db_target == "analytics":
    target_metadata = BaseAnalytics.metadata
else:
    target_metadata = BaseArticles.metadata

# Update version_locations dynamically
versions_folder = "versions" if db_target == "articles" else f"versions_{db_target}"
version_locations_path = os.path.abspath(os.path.join(os.path.dirname(__file__), versions_folder))
# Use raw config setter for multple locations if needed, or set main option
config.set_main_option("version_locations", version_locations_path)

database_url = resolve_alembic_url(db_target)

config.set_main_option("sqlalchemy.url", escape_for_configparser(database_url))

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        **alembic_engine_kwargs(database_url),
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
