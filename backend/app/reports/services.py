from collections import defaultdict
from decimal import Decimal
from typing import Dict, List, Tuple

from backend.app.articles.ports import ArticleRepositoryPort
from backend.app.movements.domain import VatClassifier
from backend.app.reports.domain import VatCalculator
from backend.app.reports.ports import (
    DailyInventoryBalanceReportRepositoryPort,
    GoodsReceivedReportRepositoryPort,
    ShrinkageReportRepositoryPort,
)
from backend.app.reports.schemas import (
    DailyInventoryBalanceFilters,
    DailyInventoryBalanceResponse,
    DailyInventoryBalanceSummary,
    GoodsReceivedLineItem,
    GoodsReceivedReportFilters,
    GoodsReceivedReportResponse,
    ShrinkageLineItem,
    ShrinkageReportFilters,
    ShrinkageReportResponse,
)


class ShrinkageReportService:
    """
    Controller service orchestrating shrinkage report generation and financial erosion
    calculations.
    Coordinates between analytics audit logs and articles catalog.
    """

    def __init__(
        self,
        report_repository: ShrinkageReportRepositoryPort,
        article_repository: ArticleRepositoryPort,
    ):
        self.report_repository = report_repository
        self.article_repository = article_repository

    async def get_shrinkage_report(
        self, tenant_id: str, filters: ShrinkageReportFilters
    ) -> ShrinkageReportResponse:
        """
        Generates the aggregated shrinkage report for the specified tenant, date range,
        and filters.
        """
        try:
            numeric_tenant_id = int(tenant_id)
        except (ValueError, TypeError):
            numeric_tenant_id = 1

        raw_records = await self.report_repository.fetch_shrinkage_records(
            tenant_id=numeric_tenant_id,
            start_date=filters.start_date,
            end_date=filters.end_date,
            branch_id=filters.branch_id,
        )

        # Aggregate shrinkage quantities by article code
        quantities_by_article: Dict[str, int] = defaultdict(int)
        for record in raw_records:
            quantities_by_article[record.article_code] += record.affected_amount

        line_items: List[ShrinkageLineItem] = []
        total_financial_erosion = Decimal("0.00")
        total_shrinkage_units = 0

        for article_code, total_qty in quantities_by_article.items():
            article = await self.article_repository.get_by_id(article_code)

            if article:
                des_articulo = article.des_articulo
                des_familia = article.des_familia or ""
                pcio_com_siva = article.pcio_com_siva
            else:
                des_articulo = "Artículo desconocido"
                des_familia = ""
                pcio_com_siva = Decimal("0.00")

            vat_rate = VatClassifier.classify(
                des_familia=des_familia,
                default_vat_rate=filters.default_vat_rate,
            )
            total_unit_cost = VatCalculator.calculate_total_unit_cost(
                pcio_com_siva=pcio_com_siva,
                vat_rate=vat_rate,
            )
            total_loss = VatCalculator.calculate_financial_loss(
                quantity=total_qty,
                total_unit_cost=total_unit_cost,
            )

            line_items.append(
                ShrinkageLineItem(
                    article_code=article_code,
                    des_articulo=des_articulo,
                    des_familia=des_familia,
                    pcio_com_siva=pcio_com_siva,
                    vat_rate=vat_rate,
                    total_unit_cost=total_unit_cost,
                    total_quantity=total_qty,
                    total_financial_loss=total_loss,
                )
            )

            total_shrinkage_units += total_qty
            total_financial_erosion += total_loss

        return ShrinkageReportResponse(
            tenant_id=tenant_id,
            start_date=filters.start_date,
            end_date=filters.end_date,
            default_vat_rate=filters.default_vat_rate,
            total_items=len(line_items),
            total_shrinkage_units=total_shrinkage_units,
            total_financial_erosion=total_financial_erosion,
            line_items=line_items,
        )


