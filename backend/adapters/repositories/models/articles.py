from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    String,
    CHAR,
    Integer,
    SmallInteger,
    Float,
    Numeric,
    ForeignKeyConstraint,
    Index,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class BaseArticles(DeclarativeBase):
    pass


class Familia(BaseArticles):
    __tablename__ = "familias"

    id_familia: Mapped[str] = mapped_column(String(2), primary_key=True)
    des_familia: Mapped[str] = mapped_column(String(40), nullable=False)

    grupos: Mapped[List["Grupo"]] = relationship(back_populates="familia", cascade="all, delete-orphan")


class Grupo(BaseArticles):
    __tablename__ = "grupos"

    id_familia: Mapped[str] = mapped_column(String(2), primary_key=True)
    id_grupo: Mapped[str] = mapped_column(String(2), primary_key=True)
    des_grupo: Mapped[str] = mapped_column(String(40), nullable=False)

    familia: Mapped["Familia"] = relationship(back_populates="grupos")
    articulos: Mapped[List["Articulo"]] = relationship(back_populates="grupo")

    __table_args__ = (
        ForeignKeyConstraint(
            ["id_familia"],
            ["familias.id_familia"],
            onupdate="CASCADE",
            ondelete="RESTRICT"
        ),
    )


class Marca(BaseArticles):
    __tablename__ = "marcas"

    id_marca: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    des_marca: Mapped[str] = mapped_column(String(80), nullable=False)

    articulos: Mapped[List["Articulo"]] = relationship(back_populates="marca")


class Articulo(BaseArticles):
    __tablename__ = "articulos"

    id_articulo: Mapped[str] = mapped_column(CHAR(25), primary_key=True)
    presentacion: Mapped[Optional[str]] = mapped_column(CHAR(255), nullable=True)
    des_articulo: Mapped[str] = mapped_column(CHAR(255), nullable=False)
    id_marca: Mapped[int] = mapped_column(Integer, nullable=False)
    id_familia: Mapped[str] = mapped_column(String(2), nullable=False)
    id_grupo: Mapped[str] = mapped_column(String(2), nullable=False)
    pcio_com_siva: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False)

    marca: Mapped["Marca"] = relationship(back_populates="articulos")
    grupo: Mapped["Grupo"] = relationship(back_populates="articulos")

    __table_args__ = (
        ForeignKeyConstraint(
            ["id_marca"],
            ["marcas.id_marca"],
            onupdate="CASCADE",
            ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["id_familia", "id_grupo"],
            ["grupos.id_familia", "grupos.id_grupo"],
            onupdate="CASCADE",
            ondelete="RESTRICT"
        ),
        Index("ix_articulos_id_marca", "id_marca"),
        Index("ix_articulos_id_familia_id_grupo", "id_familia", "id_grupo"),
        Index("ft_articulos_des_articulo", "des_articulo", mysql_prefix="FULLTEXT"),
    )



class StockPorDeposito(BaseArticles):
    __tablename__ = "stock_por_deposito"

    id_empresa: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_sucursal: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_deposito: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    id_articulo: Mapped[str] = mapped_column(CHAR(25), primary_key=True)
    stock_real: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    articulo: Mapped["Articulo"] = relationship()
    empresa: Mapped["Empresa"] = relationship()
    sucursal: Mapped["Sucursal"] = relationship()
    deposito: Mapped["Deposito"] = relationship(overlaps="sucursal")

    __table_args__ = (
        ForeignKeyConstraint(
            ["id_articulo"],
            ["articulos.id_articulo"],
            onupdate="CASCADE",
            ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["id_empresa"],
            ["empresas.id_empresa"],
            onupdate="CASCADE",
            ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["id_sucursal"],
            ["sucursales.id_sucursal"],
            onupdate="CASCADE",
            ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["id_sucursal", "id_deposito"],
            ["depositos.id_sucursal", "depositos.id_deposito"],
            onupdate="CASCADE",
            ondelete="RESTRICT"
        ),
        Index("ix_stock_deposito_empresa_sucursal", "id_empresa", "id_sucursal"),
        Index("ix_stock_deposito_id_articulo", "id_articulo"),
    )


