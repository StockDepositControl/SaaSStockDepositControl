import pytest
from backend.scripts.seed import resolve_seed_urls
from sqlalchemy.engine import make_url

pytestmark = pytest.mark.usefixtures("clean_db_env")

MYSQL_URL = "mysql+aiomysql://app:secret@dbhost:3306/db_articles"


def test_database_url_env_swaps_database_names_for_users_and_analytics(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", MYSQL_URL)

    articles, users, analytics = resolve_seed_urls()

    assert articles == MYSQL_URL
    for url, db_name in ((users, "db_users"), (analytics, "db_analytics")):
        parsed = make_url(url)
        assert (parsed.username, parsed.password, parsed.host) == (
            "app",
            "secret",
            "dbhost",
        )
        assert parsed.database == db_name


def test_specific_env_url_wins_over_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", MYSQL_URL)
    monkeypatch.setenv("USERS_DATABASE_URL", "mysql+aiomysql://u:p@other/users_x")

    _, users, _ = resolve_seed_urls()

    assert users == "mysql+aiomysql://u:p@other/users_x"


def test_components_with_reserved_characters_round_trip(monkeypatch):
    monkeypatch.setenv("DB_USER", "app_user")
    monkeypatch.setenv("DB_PASSWORD", "p@ss/w#rd:1%")
    monkeypatch.setenv("DB_HOST", "dbhost")

    articles, _, analytics = resolve_seed_urls()

    assert make_url(articles).password == "p@ss/w#rd:1%"
    assert make_url(analytics).database == "db_analytics"


def test_explicit_per_database_urls_are_used_verbatim(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", MYSQL_URL)

    urls = resolve_seed_urls(
        url_articles="a://1", url_users="u://2", url_analytics="n://3"
    )

    assert urls == ("a://1", "u://2", "n://3")


def test_non_sqlite_database_url_override_is_shared_by_all_databases():
    assert resolve_seed_urls(database_url=MYSQL_URL) == (MYSQL_URL,) * 3


def test_sqlite_memory_override_gets_one_shared_memory_db_per_logical_database():
    articles, users, analytics = resolve_seed_urls(
        database_url="sqlite+aiosqlite:///:memory:"
    )

    assert "mem_articles" in articles
    assert "mem_users" in users
    assert "mem_analytics" in analytics


def test_sqlite_override_naming_a_test_database_is_shared_as_is():
    url = "sqlite+aiosqlite:///file:test_users?mode=memory&cache=shared&uri=true"

    assert resolve_seed_urls(database_url=url) == (url, url, url)
