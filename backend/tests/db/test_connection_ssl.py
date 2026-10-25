import datetime
import ssl

import pytest
from backend.adapters.database import connection
from backend.adapters.database.connection import (
    DatabaseConfigError,
    build_ssl_connect_args,
    resolve_database_url,
)
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

ENV_VARS = [
    "ARTICLES_DATABASE_URL",
    "USERS_DATABASE_URL",
    "ANALYTICS_DATABASE_URL",
    "DATABASE_URL",
    "DB_USER",
    "DB_PASSWORD",
    "DB_HOST",
    "DB_PORT",
    "DB_NAME_ARTICLES",
    "DB_NAME_USERS",
    "DB_NAME_ANALYTICS",
    "DB_SSL_MODE",
    "DB_SSL_CA",
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for name in ENV_VARS:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def ca_file(tmp_path):
    key = ec.generate_private_key(ec.SECP256R1())
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test-ca")])
    now = datetime.datetime.now(datetime.UTC)
    cert = (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=1))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )
    path = tmp_path / "ca.pem"
    path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    return str(path)


# ─── URL precedence ───


@pytest.mark.parametrize(
    "target,specific_var",
    [
        ("articles", "ARTICLES_DATABASE_URL"),
        ("users", "USERS_DATABASE_URL"),
        ("analytics", "ANALYTICS_DATABASE_URL"),
    ],
)
def test_specific_url_wins_over_base_url_and_components(
    monkeypatch, target, specific_var
):
    monkeypatch.setenv(specific_var, "mysql+aiomysql://s:s@specific:3306/specific_db")
    monkeypatch.setenv("DATABASE_URL", "mysql+aiomysql://b:b@base:3306/base_db")
    monkeypatch.setenv("DB_HOST", "component-host")

    assert (
        resolve_database_url(target) == "mysql+aiomysql://s:s@specific:3306/specific_db"
    )


def test_articles_uses_base_url_verbatim(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "mysql+aiomysql://b:b@base:3306/base_db")

    assert resolve_database_url("articles") == "mysql+aiomysql://b:b@base:3306/base_db"


@pytest.mark.parametrize(
    "target,db_name", [("users", "db_users"), ("analytics", "db_analytics")]
)
def test_base_url_substitutes_database_name(monkeypatch, target, db_name):
    monkeypatch.setenv(
        "DATABASE_URL", "mysql+aiomysql://b:p%40ss@base:3306/db_articles"
    )

    resolved = resolve_database_url(target)

    assert resolved == f"mysql+aiomysql://b:p%40ss@base:3306/{db_name}"


def test_base_url_substitution_honours_configured_names(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "mysql+aiomysql://b:b@base:3306/db_articles")
    monkeypatch.setenv("DB_NAME_USERS", "custom_users")

    assert resolve_database_url("users").endswith("/custom_users")


def test_components_used_when_no_urls(monkeypatch):
    monkeypatch.setenv("DB_USER", "app_user")
    monkeypatch.setenv("DB_PASSWORD", "pw")
    monkeypatch.setenv("DB_HOST", "dbhost")
    monkeypatch.setenv("DB_PORT", "3307")

    assert (
        resolve_database_url("users")
        == "mysql+aiomysql://app_user:pw@dbhost:3307/db_users"
    )


def test_component_defaults(monkeypatch):
    assert (
        resolve_database_url("articles")
        == "mysql+aiomysql://root:@localhost:3306/db_articles"
    )


def test_unknown_target_is_rejected():
    with pytest.raises(DatabaseConfigError):
        resolve_database_url("billing")


# ─── TLS ───


def test_ssl_disabled_by_default():
    assert build_ssl_connect_args() == {}


def test_ssl_disable_explicit(monkeypatch):
    monkeypatch.setenv("DB_SSL_MODE", "disable")

    assert build_ssl_connect_args() == {}


def test_ssl_require_encrypts_without_verification(monkeypatch):
    monkeypatch.setenv("DB_SSL_MODE", "require")

    ctx = build_ssl_connect_args()["ssl"]

    assert isinstance(ctx, ssl.SSLContext)
    assert ctx.verify_mode == ssl.CERT_NONE
    assert ctx.check_hostname is False


