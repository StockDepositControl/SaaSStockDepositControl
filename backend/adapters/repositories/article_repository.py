from decimal import Decimal
from typing import List, Optional, Tuple, Set
from sqlalchemy import select, or_, and_, func
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
from backend.adapters.repositories.models.analytics import AuditRecord as AuditRecordORM
from backend.adapters.database.connection import get_articles_session_factory, get_analytics_session_factory
from backend.adapters.database.multi_tenant import get_tenant_id

class SQLAlchemyArticleRepository(ArticleRepositoryPort):
    """
    SQLAlchemy 2.0 implementation of ArticleRepositoryPort.
    Queries the articles database tables (`articulos`, `codigos_barra_articulo`, etc.) in db_articles.
    """
    def __init__(
        self,
        session_factory: Optional[async_sessionmaker] = None,
        analytics_session_factory: Optional[async_sessionmaker] = None,
    ):
        self.session_factory = session_factory or get_articles_session_factory()
        self.analytics_session_factory = analytics_session_factory or get_analytics_session_factory()
    # Filter search results based on whether the article has been audited in the current session.
    async def _get_audited_article_codes(self, active_session_id: Optional[int]) -> Set[str]:
        if not active_session_id:
            return set()
        try:
            async with self.analytics_session_factory() as session:
                stmt = select(AuditRecordORM.article_code).where(AuditRecordORM.session_id == active_session_id)
                result = await session.execute(stmt)
                return {str(code).strip() for code in result.scalars().all() if code}
        except Exception:
            return set()

    def _to_domain(self, art_orm: ArticuloORM, fue_auditado: bool = False) -> Articulo:
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
            fue_auditado=fue_auditado,
        )

    async def get_by_id(self, id_articulo: str, active_session_id: Optional[int] = None) -> Optional[Articulo]:
        audited_codes = await self._get_audited_article_codes(active_session_id)
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
            is_audited = str(art_orm.id_articulo).strip() in audited_codes
            return self._to_domain(art_orm, fue_auditado=is_audited)

    async def get_by_barcode(self, barcode: str, active_session_id: Optional[int] = None) -> Optional[Articulo]:
        audited_codes = await self._get_audited_article_codes(active_session_id)
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
            is_audited = str(art_orm.id_articulo).strip() in audited_codes
            return self._to_domain(art_orm, fue_auditado=is_audited)

    async def search(self, query: str, active_session_id: Optional[int] = None) -> List[Articulo]:
        clean_query = query.strip()
        if not clean_query:
            return []

        audited_codes = await self._get_audited_article_codes(active_session_id)

        async with self.session_factory() as session:
            # 1. Try exact match by Article ID
            art_by_id = await self.get_by_id(clean_query, active_session_id=active_session_id)
            if art_by_id:
                return [art_by_id]

            # 2. Try exact match by barcode string
            art_by_bc = await self.get_by_barcode(clean_query, active_session_id=active_session_id)
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

            return [
                self._to_domain(art, fue_auditado=str(art.id_articulo).strip() in audited_codes)
                for art in art_orms
            ]

    async def list_articles(
        self,
        page: int = 1,
        limit: int = 50,
        search: Optional[str] = None,
        id_familia: Optional[str] = None,
        id_grupo: Optional[str] = None,
        fue_auditado: Optional[bool] = None,
        active_session_id: Optional[int] = None
    ) -> Tuple[List[Articulo], int]:
        audited_codes = await self._get_audited_article_codes(active_session_id)

        conditions = []
        if id_familia:
            conditions.append(ArticuloORM.id_familia == id_familia)
        if id_grupo:
            conditions.append(ArticuloORM.id_grupo == id_grupo)
        if search and search.strip():
            clean_search = search.strip()
            tokens = clean_search.split()
            token_conditions = [ArticuloORM.des_articulo.ilike(f"%{t}%") for t in tokens]
            conditions.append(
                or_(
                    ArticuloORM.id_articulo == clean_search,
                    and_(*token_conditions)
                )
            )
        if fue_auditado is True:
            if not audited_codes:
                return [], 0
            conditions.append(ArticuloORM.id_articulo.in_(audited_codes))
        elif fue_auditado is False and active_session_id:
            if audited_codes:
                conditions.append(ArticuloORM.id_articulo.not_in(audited_codes))

        where_clause = and_(*conditions) if conditions else True

        async with self.session_factory() as session:
            count_stmt = select(func.count(ArticuloORM.id_articulo)).where(where_clause)
            count_res = await session.execute(count_stmt)
            total = count_res.scalar() or 0

            stmt = (
                select(ArticuloORM)
                .options(
                    joinedload(ArticuloORM.marca),
                    joinedload(ArticuloORM.grupo).joinedload(GrupoORM.familia),
                )
                .where(where_clause)
                .order_by(ArticuloORM.id_articulo)
            )

            if page is not None and limit is not None:
                offset = max(0, (page - 1) * limit)
                stmt = stmt.offset(offset).limit(limit)

            result = await session.execute(stmt)
            art_orms = result.scalars().unique().all()

            items = [
                self._to_domain(art, fue_auditado=str(art.id_articulo).strip() in audited_codes)
                for art in art_orms
            ]
            return items, total
