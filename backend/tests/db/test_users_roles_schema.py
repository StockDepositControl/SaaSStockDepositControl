import pytest
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from backend.adapters.repositories.models import (
    BaseUsers,
    Enterprise,
    Branch,
    User,
    Role,
    UserRoleAssociation,
)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    BaseUsers.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(scope="module")
def users_inspector():
    engine = create_engine("sqlite:///:memory:")
    BaseUsers.metadata.create_all(engine)
    return inspect(engine)


# ---------------------------------------------------------------------------
# 1. Table & Column Definitions
# ---------------------------------------------------------------------------

def test_user_management_tables_exist(users_inspector):
    tables = users_inspector.get_table_names()
    for expected in ["enterprises", "branches", "users", "roles", "user_roles"]:
        assert expected in tables, f"Expected table '{expected}' not found in metadata"


def test_users_table_columns_and_constraints(users_inspector):
    cols = {c["name"]: c for c in users_inspector.get_columns("users")}
    expected_cols = [
        "user_id", "tenant_id", "first_name", "last_name", "email",
        "password_hash", "branch_id", "is_active", "created_at", "updated_at"
    ]
    for col in expected_cols:
        assert col in cols, f"Column '{col}' missing from users table"

    # Soft deactivation column invariants
    assert cols["is_active"]["nullable"] is False

    # Primary key
    pk = users_inspector.get_pk_constraint("users")
    assert pk["constrained_columns"] == ["user_id"]


def test_roles_table_columns(users_inspector):
    cols = {c["name"]: c for c in users_inspector.get_columns("roles")}
    assert "role_id" in cols
    assert "name" in cols
    assert "description" in cols
    assert cols["name"]["nullable"] is False


def test_user_roles_composite_pk(users_inspector):
    pk = users_inspector.get_pk_constraint("user_roles")
    assert set(pk["constrained_columns"]) == {"user_id", "role_id"}


# ---------------------------------------------------------------------------
# 2. Indexes and Multi-Tenant Unique Constraints
# ---------------------------------------------------------------------------

def test_users_table_indexes(users_inspector):
    indexes = users_inspector.get_indexes("users")
    index_names = {idx["name"]: idx for idx in indexes}

    assert "idx_users_tenant_id" in index_names
    assert "tenant_id" in index_names["idx_users_tenant_id"]["column_names"]

    assert "idx_users_tenant_email" in index_names
    assert index_names["idx_users_tenant_email"]["unique"] in [1, True]
    assert index_names["idx_users_tenant_email"]["column_names"] == ["tenant_id", "email"]

    assert "idx_users_branch_id" in index_names


def test_tenant_email_uniqueness_isolation(db_session: Session):
    ent1 = Enterprise(tenant_id=1, description="Tenant 1")
    ent2 = Enterprise(tenant_id=2, description="Tenant 2")
    db_session.add_all([ent1, ent2])
    db_session.commit()

    # Identical email in two different tenants must succeed
    u1 = User(
        tenant_id=1,
        first_name="Alice",
        last_name="One",
        email="operator@pharmacy.com",
        password_hash="hash1",
        is_active=True
    )
    u2 = User(
        tenant_id=2,
        first_name="Bob",
        last_name="Two",
        email="operator@pharmacy.com",
        password_hash="hash2",
        is_active=True
    )
    db_session.add_all([u1, u2])
    db_session.commit()

    assert u1.user_id is not None
    assert u2.user_id is not None

    # Duplicate email within the same tenant must raise IntegrityError
    u3 = User(
        tenant_id=1,
        first_name="Charlie",
        last_name="Duplicate",
        email="operator@pharmacy.com",
        password_hash="hash3",
        is_active=True
    )
    db_session.add(u3)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ---------------------------------------------------------------------------
# 3. Soft-Deactivation & Lifecycle Integrity
# ---------------------------------------------------------------------------

def test_soft_deactivation_lifecycle(db_session: Session):
    ent = Enterprise(tenant_id=1, description="Tenant 1")
    db_session.add(ent)
    db_session.commit()

    user = User(
        tenant_id=1,
        first_name="Active",
        last_name="Staff",
        email="staff@tenant1.com",
        password_hash="secret",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.is_active is True

    # Soft-deactivate user
    user.is_active = False
    db_session.commit()
    db_session.refresh(user)

    assert user.is_active is False

    # Verify user record still exists in persistence
    fetched = db_session.scalar(select(User).where(User.user_id == user.user_id))
    assert fetched is not None
    assert fetched.is_active is False


# ---------------------------------------------------------------------------
# 4. Foreign Key Cascades & Role Associations
# ---------------------------------------------------------------------------

def test_user_role_cascade_on_user_delete(db_session: Session):
    ent = Enterprise(tenant_id=1, description="Tenant 1")
    role_admin = Role(name="administrador", description="Admin role")
    db_session.add_all([ent, role_admin])
    db_session.commit()

    user = User(
        tenant_id=1,
        first_name="Temp",
        last_name="Admin",
        email="temp_admin@tenant1.com",
        password_hash="secret",
        is_active=True
    )
    user.roles.append(role_admin)
    db_session.add(user)
    db_session.commit()

    assoc = db_session.scalar(
        select(UserRoleAssociation).where(
            UserRoleAssociation.user_id == user.user_id,
            UserRoleAssociation.role_id == role_admin.role_id
        )
    )
    assert assoc is not None

    # Deleting user must cascade-delete association without deleting the Role
    db_session.delete(user)
    db_session.commit()

    assoc_after = db_session.scalar(
        select(UserRoleAssociation).where(UserRoleAssociation.user_id == user.user_id)
    )
    assert assoc_after is None

    role_after = db_session.scalar(
        select(Role).where(Role.role_id == role_admin.role_id)
    )
    assert role_after is not None


def test_enterprise_cascade_deletes_users_and_branches(db_session: Session):
    ent = Enterprise(tenant_id=99, description="Tenant to Delete")
    db_session.add(ent)
    db_session.commit()

    branch = Branch(tenant_id=99, description="Branch to Delete")
    user = User(
        tenant_id=99,
        first_name="Cascaded",
        last_name="User",
        email="cascaded@tenant99.com",
        password_hash="secret",
        is_active=True
    )
    db_session.add_all([branch, user])
    db_session.commit()

    assert user.user_id is not None
    assert branch.id_branch is not None

    # Deleting enterprise cascades through ORM relationship
    db_session.delete(ent)
    db_session.commit()

    branches_remaining = db_session.scalars(select(Branch).where(Branch.tenant_id == 99)).all()
    assert len(branches_remaining) == 0
