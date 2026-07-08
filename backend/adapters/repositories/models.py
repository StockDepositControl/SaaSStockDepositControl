import enum
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    String,
    Integer,
    BigInteger,
    DECIMAL as SQLDecimal,
    Boolean,
    DateTime,
    Date,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    and_
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class UserRole(str, enum.Enum):
    ADMINISTRADOR = "administrador"
    SUPERVISOR = "supervisor"
    AUDITOR = "auditor"

class TipoAccion(str, enum.Enum):
    ALTA = "Alta"
    BAJA = "Baja"
    SIN_ACCION = "Sin Acción"

class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False)
    nombre_completo: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    id_sucursal: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        Index("ix_usuarios_tenant", "tenant_id"),
        Index("ix_usuarios_tenant_email", "tenant_id", "email"),
    )

class Familia(Base):
    __tablename__ = "familias"

    id_familia: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    des_familia: Mapped[str] = mapped_column(String(255), nullable=False)

    grupos: Mapped[List["Grupo"]] = relationship(back_populates="familia", cascade="all, delete-orphan")
    articulos: Mapped[List["Articulo"]] = relationship(back_populates="familia")

class Grupo(Base):
    __tablename__ = "grupos"

    id_familia: Mapped[int] = mapped_column(ForeignKey("familias.id_familia", ondelete="CASCADE"), primary_key=True)
    id_grupo: Mapped[int] = mapped_column(Integer, primary_key=True)
    des_grupo: Mapped[str] = mapped_column(String(255), nullable=False)

    familia: Mapped["Familia"] = relationship(back_populates="grupos")

class Marca(Base):
    __tablename__ = "marcas"

    id_marca: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    des_marca: Mapped[str] = mapped_column(String(255), nullable=False)

    articulos: Mapped[List["Articulo"]] = relationship(back_populates="marca")

class Articulo(Base):
    __tablename__ = "articulos"

    tenant_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    id_articulo: Mapped[str] = mapped_column(String(50), primary_key=True)
    presentacion: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    des_articulo: Mapped[str] = mapped_column(String(255), nullable=False)
    id_marca: Mapped[Optional[int]] = mapped_column(ForeignKey("marcas.id_marca", ondelete="SET NULL"), nullable=True)
    id_familia: Mapped[Optional[int]] = mapped_column(ForeignKey("familias.id_familia", ondelete="SET NULL"), nullable=True)
    id_grupo: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    pcio_com_siva: Mapped[Decimal] = mapped_column(SQLDecimal(15, 4), nullable=False)

    marca: Mapped[Optional["Marca"]] = relationship(back_populates="articulos")
    familia: Mapped[Optional["Familia"]] = relationship(back_populates="articulos")
    
    grupo: Mapped[Optional["Grupo"]] = relationship(
        primaryjoin="and_(Articulo.id_familia == Grupo.id_familia, Articulo.id_grupo == Grupo.id_grupo)",
        foreign_keys="[Articulo.id_familia, Articulo.id_grupo]"
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["id_familia", "id_grupo"],
            ["grupos.id_familia", "grupos.id_grupo"],
            ondelete="SET NULL"
        ),
        Index("ix_articulos_tenant_articulo", "tenant_id", "id_articulo"),
        Index("ix_articulos_id_marca", "id_marca"),
        Index("ix_articulos_id_familia_id_grupo", "id_familia", "id_grupo"),
    )

class StockPorDeposito(Base):
    __tablename__ = "stock_por_deposito"

    tenant_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    id_sucursal: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_deposito: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_articulo: Mapped[str] = mapped_column(String(50), primary_key=True)
    stock_real: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    fue_auditado: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fecha_hora_auditacion: Mapped[Optional[datetime]] = mapped_column("fecha_hora_auditación", DateTime, nullable=True)

    articulo: Mapped["Articulo"] = relationship()

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "id_articulo"],
            ["articulos.tenant_id", "articulos.id_articulo"],
            ondelete="CASCADE"
        ),
        Index("ix_stock_por_deposito_tenant_deposito", "tenant_id", "id_sucursal", "id_deposito"),
    )

class LotePorDeposito(Base):
    __tablename__ = "lotes_por_deposito"

    tenant_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    id_deposito: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_articulo: Mapped[str] = mapped_column(String(50), primary_key=True)
    lote: Mapped[str] = mapped_column(String(50), primary_key=True)
    vencimiento: Mapped[date] = mapped_column(Date, nullable=False)
    stock_real: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    articulo: Mapped["Articulo"] = relationship()

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "id_articulo"],
            ["articulos.tenant_id", "articulos.id_articulo"],
            ondelete="CASCADE"
        ),
        Index("ix_lotes_por_deposito_tenant_deposito", "tenant_id", "id_deposito"),
        Index("ix_lotes_por_deposito_vencimiento", "vencimiento"),
    )

class AuditoriaRegistro(Base):
    __tablename__ = "auditorias_registro"

    id_auditoria: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String(50), nullable=False)
    id_sucursal: Mapped[int] = mapped_column(Integer, nullable=False)
    id_deposito: Mapped[int] = mapped_column(Integer, nullable=False)
    id_articulo: Mapped[str] = mapped_column(String(50), nullable=False)
    tipo_accion: Mapped[TipoAccion] = mapped_column(Enum(TipoAccion), nullable=False)
    cantidad_afectada: Mapped[int] = mapped_column(Integer, nullable=False)
    monto_valorizado: Mapped[Decimal] = mapped_column(SQLDecimal(15, 4), nullable=False)
    id_usuario: Mapped[int] = mapped_column(ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False)
    fecha_hora: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    articulo: Mapped["Articulo"] = relationship()
    usuario: Mapped["Usuario"] = relationship()

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "id_articulo"],
            ["articulos.tenant_id", "articulos.id_articulo"],
            ondelete="CASCADE"
        ),
        Index("ix_auditorias_registro_tenant_sucursal", "tenant_id", "id_sucursal"),
        Index("ix_auditorias_registro_id_usuario", "id_usuario"),
    )
