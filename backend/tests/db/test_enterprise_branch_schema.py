import pytest
from backend.adapters.repositories.models import BaseUsers, Branch, Enterprise, User
from sqlalchemy import create_engine, inspect


@pytest.fixture(scope="module")
def users_inspector():
    engine = create_engine("sqlite:///:memory:")
    BaseUsers.metadata.create_all(engine)
    return inspect(engine)


def test_enterprises_table_exists(users_inspector):
    tables = users_inspector.get_table_names()
    assert "enterprises" in tables
    cols = {col["name"]: col for col in users_inspector.get_columns("enterprises")}
    assert "tenant_id" in cols
    assert "description" in cols
    assert "id_enterprise" not in cols
    pk_cols = users_inspector.get_pk_constraint("enterprises")["constrained_columns"]
    assert pk_cols == ["tenant_id"]


def test_branches_table_exists(users_inspector):
    tables = users_inspector.get_table_names()
    assert "branches" in tables
    cols = {col["name"]: col for col in users_inspector.get_columns("branches")}
    assert "id_branch" in cols
    assert "tenant_id" in cols
    assert "description" in cols
    assert "enterprise_id" not in cols

    fks = users_inspector.get_foreign_keys("branches")
    referred_tables = [fk["referred_table"] for fk in fks]
    assert "enterprises" in referred_tables


def test_users_table_has_enterprise_and_branch_fks(users_inspector):
    cols = {col["name"]: col for col in users_inspector.get_columns("users")}
    assert "tenant_id" in cols
    assert "branch_id" in cols
    assert "enterprise_id" not in cols

    fks = users_inspector.get_foreign_keys("users")
    referred_tables = [fk["referred_table"] for fk in fks]
    assert "enterprises" in referred_tables
    assert "branches" in referred_tables


def test_enterprise_orm_cascade():
    assert "delete-orphan" in Enterprise.branches.property.cascade


def test_branch_orm_relationships():
    assert Branch.enterprise.property.mapper.class_ == Enterprise
    assert User.enterprise.property.mapper.class_ == Enterprise
    assert User.branch.property.mapper.class_ == Branch
