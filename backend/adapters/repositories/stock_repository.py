from decimal import Decimal
from typing import Optional, Tuple
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.app.movements.models import StockPorDeposito
from backend.app.movements.ports import StockRepositoryPort
from backend.adapters.repositories.models.articles import (
    StockPorDeposito as StockPorDepositoORM,
    Articulo as ArticuloORM,
    Grupo as GrupoORM,
)
from backend.adapters.database.connection import get_articles_session_factory
from backend.app.exceptions import EntityNotFoundException

class SQLAlchemyStockRepository(StockRepositoryPort):
    """
    SQLAlchemy implementation of StockRepositoryPort querying db_articles.
    Strictly READ-ONLY regarding db_articles schema and entities.
    """
    def __init__(self, session_factory: Optional[async_sessionmaker] = None):
        self.session_factory = session_factory or get_articles_session_factory()

    async def get_stock_position(
        self, tenant_id: str, id_sucursal: int, id_deposito: int, id_articulo: str, id_empresa: Optional[int] = None
    ) -> Optional[StockPorDeposito]:
        try:
            resolved_empresa = id_empresa if id_empresa is not None else int(tenant_id)
        except (ValueError, TypeError):
            resolved_empresa = 1

        async with self.session_factory() as session:
            stmt = (
                select(StockPorDepositoORM)
                .where(
                    StockPorDepositoORM.id_empresa == resolved_empresa,
                    StockPorDepositoORM.id_sucursal == id_sucursal,
                    StockPorDepositoORM.id_deposito == id_deposito,
                    StockPorDepositoORM.id_articulo == id_articulo,
                )
            )
            result = await session.execute(stmt)
            stock_orm = result.scalar_one_or_none()
            if not stock_orm:
                return None

            stock_real_int = int(stock_orm.stock_real) if stock_orm.stock_real is not None else 0

            return StockPorDeposito(
                id_empresa=stock_orm.id_empresa,
                id_sucursal=stock_orm.id_sucursal,
                id_deposito=stock_orm.id_deposito,
                id_articulo=str(stock_orm.id_articulo).strip(),
                stock_real=stock_real_int,
            )


    async def get_article_cost_info(
        self, tenant_id: str, id_articulo: str
    ) -> Tuple[Decimal, str]:
        async with self.session_factory() as session:
            stmt = (
                select(ArticuloORM)
                .options(
                    joinedload(ArticuloORM.grupo).joinedload(GrupoORM.familia)
                )
                .where(ArticuloORM.id_articulo == id_articulo)
            )
            result = await session.execute(stmt)
            art_orm = result.scalar_one_or_none()
            if not art_orm:
                raise EntityNotFoundException(f"Article '{id_articulo}' not found.")

            des_familia = (
                art_orm.grupo.familia.des_familia.strip()
                if (art_orm.grupo and art_orm.grupo.familia and art_orm.grupo.familia.des_familia)
                else ""
            )
            pcio_com_siva = (
                Decimal(str(art_orm.pcio_com_siva))
                if art_orm.pcio_com_siva is not None
                else Decimal("0.0000")
            )

            return pcio_com_siva, des_familia