class GoodsReceivedReportService:
    """
    Controller service orchestrating goods received report generation and injected
    capital valorization.
    Coordinates between analytics audit logs and articles catalog.
    """

    def __init__(
        self,
        report_repository: GoodsReceivedReportRepositoryPort,
        article_repository: ArticleRepositoryPort,
    ):
        self.report_repository = report_repository
        self.article_repository = article_repository

    async def get_goods_received_report(
        self, tenant_id: str, filters: GoodsReceivedReportFilters
    ) -> GoodsReceivedReportResponse:
        """
        Generates the aggregated goods received report for the specified tenant, date
        range, and filters.
        """
        try:
            numeric_tenant_id = int(tenant_id)
        except (ValueError, TypeError):
            numeric_tenant_id = 1

        raw_records = await self.report_repository.fetch_goods_received_records(
            tenant_id=numeric_tenant_id,
            start_date=filters.start_date,
            end_date=filters.end_date,
            branch_id=filters.branch_id,
        )

        # Aggregate addition quantities by (article_code, reason)
        quantities_by_key: Dict[Tuple[str, str], int] = defaultdict(int)
        for record in raw_records:
            reason = (
                record.observation.strip()
                if record.observation and record.observation.strip()
                else "Ingreso / Alta"
            )
            quantities_by_key[(record.article_code, reason)] += record.affected_amount

        line_items: List[GoodsReceivedLineItem] = []
        total_capital_inyectado = Decimal("0.00")
        total_added_units = 0

        for (article_code, reason), total_qty in quantities_by_key.items():
            article = await self.article_repository.get_by_id(article_code)
            barcode = (
                await self.article_repository.get_barcode_by_article_id(article_code)
                or ""
            )

            if article:
                des_articulo = article.des_articulo
                des_familia = article.des_familia or ""
                pcio_com_siva = article.pcio_com_siva
            else:
                des_articulo = "Artículo desconocido"
                des_familia = ""
                pcio_com_siva = Decimal("0.00")

            vat_rate = VatClassifier.classify(
                des_familia=des_familia,
                default_vat_rate=filters.default_vat_rate,
            )
            total_unit_cost = VatCalculator.calculate_total_unit_cost(
                pcio_com_siva=pcio_com_siva,
                vat_rate=vat_rate,
            )
            capital_inyectado = VatCalculator.calculate_financial_loss(
                quantity=total_qty,
                total_unit_cost=total_unit_cost,
            )

            line_items.append(
                GoodsReceivedLineItem(
                    barcode=barcode,
                    article_code=article_code,
                    des_articulo=des_articulo,
                    des_familia=des_familia,
                    reason=reason,
                    quantity_added=total_qty,
                    pcio_com_siva=pcio_com_siva,
                    vat_rate=vat_rate,
                    total_unit_cost=total_unit_cost,
                    capital_inyectado=capital_inyectado,
                )
            )

            total_added_units += total_qty
            total_capital_inyectado += capital_inyectado

        return GoodsReceivedReportResponse(
            tenant_id=tenant_id,
            start_date=filters.start_date,
            end_date=filters.end_date,
            default_vat_rate=filters.default_vat_rate,
            total_items=len(line_items),
            total_added_units=total_added_units,
            total_capital_inyectado=total_capital_inyectado,
            line_items=line_items,
        )


class DailyInventoryBalanceReportService:
    """
    Controller service orchestrating daily inventory balance reporting.
    Calculates consolidated daily balance (Goods Received vs Shrinkage) and net
    patrimonial variation.
    """

    def __init__(
        self,
        report_repository: DailyInventoryBalanceReportRepositoryPort,
    ):
        self.report_repository = report_repository

    async def get_daily_inventory_balance_report(
        self, tenant_id: str, filters: DailyInventoryBalanceFilters
    ) -> DailyInventoryBalanceResponse:
        """
        Generates consolidated daily inventory balance report for tenant, date range,
        and optional branch.
        """
        try:
            numeric_tenant_id = int(tenant_id)
        except (ValueError, TypeError):
            numeric_tenant_id = 1

        records = await self.report_repository.fetch_daily_balance_records(
            tenant_id=numeric_tenant_id,
            start_date=filters.start_date,
            end_date=filters.end_date,
            branch_id=filters.branch_id,
        )

        daily_summaries: List[DailyInventoryBalanceSummary] = []
        total_addition_value = Decimal("0.00")
        total_shrinkage_value = Decimal("0.00")
        net_patrimonial_variation = Decimal("0.00")

        for record in records:
            net_variation = record.total_addition_value - record.total_shrinkage_value
            summary = DailyInventoryBalanceSummary(
                report_date=record.report_date,
                total_audit_articles=record.total_audit_articles,
                total_processed_units=record.total_processed_units,
                total_addition_units=record.total_addition_amount,
                total_shrinkage_units=record.total_shrinkage_amount,
                total_addition_value=record.total_addition_value,
                total_shrinkage_value=record.total_shrinkage_value,
                net_patrimonial_variation=net_variation,
            )
            daily_summaries.append(summary)

            total_addition_value += record.total_addition_value
            total_shrinkage_value += record.total_shrinkage_value
            net_patrimonial_variation += net_variation

        return DailyInventoryBalanceResponse(
            tenant_id=tenant_id,
            branch_id=filters.branch_id,
            start_date=filters.start_date,
            end_date=filters.end_date,
            total_days=len(daily_summaries),
            total_addition_value=total_addition_value,
            total_shrinkage_value=total_shrinkage_value,
            net_patrimonial_variation=net_patrimonial_variation,
            daily_summaries=daily_summaries,
        )
