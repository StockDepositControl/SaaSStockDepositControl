import ssl

import pytest
from alembic.config import Config
from backend.adapters.database.connection import DatabaseConfigError
from backend.migrations.url_config import (
    alembic_engine_kwargs,
    escape_for_configparser,
    resolve_alembic_url,
)

pytestmark = pytest.mark.usefixtures("clean_db_env")

MYSQL_URL = "mysql+aiomysql://u:p@db:3306/db_articles"
SQLITE_URL = "sqlite+aiosqlite:///tmp/test.db"


class TestPercentEscaping:
    def test_percent_is_doubled(self):
        assert (
            escape_for_configparser("mysql://u:p%40ss@h/db") == "mysql://u:p%%40ss@h/db"
        )

    def test_url_without_percent_is_unchanged(self):
        assert escape_for_configparser(MYSQL_URL) == MYSQL_URL

    def test_escaped_url_round_trips_through_alembic_config(self):
        raw = "mysql+aiomysql://u:p%40ss%23@h:3306/db_articles"
        cfg = Config()
        cfg.set_main_option("sqlalchemy.url", escape_for_configparser(raw))
        assert cfg.get_main_option("sqlalchemy.url") == raw

    def test_unescaped_url_breaks_alembic_config(self):
        cfg = Config()
        with pytest.raises(ValueError):
            cfg.set_main_option("sqlalchemy.url", "mysql://u:p%40ss@h/db")


class TestUrlPrecedence:
    def test_specific_url_wins_over_database_url(self, monkeypatch):
        monkeypatch.setenv("USERS_DATABASE_URL", "mysql+aiomysql://a:b@specific/x")
        monkeypatch.setenv("DATABASE_URL", MYSQL_URL)
        assert resolve_alembic_url("users") == "mysql+aiomysql://a:b@specific/x"

    @pytest.mark.parametrize(
        "target,db_name",
        [("users", "db_users"), ("analytics", "db_analytics")],
    )
    def test_database_url_fallback_swaps_database_name(
        self, monkeypatch, target, db_name
    ):
        monkeypatch.setenv("DATABASE_URL", MYSQL_URL)
        assert resolve_alembic_url(target) == f"mysql+aiomysql://u:p@db:3306/{db_name}"

    def test_database_url_fallback_is_verbatim_for_articles(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", MYSQL_URL)
        assert resolve_alembic_url("articles") == MYSQL_URL

    def test_db_components_are_last_resort(self, monkeypatch):
        monkeypatch.setenv("DB_USER", "app_user")
        monkeypatch.setenv("DB_HOST", "dbhost")
        assert resolve_alembic_url("analytics") == (
            "mysql+aiomysql://app_user:@dbhost:3306/db_analytics"
        )


class TestEngineKwargs:
    def test_disable_yields_no_connect_args(self):
        assert alembic_engine_kwargs(MYSQL_URL) == {}

    def test_require_passes_ssl_context_for_mysql(self, monkeypatch):
        monkeypatch.setenv("DB_SSL_MODE", "require")
        kwargs = alembic_engine_kwargs(MYSQL_URL)
        assert isinstance(kwargs["connect_args"]["ssl"], ssl.SSLContext)

    def test_sqlite_never_receives_ssl_args(self, monkeypatch):
        monkeypatch.setenv("DB_SSL_MODE", "require")
        assert alembic_engine_kwargs(SQLITE_URL) == {}

    def test_verify_ca_requires_certificate_validation(self, monkeypatch):
        monkeypatch.setenv("DB_SSL_MODE", "verify-ca")
        context = alembic_engine_kwargs(MYSQL_URL)["connect_args"]["ssl"]
        assert context.verify_mode == ssl.CERT_REQUIRED
        assert context.check_hostname is False

    def test_invalid_ssl_mode_fails_fast(self, monkeypatch):
        monkeypatch.setenv("DB_SSL_MODE", "bogus")
        with pytest.raises(DatabaseConfigError, match="DB_SSL_MODE"):
            alembic_engine_kwargs(MYSQL_URL)

    def test_unreadable_ca_fails_fast(self, monkeypatch, tmp_path):
        monkeypatch.setenv("DB_SSL_MODE", "verify-ca")
        monkeypatch.setenv("DB_SSL_CA", str(tmp_path / "missing-ca.pem"))
        with pytest.raises(DatabaseConfigError, match="DB_SSL_CA"):
            alembic_engine_kwargs(MYSQL_URL)

    def test_invalid_ssl_mode_is_ignored_for_sqlite(self, monkeypatch):
        monkeypatch.setenv("DB_SSL_MODE", "bogus")
        assert alembic_engine_kwargs(SQLITE_URL) == {}