class LotePorDeposito(BaseArticles):
    __tablename__ = "lotes_por_deposito"

    id_empresa: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_sucursal: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_deposito: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    id_articulo: Mapped[str] = mapped_column(CHAR(25), primary_key=True)
    lote: Mapped[str] = mapped_column(String(10), primary_key=True)
    vencimiento: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    stock_real: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    articulo: Mapped["Articulo"] = relationship()
    empresa: Mapped["Empresa"] = relationship()
    sucursal: Mapped["Sucursal"] = relationship()
    deposito: Mapped["Deposito"] = relationship(overlaps="sucursal")

    __table_args__ = (
        ForeignKeyConstraint(
            ["id_articulo"],
            ["articulos.id_articulo"],
            onupdate="CASCADE",
            ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["id_empresa"],
            ["empresas.id_empresa"],
            onupdate="CASCADE",
            ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["id_sucursal"],
            ["sucursales.id_sucursal"],
            onupdate="CASCADE",
            ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["id_sucursal", "id_deposito"],
            ["depositos.id_sucursal", "depositos.id_deposito"],
            onupdate="CASCADE",
            ondelete="RESTRICT"
        ),
        Index("ix_lotes_deposito_empresa_sucursal", "id_empresa", "id_sucursal"),
        Index("ix_lotes_deposito_id_articulo", "id_articulo"),
        Index("ix_lotes_deposito_vencimiento", "vencimiento"),
    )


class CodigoBarraArticulo(BaseArticles):
    __tablename__ = "codigos_barra_articulo"

    id_articulo: Mapped[str] = mapped_column(CHAR(25), primary_key=True)
    cod_barra: Mapped[str] = mapped_column(String(30), primary_key=True)

    articulo: Mapped["Articulo"] = relationship()

    __table_args__ = (
        ForeignKeyConstraint(
            ["id_articulo"],
            ["articulos.id_articulo"],
            onupdate="CASCADE",
            ondelete="RESTRICT"
        ),
        Index("ix_codigos_barra_cod_barra", "cod_barra"),
        Index("ix_codigos_barra_id_articulo", "id_articulo"),
    )


class Empresa(BaseArticles):
    __tablename__ = "empresas"

    id_empresa: Mapped[int] = mapped_column(Integer, primary_key=True)
    des_empresa: Mapped[str] = mapped_column(String(40), nullable=False)

    sucursales: Mapped[List["Sucursal"]] = relationship(back_populates="empresa", cascade="all, delete-orphan")
    depositos: Mapped[List["Deposito"]] = relationship(back_populates="empresa", cascade="all, delete-orphan")


class Sucursal(BaseArticles):
    __tablename__ = "sucursales"

    id_sucursal: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_empresa: Mapped[int] = mapped_column(Integer, nullable=False)
    des_sucursal: Mapped[str] = mapped_column(String(40), nullable=False)

    empresa: Mapped["Empresa"] = relationship(back_populates="sucursales")
    depositos: Mapped[List["Deposito"]] = relationship(back_populates="sucursal", cascade="all, delete-orphan")

    __table_args__ = (
        ForeignKeyConstraint(
            ["id_empresa"],
            ["empresas.id_empresa"],
            onupdate="CASCADE",
            ondelete="RESTRICT"
        ),
        Index("ix_sucursales_id_empresa", "id_empresa"),
    )


class Deposito(BaseArticles):
    __tablename__ = "depositos"

    id_sucursal: Mapped[int] = mapped_column(Integer, primary_key=True)
    id_deposito: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    id_empresa: Mapped[int] = mapped_column(Integer, nullable=False)
    des_deposito: Mapped[str] = mapped_column(String(30), nullable=False)

    sucursal: Mapped["Sucursal"] = relationship(back_populates="depositos")
    empresa: Mapped["Empresa"] = relationship(back_populates="depositos")

    __table_args__ = (
        ForeignKeyConstraint(
            ["id_sucursal"],
            ["sucursales.id_sucursal"],
            onupdate="CASCADE",
            ondelete="RESTRICT"
        ),
        ForeignKeyConstraint(
            ["id_empresa"],
            ["empresas.id_empresa"],
            onupdate="CASCADE",
            ondelete="RESTRICT"
        ),
        Index("ix_depositos_id_empresa", "id_empresa"),
    )