def test_ssl_verify_ca_validates_certificate_with_custom_ca(monkeypatch, ca_file):
    monkeypatch.setenv("DB_SSL_MODE", "verify-ca")
    monkeypatch.setenv("DB_SSL_CA", ca_file)

    ctx = build_ssl_connect_args()["ssl"]

    assert ctx.verify_mode == ssl.CERT_REQUIRED
    assert ctx.check_hostname is False
    assert any(c["subject"][0][0][1] == "test-ca" for c in ctx.get_ca_certs())


def test_ssl_verify_ca_without_ca_path_uses_system_trust(monkeypatch):
    monkeypatch.setenv("DB_SSL_MODE", "verify-ca")

    ctx = build_ssl_connect_args()["ssl"]

    assert ctx.verify_mode == ssl.CERT_REQUIRED


def test_ssl_mode_is_case_insensitive(monkeypatch):
    monkeypatch.setenv("DB_SSL_MODE", " REQUIRE ")

    assert "ssl" in build_ssl_connect_args()


def test_ssl_invalid_mode_fails_fast(monkeypatch):
    monkeypatch.setenv("DB_SSL_MODE", "bogus")

    with pytest.raises(DatabaseConfigError, match="DB_SSL_MODE"):
        build_ssl_connect_args()


def test_ssl_verify_ca_with_missing_ca_file_fails_fast(monkeypatch, tmp_path):
    monkeypatch.setenv("DB_SSL_MODE", "verify-ca")
    monkeypatch.setenv("DB_SSL_CA", str(tmp_path / "missing.pem"))

    with pytest.raises(DatabaseConfigError, match="DB_SSL_CA"):
        build_ssl_connect_args()


# ─── Wiring into the engine factories ───


@pytest.fixture
def captured_engines(monkeypatch):
    calls = []

    def fake_create_async_engine(url, **kwargs):
        calls.append((url, kwargs))
        return object()

    monkeypatch.setattr(connection, "create_async_engine", fake_create_async_engine)
    monkeypatch.setattr(connection, "async_sessionmaker", lambda **kw: object())
    for name in ("_articles_engine", "_users_engine", "_analytics_engine"):
        monkeypatch.setattr(connection, name, None)
    monkeypatch.setattr(connection, "_articles_session_factory", None)
    monkeypatch.setattr(connection, "_users_session_factory", None)
    monkeypatch.setattr(connection, "_analytics_session_factory", None)
    return calls


@pytest.mark.parametrize(
    "factory,db_name",
    [
        ("get_articles_session_factory", "db_articles"),
        ("get_users_session_factory", "db_users"),
        ("get_analytics_session_factory", "db_analytics"),
    ],
)
def test_factories_pass_ssl_context_when_enabled(
    monkeypatch, captured_engines, factory, db_name
):
    monkeypatch.setenv("DATABASE_URL", "mysql+aiomysql://u:p@h:3306/db_articles")
    monkeypatch.setenv("DB_SSL_MODE", "require")

    getattr(connection, factory)()

    url, kwargs = captured_engines[0]
    assert url.endswith(f"/{db_name}")
    assert isinstance(kwargs["connect_args"]["ssl"], ssl.SSLContext)


@pytest.mark.parametrize(
    "factory",
    [
        "get_articles_session_factory",
        "get_users_session_factory",
        "get_analytics_session_factory",
    ],
)
def test_factories_omit_connect_args_when_ssl_disabled(captured_engines, factory):
    getattr(connection, factory)()

    _, kwargs = captured_engines[0]
    assert "connect_args" not in kwargs


def test_provider_uses_explicit_url_and_ssl(monkeypatch, captured_engines):
    monkeypatch.setenv("DB_SSL_MODE", "require")

    connection.SQLAlchemyConnectionProvider("mysql+aiomysql://u:p@h:3306/x")

    url, kwargs = captured_engines[0]
    assert url == "mysql+aiomysql://u:p@h:3306/x"
    assert "ssl" in kwargs["connect_args"]


def test_provider_resolves_articles_url_by_precedence(monkeypatch, captured_engines):
    monkeypatch.setenv("DATABASE_URL", "mysql+aiomysql://b:b@base:3306/base_db")

    connection.SQLAlchemyConnectionProvider()

    assert captured_engines[0][0] == "mysql+aiomysql://b:b@base:3306/base_db"
