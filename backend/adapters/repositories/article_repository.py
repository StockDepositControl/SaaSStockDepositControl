from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import async_sessionmaker

from backend.app.articles.models import Articulo
from backend.app.articles.ports import ArticleRepositoryPort
from backend.adapters.repositories.models.articles import (
    Articulo as ArticuloORM,
    CodigoBarraArticulo as CodigoBarraArticuloORM,
    Marca as MarcaORM,
    Grupo as GrupoORM,
    Familia as FamiliaORM,
)
from backend.adapters.database.connection import get_articles_session_factory
from backend.adapters.database.multi_tenant import get_tenant_id

class SQLAlchemyArticleRepository(ArticleRepositoryPort):
    """
    SQLAlchemy 2.0 implementation of ArticleRepositoryPort.
    Queries the articles database tables (`articulos`, `codigos_barra_articulo`, etc.) in db_articles.
    """
    def __init__(self, session_factory: Optional[async_sessionmaker] = None):
        self.session_factory = session_factory or get_articles_session_factory()

    def _to_domain(self, art_orm: ArticuloORM) -> Articulo:
        # Extract eager-loaded descriptions safely
        des_marca = art_orm.marca.des_marca if art_orm.marca else None
        des_grupo = art_orm.grupo.des_grupo if art_orm.grupo else None
        des_familia = art_orm.grupo.familia.des_familia if (art_orm.grupo and art_orm.grupo.familia) else None

        # Convert float pcio_com_siva to Decimal cleanly
        cost_decimal = Decimal(str(art_orm.pcio_com_siva)) if art_orm.pcio_com_siva is not None else Decimal("0.00")

        return Articulo(
            id_articulo=str(art_orm.id_articulo).strip(),
            presentacion=art_orm.presentacion.strip() if art_orm.presentacion else None,
            des_articulo=art_orm.des_articulo.strip() if art_orm.des_articulo else "",
            id_marca=art_orm.id_marca,
            des_marca=des_marca.strip() if des_marca else None,
            id_familia=str(art_orm.id_familia) if art_orm.id_familia else None,
            des_familia=des_familia.strip() if des_familia else None,
            id_grupo=str(art_orm.id_grupo) if art_orm.id_grupo else None,
            des_grupo=des_grupo.strip() if des_grupo else None,
            pcio_com_siva=cost_decimal,
        )

    async def get_by_id(self, id_articulo: str) -> Optional[Articulo]:
        async with self.session_factory() as session:
            stmt = (
                select(ArticuloORM)
                .options(
                    joinedload(ArticuloORM.marca),
                    joinedload(ArticuloORM.grupo).joinedload(GrupoORM.familia),
                )
                .where(ArticuloORM.id_articulo == id_articulo)
            )
            result = await session.execute(stmt)
            art_orm = result.scalar_one_or_none()
            if not art_orm:
                return None
            return self._to_domain(art_orm)

    async def get_by_barcode(self, barcode: str) -> Optional[Articulo]:
        async with self.session_factory() as session:
            stmt = (
                select(ArticuloORM)
                .options(
                    joinedload(ArticuloORM.marca),
                    joinedload(ArticuloORM.grupo).joinedload(GrupoORM.familia),
                )
                .join(
                    CodigoBarraArticuloORM,
                    CodigoBarraArticuloORM.id_articulo == ArticuloORM.id_articulo,
                )
                .where(CodigoBarraArticuloORM.cod_barra == barcode)
            )
            result = await session.execute(stmt)
            art_orm = result.scalar_one_or_none()
            if not art_orm:
                return None
            return self._to_domain(art_orm)

    async def search(self, query: str) -> List[Articulo]:
        clean_query = query.strip()
        if not clean_query:
            return []

        async with self.session_factory() as session:
            # 1. Try exact match by Article ID
            art_by_id = await self.get_by_id(clean_query)
            if art_by_id:
                return [art_by_id]

            # 2. Try exact match by barcode string
            art_by_bc = await self.get_by_barcode(clean_query)
            if art_by_bc:
                return [art_by_bc]

            # 3. Tokenized description search (partial match on name)
            tokens = clean_query.split()
            token_conditions = [ArticuloORM.des_articulo.ilike(f"%{token}%") for token in tokens]

            stmt = (
                select(ArticuloORM)
                .options(
                    joinedload(ArticuloORM.marca),
                    joinedload(ArticuloORM.grupo).joinedload(GrupoORM.familia),
                )
                .where(and_(*token_conditions))
                .limit(100)
            )
            result = await session.execute(stmt)
            art_orms = result.scalars().unique().all()

            return [self._to_domain(art) for art in art_orms]
