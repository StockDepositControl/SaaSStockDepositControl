from typing import Dict, List, Optional

from backend.adapters.database.connection import get_articles_session_factory
from backend.adapters.database.multi_tenant import get_sucursal_id, get_tenant_id
from backend.adapters.repositories.models.articles import (
    Articulo as ArticuloORM,
)
from backend.adapters.repositories.models.articles import (
    StockPorDeposito as StockPorDepositoORM,
)
from backend.app.movements.domain import StockPorDeposito
from backend.app.movements.ports import StockRepositoryPort
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker


class SQLAlchemyStockRepository(StockRepositoryPort):
    """
    SQLAlchemy implementation of StockRepositoryPort querying db_articles.
    Strictly READ-ONLY regarding db_articles schema and entities.
    """

    def __init__(self, session_factory: Optional[async_sessionmaker] = None):
        self.session_factory = session_factory or get_articles_session_factory()

    async def get_stock_position(
        self, tenant_id: int, id_sucursal: int, id_deposito: int, id_articulo: str
    ) -> Optional[StockPorDeposito]:
        resolved_empresa = tenant_id

        async with self.session_factory() as session:
            stmt = select(StockPorDepositoORM).where(
                StockPorDepositoORM.id_empresa == resolved_empresa,
                StockPorDepositoORM.id_sucursal == id_sucursal,
                StockPorDepositoORM.id_deposito == id_deposito,
                StockPorDepositoORM.id_articulo == id_articulo,
            )
            result = await session.execute(stmt)
            stock_orm = result.scalar_one_or_none()
            if not stock_orm:
                return None

            stock_real_int = (
                int(stock_orm.stock_real) if stock_orm.stock_real is not None else 0
            )

            return StockPorDeposito(
                id_empresa=stock_orm.id_empresa,
                id_sucursal=stock_orm.id_sucursal,
                id_deposito=stock_orm.id_deposito,
                id_articulo=str(stock_orm.id_articulo).strip(),
                stock_real=stock_real_int,
            )

    async def get_stock_positions_batch(
        self, deposit_id: int, article_ids: List[str]
    ) -> Dict[str, int]:
        if not article_ids:
            return {}

        tenant_id = get_tenant_id() or 1
        sucursal_id = get_sucursal_id() or 1

        async with self.session_factory() as session:
            stmt = select(
                StockPorDepositoORM.id_articulo, StockPorDepositoORM.stock_real
            ).where(
                StockPorDepositoORM.id_empresa == tenant_id,
                StockPorDepositoORM.id_sucursal == sucursal_id,
                StockPorDepositoORM.id_deposito == deposit_id,
                StockPorDepositoORM.id_articulo.in_(article_ids),
            )
            result = await session.execute(stmt)
            rows = result.all()
            return {
                str(row[0]).strip(): (int(row[1]) if row[1] is not None else 0)
                for row in rows
            }

    async def count_catalog_articles(self) -> int:
        async with self.session_factory() as session:
            result = await session.execute(
                select(func.count()).select_from(ArticuloORM)
            )
            return int(result.scalar_one() or 0)

    async def count_out_of_stock_articles(
        self, tenant_id: int, branch_id: int, deposit_id: int
    ) -> int:
        async with self.session_factory() as session:
            stmt = (
                select(func.count())
                .select_from(StockPorDepositoORM)
                .where(
                    StockPorDepositoORM.id_empresa == tenant_id,
                    StockPorDepositoORM.id_sucursal == branch_id,
                    StockPorDepositoORM.id_deposito == deposit_id,
                    StockPorDepositoORM.stock_real == 0,
                )
            )
            result = await session.execute(stmt)
            return int(result.scalar_one() or 0)
